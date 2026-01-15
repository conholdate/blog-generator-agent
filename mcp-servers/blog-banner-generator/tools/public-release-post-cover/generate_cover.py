import argparse
import os, sys
import glob
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import requests
from PIL import Image
from io import BytesIO
import math
from fastmcp import FastMCP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, ""))

if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)

print(f"binaa - {PARENT_PATH}", flush=True, file=sys.stderr)

FONTS_DIR = os.path.join(BASE_DIR, "fonts")
LOGOS_DIR = os.path.join(BASE_DIR, "logos")


# MCP Server
mcp = FastMCP("cover_image_generator")

def load_font(preferred_paths: List[str], font_size: int) -> ImageFont.FreeTypeFont:
    for path in preferred_paths:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    # Fallback to default PIL font (not ideal, but ensures the script runs)
    return ImageFont.load_default()


def _set_font_variation_by_name_if_possible(font: ImageFont.FreeTypeFont, name_candidates: List[str]) -> bool:
    try:
        if hasattr(font, "get_variation_names") and hasattr(font, "set_variation_by_name"):
            names = font.get_variation_names() or []
            lowered = {n.lower(): n for n in names}
            for cand in name_candidates:
                cands = [cand, cand.replace(" ", ""), cand.replace(" ", "-")]
                for c in cands:
                    if c.lower() in lowered:
                        font.set_variation_by_name(lowered[c.lower()])
                        return True
    except Exception:
        pass
    return False


def _set_font_weight_axis_if_possible(font: ImageFont.FreeTypeFont, weight_value: Optional[int]) -> bool:
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
                # axis is a dict like {"name": "Weight", "tag": "wght", "min": 100, "default": 400, "max": 900}
                tag = axis.get("tag") or axis.get("name")
                if isinstance(tag, str) and tag.lower() == "wght":
                    wght_index = idx
                values.append(axis.get("default", 0))
            if wght_index is None:
                return False
            # Clamp into allowed range
            min_w = axes[wght_index].get("min", weight_value)
            max_w = axes[wght_index].get("max", weight_value)
            clamped = max(min_w, min(max_w, weight_value))
            values[wght_index] = clamped
            font.set_variation_by_axes(values)
            return True
    except Exception:
        pass
    return False


def load_inter_variable_font(font_name: str, font_size: int, instance_name: Optional[str], weight_value: Optional[int]) -> ImageFont.FreeTypeFont:
    inter_path = os.path.join(FONTS_DIR, font_name)
    if os.path.isfile(inter_path):
        try:
            fnt = ImageFont.truetype(inter_path, font_size)
            # Prefer named instance if available
            name_candidates: List[str] = []
            if instance_name:
                name_candidates.append(instance_name)
            # Add some common aliases for robustness
            if instance_name and instance_name.lower() == "extra bold":
                name_candidates += ["ExtraBold", "Extra Bold", "Extrabold", "Extrabold"]
            if instance_name and instance_name.lower() == "bold":
                name_candidates += ["Bold"]

            if name_candidates and _set_font_variation_by_name_if_possible(fnt, name_candidates):
                return fnt

            # Fallback to weight axis if supported
            if _set_font_weight_axis_if_possible(fnt, weight_value):
                return fnt

            return fnt
        except Exception:
            pass
    # Final fallback
    return ImageFont.load_default()


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font, anchor="la")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def wrap_text_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current_line: List[str] = []

    for word in words:
        trial = (" ".join(current_line + [word])).strip()
        w, _ = measure_text(draw, trial, font)
        if w <= max_width or not current_line:
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

    # Compute total text block height
    ascent, descent = font.getmetrics()
    base_line_height = ascent + descent
    if line_spacing_px == 0:
        line_spacing_px = max(2, int(0.2 * base_line_height))
    line_heights = []
    for line in lines:
        _, h = measure_text(draw, line, font)
        line_heights.append(h)
    total_text_height = sum(line_heights) + (len(lines) - 1) * line_spacing_px

    # Vertical alignment
    if v_align.lower() in ("middle", "center", "centre"):
        start_y = y + (height - total_text_height) // 2
    elif v_align.lower() in ("bottom", "right"):  # handle possible spec typo using 'right' for vertical
        start_y = y + height - total_text_height
    else:
        start_y = y

    # Draw each line with horizontal alignment
    current_y = start_y
    for i, line in enumerate(lines):
        line_width, line_height = measure_text(draw, line, font)
        if h_align.lower() in ("center", "centre"):
            line_x = x + (width - line_width) // 2
        elif h_align.lower() in ("right", "bottom"):  # handle possible spec typo using 'top'/'right'
            line_x = x + width - line_width
        else:
            line_x = x
        draw.text((line_x, current_y), line, font=font, fill=fill)
        current_y += line_height + line_spacing_px


def fit_image_into_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = img.size
    if w == 0 or h == 0:
        return img
    scale = min(max_w / w, max_h / h)
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return img.resize(new_size, Image.LANCZOS)

# Folder containing all background images
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Mapping language aliases → filename
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
    "NODE": "nodejs.jpg"
}
#DEFAULT_IMAGE = "default-left.png"

def extract_language(product_name: str) -> str:
    if " for " not in product_name.lower():
        return ""
    return product_name.split("for")[-1].strip()

def normalize_language(lang: str) -> str:
    # Remove spaces, hyphens, and dots
    return (
        lang.replace(" ", "")
            .replace("-", "")
            .replace(".", "")
            .upper()
    )

IMAGE_ALIGNMENT_MAP = {
    "right": "default-right.png",
    "left": "default-left.jpg",
}

def load_background_image(product_name: str, alignment: str):
    # 1. Extract language from input string
    lang_raw = extract_language(product_name)
    alignment = alignment.lower()

    filename = IMAGE_ALIGNMENT_MAP.get(alignment, "default-blank.png")
    is_default = alignment in IMAGE_ALIGNMENT_MAP
    
    # 3. Load image
    file_path = os.path.join(TEMPLATE_DIR, filename)
    print(f"bingoo - {file_path}", flush=True, file=sys.stderr )
    img = Image.open(file_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    return img, draw

# main method to generate banner image
def generate_cover_image(product_family: str, main_Heading: str, product_label_alignment: str, output_path: str) -> None:
    template_path = None

    # Image settings
    width = 1200
    height = 630

    img, draw = load_background_image(product_family, product_label_alignment)

    """
    font_version_size = 100
    rect_position_x = 692
    rect_position_y = 264
    rect_width = 370
    rect_height = 116
    language_font_size = 76
    if len(extract_language(product_family)) > 4:
        language_font_size = 64
        rect_position_x = 695.49
        rect_position_y = 280.27
        rect_width = 360
        rect_height = 89.1
    """
    MAX_FONT_SIZE = 64
    MIN_FONT_SIZE = 12
    CHARS_PER_STEP = 5
    SIZE_DECREMENT = 10  # pixels per step
    language_font_size = max(
        MIN_FONT_SIZE,
        MAX_FONT_SIZE - ((max(0, len(extract_language(product_family)) - 5) // CHARS_PER_STEP) * SIZE_DECREMENT))

    # Load variable font (Inter.ttf) and set variations (weights)
    font_main_heading = load_inter_variable_font(font_name="Montserrat-Bold.ttf", font_size=76, instance_name="ExtraBold", weight_value=600)
    font_product_family = load_inter_variable_font(font_name="Montserrat-Bold.ttf", font_size=26, instance_name="Bold", weight_value=800)
    font_language_variant = load_inter_variable_font(font_name="Poppins-Bold.ttf", font_size=language_font_size, instance_name="Bold", weight_value=800)
    
    # Label color
    white = (255, 255, 255)
    # 1) Main Heading of banner
    title_x, title_y = 94.0, 216.0
    title_w, title_h = 1050.04, 90.32
    # The spec lists vertical align "center" and horizontal "left"; interpret as center-left
    draw_text_block(
        draw=draw,
        text=main_Heading,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_main_heading,
        fill=white,
        h_align="left",
        v_align="center",
    )

    # 2) Product Family information
    alignment = product_label_alignment.lower()
    if alignment == "right":
        RIGHT_MARGIN = 60
        # Measure text width
        bbox = draw.textbbox(
            (0, 0),
            product_family,
            font=font_product_family
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Compute X dynamically so text ends at right margin
        title_x = img.width - RIGHT_MARGIN - text_width
        title_y = 535.0
        title_w, title_h = text_width, 90.32
    else: 
        title_x, title_y = 64.0, 535.0  # Left Alignment
        title_w, title_h = 700.04, 90.32

    # The spec lists vertical align "right" and horizontal "top"; interpret as top-right
    draw_text_block(
        draw=draw,
        text=product_family,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_product_family,
        fill=white,
        h_align="left",
        v_align="top",
    )

    """
    # 3) Rectangle parameters
    x1, y1 = 100, 420
    x2, y2 = 400, 550
    radius = 30
    outline_color = "#FFFFFF"
    fill_color = "#FFFFFF"
    width = .1

    # Draw rounded rectangle
    draw.rounded_rectangle(
        [(x1, y1), (x2, y2)],
        radius=radius,
        outline=outline_color,
        fill=fill_color,
        width=width
    )
    """

    # 4) Set programming language font color
    text = extract_language(product_family)
    COLOR_MAP = {
    '.NET': (0, 109, 226),
    'Java': (255, 95, 84),
    'Node.js': (94, 170, 101),
    'Python': (251, 189, 57),
    }
    fill_Color = COLOR_MAP.get(text, (0, 109, 226))

    if alignment == "right":
        title_x, title_y = 95.0, 450.0
    else:
        title_x, title_y = 895.0, 455.0
    title_w, title_h = 210.04, 90.32
    # The spec lists vertical align "right" and horizontal "top"; interpret as top-right
    draw_text_block(
        draw=draw,
        text=text,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_language_variant,
        fill=fill_Color,
        h_align="center",
        v_align="top",
    )

    # When output path is not specified, use product name and title separated by hyphen, replace spaces and dots with hyphen
    output_file_name = f"{product_family}".lower().replace(" ", "-").replace(".", "-").replace("--", "-")
    output_file = f"{output_file_name}.png"
    if output_path == "":
        output_path = os.path.join("output", output_file)

    # Save result (ensure output directory exists)
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    # Preserve transparency by saving with alpha (PNG)
    img.save(output_path, format="PNG")

    return output_path


# -----------------------------
# MCP TOOL
# -----------------------------
@mcp.tool()
async def generate_blog_image(
    product_family: str,
    main_Heading: str,
    product_label_alignment: str,
    output_path: str 
):
   
    output_file_path = generate_cover_image(
        product_family=product_family,
        main_Heading=main_Heading,
        product_label_alignment=product_label_alignment,
        output_path=output_path

    )
    
    return {
        "output_path": output_file_path
    }


# -----------------------------
# Start MCP
# -----------------------------
if __name__ == "__main__":
    mcp.run()