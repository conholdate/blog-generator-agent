import os
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
LOGOS_DIR = os.path.join(BASE_DIR, "logos")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")


def load_font(preferred_paths: List[str], font_size: int) -> ImageFont.FreeTypeFont:
    for path in preferred_paths:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    return ImageFont.load_default()


def _set_font_variation_by_name_if_possible(
    font: ImageFont.FreeTypeFont, name_candidates: List[str]
) -> bool:
    try:
        if hasattr(font, "get_variation_names") and hasattr(font, "set_variation_by_name"):
            names = font.get_variation_names() or []
            lowered = {n.lower(): n for n in names}
            for cand in name_candidates:
                candidates = [cand, cand.replace(" ", ""), cand.replace(" ", "-")]
                for candidate in candidates:
                    if candidate.lower() in lowered:
                        font.set_variation_by_name(lowered[candidate.lower()])
                        return True
    except Exception:
        pass
    return False


def _set_font_weight_axis_if_possible(
    font: ImageFont.FreeTypeFont, weight_value: Optional[int]
) -> bool:
    if weight_value is None:
        return False
    try:
        if hasattr(font, "get_variation_axes") and hasattr(font, "set_variation_by_axes"):
            axes = font.get_variation_axes() or []
            if not axes:
                return False
            values = []
            wght_index = None
            for idx, axis in enumerate(axes):
                tag = axis.get("tag") or axis.get("name")
                if isinstance(tag, str) and tag.lower() == "wght":
                    wght_index = idx
                values.append(axis.get("default", 0))
            if wght_index is None:
                return False
            min_w = axes[wght_index].get("min", weight_value)
            max_w = axes[wght_index].get("max", weight_value)
            clamped = max(min_w, min(max_w, weight_value))
            values[wght_index] = clamped
            font.set_variation_by_axes(values)
            return True
    except Exception:
        pass
    return False


def load_inter_variable_font(
    font_name: str,
    font_size: int,
    instance_name: Optional[str],
    weight_value: Optional[int],
) -> ImageFont.FreeTypeFont:
    font_path = os.path.join(FONTS_DIR, font_name)
    if os.path.isfile(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
            name_candidates: List[str] = []
            if instance_name:
                name_candidates.append(instance_name)
            if instance_name and instance_name.lower() == "extra bold":
                name_candidates += ["ExtraBold", "Extra Bold", "Extrabold"]
            if instance_name and instance_name.lower() == "bold":
                name_candidates += ["Bold"]

            if name_candidates and _set_font_variation_by_name_if_possible(font, name_candidates):
                return font

            if _set_font_weight_axis_if_possible(font, weight_value):
                return font

            return font
        except Exception:
            pass
    return ImageFont.load_default()


def measure_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font, anchor="la")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def wrap_text_to_width(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> List[str]:
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current_line: List[str] = []

    for word in words:
        trial = (" ".join(current_line + [word])).strip()
        width, _ = measure_text(draw, trial, font)
        if width <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    rect_xywh: Tuple[float, float, float, float],
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    h_align: str = "left",
    v_align: str = "top",
    line_spacing_px: int = 0,
) -> None:
    x, y, width, height = rect_xywh
    x = int(round(x))
    y = int(round(y))
    width = int(round(width))
    height = int(round(height))

    lines = wrap_text_to_width(draw, text, font, width)

    ascent, descent = font.getmetrics()
    base_line_height = ascent + descent
    if line_spacing_px == 0:
        line_spacing_px = max(2, int(0.2 * base_line_height))
    line_heights = []
    for line in lines:
        _, line_height = measure_text(draw, line, font)
        line_heights.append(line_height)
    total_text_height = sum(line_heights) + (len(lines) - 1) * line_spacing_px

    if v_align.lower() in ("middle", "center", "centre"):
        start_y = y + (height - total_text_height) // 2
    elif v_align.lower() in ("bottom", "right"):
        start_y = y + height - total_text_height
    else:
        start_y = y

    current_y = start_y
    for line in lines:
        line_width, line_height = measure_text(draw, line, font)
        if h_align.lower() in ("center", "centre"):
            line_x = x + (width - line_width) // 2
        elif h_align.lower() in ("right", "bottom"):
            line_x = x + width - line_width
        else:
            line_x = x
        draw.text((line_x, current_y), line, font=font, fill=fill)
        current_y += line_height + line_spacing_px


def fit_image_into_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    width, height = img.size
    if width == 0 or height == 0:
        return img
    scale = min(max_w / width, max_h / height)
    new_size = (int(round(width * scale)), int(round(height * scale)))
    return img.resize(new_size, Image.LANCZOS)


LANG_IMAGE_MAP = {
    ".NET": "dotnet.jpg",
    "DOTNET": "dotnet.jpg",
    "NET": "dotnet.jpg",
    "C#": "dotnet.jpg",
    "CSHARP": "dotnet.jpg",
    "JAVA": "java.jpg",
    "Java": "java.jpg",
    "java": "java.jpg",
    "PYTHON": "python.jpg",
    "PY": "python.jpg",
    "NODEJS": "nodejs.jpg",
    "NODE": "nodejs.jpg",
}

IMAGE_ALIGNMENT_MAP = {
    "right": "default-right.png",
    "left": "default-left.jpg",
}


def extract_language(product_name: str) -> str:
    if " for " not in product_name.lower():
        return ""
    return product_name.split("for")[-1].strip()


def normalize_language(lang: str) -> str:
    return lang.replace(" ", "").replace("-", "").replace(".", "").upper()


def load_background_image(product_name: str, alignment: str):
    alignment = alignment.lower()
    filename = IMAGE_ALIGNMENT_MAP.get(alignment, "default-blank.png")
    file_path = os.path.join(TEMPLATE_DIR, filename)
    img = Image.open(file_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    return img, draw


def generate_cover_image(
    product_family: str,
    main_Heading: str,
    product_label_alignment: str,
    output_path: str,
) -> str:
    img, draw = load_background_image(product_family, product_label_alignment)

    max_font_size = 64
    min_font_size = 12
    chars_per_step = 5
    size_decrement = 10
    language_font_size = max(
        min_font_size,
        max_font_size
        - ((max(0, len(extract_language(product_family)) - 5) // chars_per_step) * size_decrement),
    )

    font_main_heading = load_inter_variable_font(
        font_name="Montserrat-Bold.ttf",
        font_size=76,
        instance_name="ExtraBold",
        weight_value=600,
    )
    font_product_family = load_inter_variable_font(
        font_name="Montserrat-Bold.ttf",
        font_size=26,
        instance_name="Bold",
        weight_value=800,
    )
    font_language_variant = load_inter_variable_font(
        font_name="Poppins-Bold.ttf",
        font_size=language_font_size,
        instance_name="Bold",
        weight_value=800,
    )

    white = (255, 255, 255)
    title_x, title_y = 94.0, 216.0
    title_w, title_h = 1050.04, 90.32
    draw_text_block(
        draw=draw,
        text=main_Heading,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_main_heading,
        fill=white,
        h_align="left",
        v_align="center",
    )

    alignment = product_label_alignment.lower()
    if alignment == "right":
        right_margin = 60
        bbox = draw.textbbox((0, 0), product_family, font=font_product_family)
        text_width = bbox[2] - bbox[0]
        title_x = img.width - right_margin - text_width
        title_y = 535.0
        title_w, title_h = text_width, 90.32
    else:
        title_x, title_y = 64.0, 535.0
        title_w, title_h = 700.04, 90.32

    draw_text_block(
        draw=draw,
        text=product_family,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_product_family,
        fill=white,
        h_align="left",
        v_align="top",
    )

    text = extract_language(product_family)
    color_map = {
        ".NET": (0, 109, 226),
        "Java": (255, 95, 84),
        "Node.js": (94, 170, 101),
        "Python": (251, 189, 57),
    }
    fill_color = color_map.get(text, (0, 109, 226))

    if alignment == "right":
        title_x, title_y = 95.0, 450.0
    else:
        title_x, title_y = 895.0, 455.0
    title_w, title_h = 210.04, 90.32
    draw_text_block(
        draw=draw,
        text=text,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_language_variant,
        fill=fill_color,
        h_align="center",
        v_align="top",
    )

    output_file_name = product_family.lower().replace(" ", "-").replace(".", "-").replace("--", "-")
    output_file = f"{output_file_name}.jpg"
    if output_path == "":
        output_path = os.path.join(BASE_DIR, "output", output_file)

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    img.convert("RGB").save(output_path, format="JPEG", quality=95)

    return output_path
