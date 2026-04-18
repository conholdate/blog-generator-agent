from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Mapping, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .normalization import normalize_missing_platform

GOOGLE_SHEETS_SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)

SOURCE_REQUIRED_HEADERS = (
    "Brand",
    "Product",
    "Baseline Platform",
    "Category",
    "Sub Category",
    "Topic",
    "PHP",
    "SHAREPOINT",
    "JASPERREPORTS",
    "REPORTING SERVICES",
    "JAVASCRIPT",
    "GO",
    "RUST",
    "CPP",
    "GENERAL",
    "JAVA",
    "NET",
    "NODEJS",
    "PYTHON",
)

SOURCE_REQUIRED_HEADER_ALIASES: Dict[str, tuple[str, ...]] = {
    "ANDROID": ("ANDROID", "ANDROID_VIA_JAVA"),
}

SHEET_PLATFORM_COLUMNS: Dict[str, Optional[str]] = {
    "ANDROID": "android_via_java",
    "ANDROID_VIA_JAVA": "android_via_java",
    "CPP": "cpp",
    "GENERAL": None,
    "GO": "go_via_cpp",
    "JAVA": "java",
    "JASPERREPORTS": "jasperreports",
    "JAVASCRIPT": "javascript_via_cpp",
    "NET": "net",
    "NODEJS": "nodejs",
    "PHP": "php",
    "PYTHON": "python",
    "REPORTING SERVICES": "reporting_services",
    "RUST": "rust_via_cpp",
    "SHAREPOINT": "sharepoint",
}

OUTPUT_HEADERS = [
    "generated_at_utc",
    "run_id",
    "status",
    "source_sheet_row",
    "brand",
    "product",
    "baseline_platform",
    "category",
    "sub_category",
    "seed_topic",
    "selected_platform",
    "generated_title",
    "primary_keyword",
    "secondary_keywords",
    "long_tail_keywords",
    "semantic_keywords",
    "target_persona",
    "angle",
    "outline",
    "editorial_notes",
    "markdown_path",
]


@dataclass(frozen=True)
class TopicSheetSelection:
    brand: str
    product: str
    baseline_platform: str
    category: str
    sub_category: str
    topic: str
    row_index: int
    platforms: List[str]


def normalize_spreadsheet_id(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", text)
    if match:
        return match.group(1)
    return text


def _build_sheets_service(credentials_file: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=GOOGLE_SHEETS_SCOPES,
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _row_to_mapping(headers: List[str], values: List[str]) -> Dict[str, str]:
    padded = list(values) + [""] * max(0, len(headers) - len(values))
    return {header: (padded[idx] if idx < len(padded) else "") for idx, header in enumerate(headers)}


def _find_missing_source_headers(headers: List[str]) -> List[str]:
    missing: List[str] = []
    for header in SOURCE_REQUIRED_HEADERS:
        if header not in headers:
            missing.append(header)

    for canonical, aliases in SOURCE_REQUIRED_HEADER_ALIASES.items():
        if not any(alias in headers for alias in aliases):
            missing.append(canonical)

    return missing


def _sheet_cell_is_missing(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return text == "NO"


def fetch_topic_sheet_selection(
    *,
    credentials_file: str,
    spreadsheet_id: str,
    worksheet_name: str,
    row_index: int,
) -> TopicSheetSelection:
    if row_index < 2:
        raise ValueError("Google Sheet row index must be >= 2 because row 1 is reserved for headers.")

    spreadsheet_id = normalize_spreadsheet_id(spreadsheet_id)
    service = _build_sheets_service(credentials_file)
    ranges = [
        f"'{worksheet_name}'!1:1",
        f"'{worksheet_name}'!{row_index}:{row_index}",
    ]

    try:
        response = (
            service.spreadsheets()
            .values()
            .batchGet(
                spreadsheetId=spreadsheet_id,
                ranges=ranges,
                majorDimension="ROWS",
                valueRenderOption="FORMATTED_VALUE",
            )
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Failed to read Google Sheet row {row_index}: {exc}") from exc

    value_ranges = response.get("valueRanges", [])
    header_values = (value_ranges[0].get("values") or [[]])[0] if len(value_ranges) > 0 else []
    row_values = (value_ranges[1].get("values") or [[]])[0] if len(value_ranges) > 1 else []

    headers = [str(v).strip() for v in header_values if str(v).strip()]
    missing_headers = _find_missing_source_headers(headers)
    if missing_headers:
        raise ValueError(
            f"Google Sheet is missing required headers: {', '.join(missing_headers)}."
        )
    if not row_values:
        raise ValueError(f"Row #{row_index} was not found or is empty in worksheet '{worksheet_name}'.")

    row = _row_to_mapping(headers, [str(v).strip() for v in row_values])
    platforms: List[str] = []
    for column_name, platform_key in SHEET_PLATFORM_COLUMNS.items():
        if not platform_key:
            continue
        if _sheet_cell_is_missing(row.get(column_name)):
            normalized = normalize_missing_platform(platform_key)
            if normalized and normalized not in platforms:
                platforms.append(normalized)

    topic = row.get("Topic", "").strip()
    if not topic:
        raise ValueError(f"Row #{row_index} does not contain a Topic value.")

    return TopicSheetSelection(
        brand=row.get("Brand", "").strip(),
        product=row.get("Product", "").strip(),
        baseline_platform=row.get("Baseline Platform", "").strip(),
        category=row.get("Category", "").strip(),
        sub_category=row.get("Sub Category", "").strip(),
        topic=topic,
        row_index=row_index,
        platforms=platforms,
    )


def ensure_output_headers(
    *,
    credentials_file: str,
    spreadsheet_id: str,
    worksheet_name: str,
) -> None:
    spreadsheet_id = normalize_spreadsheet_id(spreadsheet_id)
    service = _build_sheets_service(credentials_file)
    header_range = f"'{worksheet_name}'!1:1"
    try:
        existing = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                majorDimension="ROWS",
                valueRenderOption="FORMATTED_VALUE",
            )
            .execute()
        )
        existing_values = existing.get("values") or []
        if existing_values and existing_values[0]:
            return

        (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                valueInputOption="RAW",
                body={"values": [OUTPUT_HEADERS]},
            )
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Failed to initialize Google Sheet output headers: {exc}") from exc


def append_output_row(
    *,
    credentials_file: str,
    spreadsheet_id: str,
    worksheet_name: str,
    row_payload: Mapping[str, Any],
) -> None:
    spreadsheet_id = normalize_spreadsheet_id(spreadsheet_id)
    service = _build_sheets_service(credentials_file)
    ordered = [str(row_payload.get(header, "") or "") for header in OUTPUT_HEADERS]
    append_range = f"'{worksheet_name}'!A:A"
    try:
        (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=append_range,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [ordered]},
            )
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Failed to append output row to Google Sheet: {exc}") from exc


def build_output_row(
    *,
    selection: TopicSheetSelection,
    selected_platform: str,
    result: Any,
    markdown_path: str,
) -> Dict[str, str]:
    def _multiline(values: Any) -> str:
        if not isinstance(values, list):
            return str(values or "")
        items = [str(v).strip() for v in values if str(v or "").strip()]
        return "\n".join(items)

    topic = result.topics[0] if getattr(result, "topics", None) else None
    keyword_groups = getattr(topic, "keyword_groups", None) if topic is not None else None
    core_keywords = getattr(keyword_groups, "core_seo_keywords", []) if keyword_groups else []
    long_tail_keywords = getattr(keyword_groups, "long_tail_keywords", []) if keyword_groups else []
    context_keywords = getattr(keyword_groups, "context_keywords", []) if keyword_groups else []
    editorial_notes = getattr(topic, "editorial_notes", []) if topic is not None else []
    outline = getattr(topic, "outline", []) if topic is not None else []

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": getattr(result, "run_id", ""),
        "status": "ok" if topic is not None else "no_topics_generated",
        "source_sheet_row": str(selection.row_index),
        "brand": selection.brand,
        "product": selection.product,
        "baseline_platform": selection.baseline_platform,
        "category": selection.category,
        "sub_category": selection.sub_category,
        "seed_topic": selection.topic,
        "selected_platform": selected_platform,
        "generated_title": getattr(topic, "title", "") if topic is not None else "",
        "primary_keyword": getattr(topic, "primary_keyword", "") if topic is not None else "",
        "secondary_keywords": _multiline(core_keywords),
        "long_tail_keywords": _multiline(long_tail_keywords),
        "semantic_keywords": _multiline(context_keywords),
        "target_persona": getattr(topic, "target_persona", "") if topic is not None else "",
        "angle": getattr(topic, "angle", "") if topic is not None else "",
        "outline": _multiline(outline),
        "editorial_notes": _multiline(editorial_notes),
        "markdown_path": markdown_path,
    }
