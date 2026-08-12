"""
Writes changes to aspose.cloud.json.

Every write here is a targeted text edit, never a full re-serialize —
same discipline used when fixing InstallCommand by hand: touch only the
bytes that changed, so a diff shows exactly what happened and nothing
else in the file's (inconsistent, hand-edited) formatting gets disturbed.
"""
import json
import re

from .config import PRODUCTS_DATA_PATH

FIELD_ORDER = [
    "ProductName", "Category", "ProgrammingLanguage", "ProductURL", "DownloadURL",
    "ExternalDownloadURL", "DocumentationURL", "BlogsURL", "APIReferenceURL",
    "FreeAppsURL", "ForumsURL", "InstallCommand", "urlPrefix", "license",
]


def load_raw_and_parsed() -> tuple[str, list[dict]]:
    with open(PRODUCTS_DATA_PATH, "r") as f:
        text = f.read()
    return text, json.loads(text)


def patch_field(text: str, product_name: str, field_name: str, new_value: str) -> tuple[str, bool]:
    """Replace one field's value inside the entry matching product_name.
    Returns (new_text, changed)."""
    name_pattern = re.compile(r'"ProductName"\s*:\s*"((?:[^"\\]|\\.)*)"')
    matches = list(name_pattern.finditer(text))
    for i, m in enumerate(matches):
        if m.group(1) != product_name:
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]
        field_pattern = re.compile(rf'("{re.escape(field_name)}"\s*:\s*)"(?:[^"\\]|\\.)*"')
        new_chunk, n = field_pattern.subn(lambda mm: mm.group(1) + json.dumps(new_value), chunk, count=1)
        if n == 0:
            return text, False
        return text[:start] + new_chunk + text[end:], True
    return text, False


def apply_field_fixes(fixes: list[dict]) -> dict:
    """fixes: [{"ProductName": ..., "field": ..., "value": ...}, ...]"""
    text, _ = load_raw_and_parsed()
    applied, skipped = [], []
    for fix in fixes:
        text, changed = patch_field(text, fix["ProductName"], fix["field"], fix["value"])
        (applied if changed else skipped).append(fix["ProductName"] + "." + fix["field"])

    _validate_and_write(text, expected_min_entries=1)
    return {"applied": applied, "skipped": skipped}


def append_new_entries(entries: list[dict]) -> dict:
    """entries: list of fully-derived field dicts, one per new product/platform."""
    text, parsed = load_raw_and_parsed()
    before_count = len(parsed)

    insert_point = text.rstrip().rfind("]")
    if insert_point == -1:
        raise ValueError("Could not find the closing ']' of the products array")

    body_before = text[:insert_point].rstrip()
    trailing = text[insert_point:]

    pieces = []
    for values in entries:
        ordered = {k: values.get(k, "") for k in FIELD_ORDER}
        pieces.append(json.dumps(ordered, indent=2))

    addition = ",\n" + ",\n".join(pieces) if body_before.endswith("}") else "\n".join(pieces)
    new_text = body_before + addition + "\n" + trailing

    parsed_after = _validate_and_write(new_text, expected_min_entries=before_count + len(entries))
    return {"added": len(entries), "total_entries": len(parsed_after)}


def _validate_and_write(text: str, expected_min_entries: int) -> list[dict]:
    parsed = json.loads(text)  # raises if the edit broke the JSON
    if len(parsed) < expected_min_entries:
        raise ValueError(f"Safety check failed: expected >= {expected_min_entries} entries, got {len(parsed)}")
    with open(PRODUCTS_DATA_PATH, "w") as f:
        f.write(text)
    return parsed
