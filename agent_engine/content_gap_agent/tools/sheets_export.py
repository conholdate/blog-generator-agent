from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests
from .normalization import canonical_topic_key

BASE_HEADER_KEYS = [
    "brand_key",
    "product_name",
    "baseline_platform",
    "category",
    "sub_category",
    "topic",
    "status",
]

HEADER_LABELS = {
    "brand_key": "Brand",
    "product_name": "Product",
    "baseline_platform": "Baseline Platform",
    "category": "Category",
    "sub_category": "Sub Category",
    "topic": "Topic",
    "status": "Status",
}

PLATFORM_COLUMNS = [
    "NET",
    "JAVA",
    "CPP",
    "PHP",
    "SHAREPOINT",
    "JASPERREPORTS",
    "REPORTING SERVICES",
    "JAVASCRIPT",
    "GO",
    "RUST",
    "NODEJS",
    "PYTHON",
    "ANDROID",
    "GENERAL",
]

PLATFORM_HEADER_ALIASES = {
    "net": "NET",
    ".net": "NET",
    "java": "JAVA",
    "cpp": "CPP",
    "c++": "CPP",
    "php": "PHP",
    "sharepoint": "SHAREPOINT",
    "jasperreports": "JASPERREPORTS",
    "reporting services": "REPORTING SERVICES",
    "reporting_services": "REPORTING SERVICES",
    "javascript via c++": "JAVASCRIPT",
    "javascript_cpp": "JAVASCRIPT",
    "go via c++": "GO",
    "go_cpp": "GO",
    "rust via c++": "RUST",
    "rust_cpp": "RUST",
    "nodejs": "NODEJS",
    "node.js": "NODEJS",
    "node.js via c++": "NODEJS",
    "nodejs via c++": "NODEJS",
    "nodejs_cpp": "NODEJS",
    "node.js via java": "NODEJS",
    "nodejs via java": "NODEJS",
    "nodejs_java": "NODEJS",
    "node.js via .net": "NODEJS",
    "nodejs via .net": "NODEJS",
    "nodejs_net": "NODEJS",
    "php via java": "PHP",
    "php_java": "PHP",
    "python": "PYTHON",
    "python via .net": "PYTHON",
    "python via java": "PYTHON",
    "python_net": "PYTHON",
    "python_java": "PYTHON",
    "android": "ANDROID",
    "android via java": "ANDROID",
    "android_java": "ANDROID",
    "general": "GENERAL",
}


def _sanitize_brand_key(brand_key: str) -> str:
    return str(brand_key or "").strip().lower()


def _canonical_platform_header(platform: str) -> str:
    raw = str(platform or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    if lowered in PLATFORM_HEADER_ALIASES:
        return PLATFORM_HEADER_ALIASES[lowered]
    return raw.upper()


def _default_output_json(brand_key: str) -> str:
    safe_brand = _sanitize_brand_key(brand_key) or "brand"
    return f"outputs/google_sheets/{safe_brand}_missing_topics.json"


def _normalize_sheet_config(brand_key: str, raw_cfg: dict[str, Any] | None) -> dict[str, str]:
    cfg = {str(k): str(v).strip() for k, v in (raw_cfg or {}).items() if v is not None and str(v).strip()}
    if not cfg:
        return {}

    cfg.setdefault("sheet_name", "All Missing Topics")
    cfg.setdefault("output_json", _default_output_json(brand_key))
    return cfg


def _legacy_sheet_config(settings: Any, brand_key: str) -> dict[str, str]:
    attr_prefixes = {
        "aspose": "TOPICS_ASPOSE_COM",
        "groupdocs": "TOPICS_GROUPDOCS_COM",
        "conholdate": "TOPICS_CONHOLDATE_COM",
        "aspose_cloud": "TOPICS_ASPOSE_CLOUD",
        "groupdocs_cloud": "TOPICS_GROUPDOCS_CLOUD",
        "conholdate_cloud": "TOPICS_CONHOLDATE_CLOUD",
    }
    prefix = attr_prefixes.get(_sanitize_brand_key(brand_key))
    if not prefix:
        return {}

    raw_cfg = {
        "webhook_url": str(getattr(settings, f"{prefix}_WEBHOOK_URL", "") or "").strip(),
        "token": str(
            getattr(settings, "TOPICS_SHEETS_TOKEN", None)
            or getattr(settings, f"{prefix}_TOKEN", "")
            or ""
        ).strip(),
        "coverage_json": str(getattr(settings, f"{prefix}_COVERAGE_JSON", "") or "").strip(),
    }
    return {key: value for key, value in raw_cfg.items() if value}


def resolve_sheet_config(settings: Any, brand_key: str) -> dict[str, str]:
    normalized_brand = _sanitize_brand_key(brand_key)
    sheets = getattr(settings, "TOPICS_SHEETS", {}) or {}
    brand_cfg: dict[str, Any] = {}
    if isinstance(sheets, dict):
        for key, value in sheets.items():
            if _sanitize_brand_key(str(key)) == normalized_brand:
                if isinstance(value, dict):
                    brand_cfg = value
                break

    legacy_cfg = _legacy_sheet_config(settings, normalized_brand)
    if brand_cfg or legacy_cfg:
        return _normalize_sheet_config(normalized_brand, {**brand_cfg, **legacy_cfg})

    return {}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _sheet_hyperlink(url: str, label: str) -> str:
    safe_url = str(url or "").replace('"', '""')
    safe_label = str(label or "").replace('"', '""')
    if not safe_url:
        return label
    return f'=HYPERLINK("{safe_url}","{safe_label}")'


def _collect_platforms(payload: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    return list(PLATFORM_COLUMNS)


def _extract_rows(coverage_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = _load_json(coverage_path)
    brand_key = str(payload.get("brand_key") or "").strip()
    product_key = str(payload.get("product_key") or "").strip()
    product_name = str(payload.get("product_name") or product_key).strip()
    baseline_platform = str(payload.get("baseline_platform") or "all").strip() or "all"
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError(f"Expected rows array in {coverage_path}")

    platform_keys = _collect_platforms(payload, rows)
    extracted_by_topic: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue

        coverage = row.get("coverage") or {}
        if not isinstance(coverage, dict):
            continue

        missing_platforms = sorted(
            platform
            for platform, cell in coverage.items()
            if not bool((cell or {}).get("matched"))
        )
        if not missing_platforms:
            continue

        matched_platforms: dict[str, str] = {}
        present_platforms: set[str] = set()
        for platform, cell in coverage.items():
            header = _canonical_platform_header(platform)
            if not header:
                continue
            present_platforms.add(header)
            if bool((cell or {}).get("matched")):
                matched_platforms[header] = str((cell or {}).get("url") or "")

        item = {
            "brand_key": brand_key,
            "product_name": product_name,
            "baseline_platform": baseline_platform,
            "category": row.get("category") or "",
            "sub_category": row.get("sub_category") or "",
            "topic": row.get("topic") or "",
            "status": "Queued",
        }
        for platform in platform_keys:
            if platform not in present_platforms:
                item[platform] = ""
                continue

            matched_url = matched_platforms.get(platform) or ""
            item[platform] = _sheet_hyperlink(matched_url, "YES") if matched_url else "NO"

        topic_key = canonical_topic_key(str(item.get("topic") or ""))
        if not topic_key:
            topic_key = str(item.get("topic") or "").strip().lower()

        existing = extracted_by_topic.get(topic_key)
        if existing is None:
            extracted_by_topic[topic_key] = item
            continue

        if not existing.get("category") and item.get("category"):
            existing["category"] = item["category"]
        if not existing.get("sub_category") and item.get("sub_category"):
            existing["sub_category"] = item["sub_category"]
        if len(str(item.get("topic") or "")) < len(str(existing.get("topic") or "")):
            existing["topic"] = item["topic"]

        for platform in platform_keys:
            current = str(existing.get(platform) or "")
            incoming = str(item.get(platform) or "")
            if current.startswith("=HYPERLINK("):
                continue
            if incoming.startswith("=HYPERLINK(") or (not current and incoming):
                existing[platform] = incoming

    return list(extracted_by_topic.values()), platform_keys


def build_payload(
    *,
    coverage_json: Path,
    sheet_name: str,
    replace: bool,
) -> dict[str, Any]:
    all_rows, platform_keys = _extract_rows(coverage_json)
    sources = [str(coverage_json)]
    header_keys = BASE_HEADER_KEYS + [platform.upper() for platform in platform_keys]
    headers = [HEADER_LABELS.get(key, key) for key in header_keys]

    all_rows.sort(
        key=lambda row: (
            str(row["brand_key"]),
            str(row["product_name"]),
            str(row["topic"]),
        )
    )

    return {
        "sheet_name": sheet_name,
        "mode": "replace" if replace else "append",
        "headers": headers,
        "rows": [[row.get(key, "") for key in header_keys] for row in all_rows],
        "meta": {
            "source_count": len(sources),
            "row_count": len(all_rows),
            "sources": sources,
        },
    }


def write_payload(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def should_post_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    mode = str(payload.get("mode") or "").strip().lower()
    meta = payload.get("meta") or {}
    row_count = int(meta.get("row_count") or 0)
    if mode == "append" and row_count == 0:
        return False, "Skipping POST for empty append payload."
    return True, ""


def is_successful_sheet_response(status: int, text: str) -> tuple[bool, str]:
    body = str(text or "").strip()
    lowered = body.lower()
    if status < 200 or status >= 300:
        return False, f"Google Sheets webhook returned status={status}: {body[:500]}"
    if "invalid token" in lowered or "unauthorized" in lowered:
        return False, f"Google Sheets webhook rejected token: {body[:500]}"
    if lowered.startswith("error:") or '"error"' in lowered:
        return False, f"Google Sheets webhook returned an error body: {body[:500]}"
    return True, ""


def post_payload(payload: dict[str, Any], url: str, token: str | None) -> tuple[int, str]:
    query: dict[str, str] = {}
    if token:
        query["token"] = token

    print("[sheets] headers before POST:")
    print(json.dumps(payload.get("headers") or [], ensure_ascii=False, indent=2))

    try:
        resp = requests.post(
            url,
            params=query,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
            allow_redirects=True,
        )
        return resp.status_code, resp.text
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None:
            return response.status_code, response.text
        return 0, str(exc)
