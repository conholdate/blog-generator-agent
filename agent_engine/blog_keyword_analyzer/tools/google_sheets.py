from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import socket
import ssl
import time
from typing import Any, Callable, Dict, List, Mapping, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .normalization import KeywordRefiner, canonical_product_name, normalize_missing_platform

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
    "GENERAL": "general",
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
    "question_keywords",
    "entity_keywords",
    "primary_keyword_intent",
    "primary_keyword_score",
    "primary_keyword_aeo_score",
    "primary_keyword_placement",
    "keyword_clusters",
    "rejected_keywords",
    "target_persona",
    "angle",
    "outline",
    "editorial_notes",
    "markdown_path",
]

refiner = KeywordRefiner()


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


def _is_retriable_google_sheets_error(exc: BaseException) -> bool:
    if isinstance(exc, HttpError):
        status = getattr(getattr(exc, "resp", None), "status", None)
        return status in {408, 429, 500, 502, 503, 504}
    return isinstance(exc, (TimeoutError, ConnectionError, socket.timeout, ssl.SSLError))


def execute_google_sheets_request(
    build_request: Callable[[], Any],
    *,
    operation: str,
    attempts: int = 5,
    initial_delay: float = 1.0,
) -> Any:
    last_exc: BaseException | None = None
    for attempt in range(1, max(attempts, 1) + 1):
        try:
            return build_request().execute()
        except BaseException as exc:
            if not _is_retriable_google_sheets_error(exc) or attempt >= attempts:
                raise
            last_exc = exc
            delay = initial_delay * (2 ** (attempt - 1))
            print(
                f"Google Sheets {operation} failed on attempt {attempt}/{attempts}: {exc}. "
                f"Retrying in {delay:.1f}s...",
                flush=True,
            )
            time.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Google Sheets {operation} did not execute.")


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
        response = execute_google_sheets_request(
            lambda: service.spreadsheets()
            .values()
            .batchGet(
                spreadsheetId=spreadsheet_id,
                ranges=ranges,
                majorDimension="ROWS",
                valueRenderOption="FORMATTED_VALUE",
            ),
            operation=f"read row {row_index}",
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
        if _sheet_cell_is_missing(row.get(column_name)):
            normalized = "general" if platform_key == "general" else normalize_missing_platform(platform_key)
            if normalized and normalized not in platforms:
                platforms.append(normalized)

    topic = row.get("Topic", "").strip()
    if not topic:
        raise ValueError(f"Row #{row_index} does not contain a Topic value.")

    return TopicSheetSelection(
        brand=row.get("Brand", "").strip(),
        product=canonical_product_name(row.get("Brand", "").strip(), row.get("Product", "").strip()),
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
        existing = execute_google_sheets_request(
            lambda: service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                majorDimension="ROWS",
                valueRenderOption="FORMATTED_VALUE",
            ),
            operation="read output headers",
        )
        existing_values = existing.get("values") or []
        existing_headers = [str(v).strip() for v in (existing_values[0] if existing_values else [])]
        if existing_headers:
            merged_headers = list(existing_headers)
            for header in OUTPUT_HEADERS:
                if header not in merged_headers:
                    merged_headers.append(header)
            if merged_headers == existing_headers:
                return
            execute_google_sheets_request(
                lambda: service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=header_range,
                    valueInputOption="RAW",
                    body={"values": [merged_headers]},
                ),
                operation="update output headers",
            )
            return

        execute_google_sheets_request(
            lambda: service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                valueInputOption="RAW",
                body={"values": [OUTPUT_HEADERS]},
            ),
            operation="initialize output headers",
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
    header_range = f"'{worksheet_name}'!1:1"
    append_range = f"'{worksheet_name}'!A:A"
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
        header_values = existing.get("values") or []
        active_headers = [str(v).strip() for v in (header_values[0] if header_values else []) if str(v).strip()]
        ordered_headers = active_headers or OUTPUT_HEADERS
        ordered = [str(row_payload.get(header, "") or "") for header in ordered_headers]
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
    def _mapping(value: Any) -> Dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        if hasattr(value, "model_dump"):
            try:
                dumped = value.model_dump()
                if isinstance(dumped, Mapping):
                    return dict(dumped)
            except Exception:
                return {}
        if hasattr(value, "dict"):
            try:
                dumped = value.dict()
                if isinstance(dumped, Mapping):
                    return dict(dumped)
            except Exception:
                return {}
        return {}

    def _field(value: Any, key: str, default: Any = "") -> Any:
        if isinstance(value, Mapping):
            return value.get(key, default)
        return getattr(value, key, default)

    def _multiline(values: Any) -> str:
        if not isinstance(values, list):
            return str(values or "")
        items = [str(v).strip() for v in values if str(v or "").strip()]
        return "\n".join(items)

    def _keyword_multiline(values: Any) -> str:
        if not isinstance(values, list):
            return _display_keyword(str(values or ""))
        items = [_display_keyword(str(v)) for v in values if str(v or "").strip()]
        return "\n".join(items)

    def _display_keyword(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text.endswith("?"):
            return text
        text = refiner.to_title_case(text)
        text = re.sub(r"(?i)\b2d\b", "2D", text)
        text = re.sub(r"(?i)\b3d\b", "3D", text)
        text = re.sub(r"(?i)\bgis\b", "GIS", text)
        return text

    def _keyword_values(values: Any) -> List[str]:
        if values is None:
            return []
        if isinstance(values, str):
            return [values.strip()] if values.strip() else []
        if not isinstance(values, list):
            value = _field(values, "keyword", "")
            return [str(value).strip()] if str(value or "").strip() else []

        keywords: List[str] = []
        for item in values:
            if isinstance(item, str):
                keyword = item
            else:
                keyword = _field(item, "keyword", "")
            keyword = str(keyword or "").strip()
            if keyword:
                keywords.append(keyword)
        return keywords

    def _keyword_key(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    def _dedupe_keywords(values: Any, *, exclude: Any = None) -> List[str]:
        excluded = {_keyword_key(v) for v in _keyword_values(exclude)}
        seen: set[str] = set()
        keywords: List[str] = []
        for value in _keyword_values(values):
            key = _keyword_key(value)
            if not key or key in excluded or key in seen:
                continue
            seen.add(key)
            keywords.append(value)
        return keywords

    topic = result.topics[0] if getattr(result, "topics", None) else None
    keyword_groups = _mapping(_field(topic, "keyword_groups", None)) if topic is not None else {}
    keyword_analysis = _mapping(_field(topic, "keyword_analysis", None)) if topic is not None else {}
    primary_keyword = _field(topic, "primary_keyword", "") if topic is not None else ""
    supporting_keywords = _keyword_values(_field(topic, "supporting_keywords", [])) if topic is not None else []
    core_keywords = _dedupe_keywords(keyword_groups.get("core_seo_keywords") or [])
    long_tail_keywords = _dedupe_keywords(keyword_groups.get("long_tail_keywords") or [], exclude=[primary_keyword])
    context_keywords = _dedupe_keywords(keyword_groups.get("context_keywords") or [], exclude=[primary_keyword])
    analysis_secondary = keyword_analysis.get("secondary_keywords") or []
    analysis_long_tail = keyword_analysis.get("long_tail_keywords") or []
    analysis_inventory = keyword_analysis.get("keyword_inventory") or []
    analysis_aio_aeo = keyword_analysis.get("aio_aeo_keywords") or []
    analysis_semantic = keyword_analysis.get("semantic_keywords") or []
    question_keywords = keyword_analysis.get("question_keywords") or []
    entity_keywords = keyword_analysis.get("entities") or []
    rejected_keywords = keyword_analysis.get("rejected_keywords") or []
    primary_analysis = _mapping(keyword_analysis.get("primary_keyword"))
    primary_intent = primary_analysis.get("intent", "")
    primary_score = primary_analysis.get("score", "")
    primary_aeo_score = primary_analysis.get("aeo_score", "")
    primary_placement = primary_analysis.get("placement") or []
    clusters = keyword_analysis.get("keyword_clusters") or []
    editorial_notes = _field(topic, "editorial_notes", []) if topic is not None else []
    outline = _field(topic, "outline", []) if topic is not None else []

    if not core_keywords:
        core_keywords = _dedupe_keywords(analysis_secondary, exclude=[primary_keyword])
    if not core_keywords:
        core_keywords = _dedupe_keywords(supporting_keywords[:1], exclude=[primary_keyword])
    if not core_keywords:
        core_keywords = _dedupe_keywords(analysis_inventory, exclude=[primary_keyword])[:5]

    if not long_tail_keywords:
        long_tail_keywords = _dedupe_keywords(analysis_long_tail, exclude=[primary_keyword] + core_keywords)
    if not long_tail_keywords:
        supporting_tail = [kw for kw in supporting_keywords if len(str(kw).split()) >= 4]
        long_tail_keywords = _dedupe_keywords(supporting_tail, exclude=[primary_keyword] + core_keywords)
    if not long_tail_keywords:
        long_tail_keywords = _dedupe_keywords(analysis_aio_aeo, exclude=[primary_keyword] + core_keywords)[:5]
    if not long_tail_keywords:
        long_tail_keywords = _dedupe_keywords(analysis_inventory, exclude=[primary_keyword] + core_keywords)[:5]

    if not context_keywords:
        context_keywords = _dedupe_keywords(analysis_semantic, exclude=[primary_keyword] + core_keywords + long_tail_keywords)

    cluster_lines: list[str] = []
    for cluster in clusters:
        cluster_name = _field(cluster, "cluster_name", "") if cluster is not None else ""
        cluster_keywords = _field(cluster, "keywords", []) if cluster is not None else []
        if cluster_name and cluster_keywords:
            cluster_lines.append(f"{cluster_name}: {', '.join(_display_keyword(str(v)) for v in cluster_keywords if str(v).strip())}")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": getattr(result, "run_id", ""),
        "status": "Queued" if topic is not None else "no_topics_generated",
        "source_sheet_row": str(selection.row_index),
        "brand": selection.brand,
        "product": selection.product,
        "baseline_platform": selection.baseline_platform,
        "category": selection.category,
        "sub_category": selection.sub_category,
        "seed_topic": selection.topic,
        "selected_platform": selected_platform,
        "generated_title": getattr(topic, "title", "") if topic is not None else "",
        "primary_keyword": _display_keyword(primary_keyword),
        "secondary_keywords": _keyword_multiline(core_keywords),
        "long_tail_keywords": _keyword_multiline(long_tail_keywords),
        "semantic_keywords": _keyword_multiline(context_keywords),
        "question_keywords": _keyword_multiline(question_keywords),
        "entity_keywords": _keyword_multiline(entity_keywords),
        "primary_keyword_intent": str(primary_intent or ""),
        "primary_keyword_score": str(primary_score or ""),
        "primary_keyword_aeo_score": str(primary_aeo_score or ""),
        "primary_keyword_placement": _multiline(primary_placement),
        "keyword_clusters": _multiline(cluster_lines),
        "rejected_keywords": _keyword_multiline(rejected_keywords),
        "target_persona": getattr(topic, "target_persona", "") if topic is not None else "",
        "angle": getattr(topic, "angle", "") if topic is not None else "",
        "outline": _multiline(outline),
        "editorial_notes": _multiline(editorial_notes),
        "markdown_path": markdown_path,
    }
