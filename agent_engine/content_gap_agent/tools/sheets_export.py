from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE_HEADER_KEYS = [
    "brand_key",
    "product_key",
    "baseline_platform",
    "category",
    "sub_category",
    "topic",
]

HEADER_LABELS = {
    "brand_key": "Brand",
    "product_key": "Product",
    "baseline_platform": "Baseline Platform",
    "category": "Category",
    "sub_category": "Sub Category",
    "topic": "Topic",
}


def _sanitize_brand_key(brand_key: str) -> str:
    return str(brand_key or "").strip().lower()


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


def resolve_sheet_config(settings: Any, brand_key: str) -> dict[str, str]:
    normalized_brand = _sanitize_brand_key(brand_key)
    sheets = getattr(settings, "TOPICS_SHEETS", {}) or {}
    brand_cfg = None
    if isinstance(sheets, dict):
        for key, value in sheets.items():
            if _sanitize_brand_key(str(key)) == normalized_brand:
                brand_cfg = value
                break
    if isinstance(brand_cfg, dict):
        return _normalize_sheet_config(normalized_brand, brand_cfg)

    # Backward compatibility for the original Aspose env var names.
    if normalized_brand == "aspose":
        return _normalize_sheet_config(
            normalized_brand,
            {
                "webhook_url": str(getattr(settings, "TOPICS_ASPOSE_COM_WEBHOOK_URL", "") or "").strip(),
                "token": str(getattr(settings, "TOPICS_ASPOSE_COM_TOKEN", "") or "").strip(),
                "coverage_json": str(getattr(settings, "TOPICS_ASPOSE_COM_COVERAGE_JSON", "") or "").strip(),
                "output_json": "outputs/google_sheets/topics_blog_aspose_com_missing_topics.json",
            },
        )
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
    configured = payload.get("platforms") or []
    ordered: list[str] = []
    seen: set[str] = set()

    if isinstance(configured, list):
        for item in configured:
            platform = str(item or "").strip()
            if platform and platform not in seen:
                ordered.append(platform)
                seen.add(platform)

    for row in rows:
        coverage = row.get("coverage") or {}
        if not isinstance(coverage, dict):
            continue
        for platform in coverage.keys():
            platform = str(platform or "").strip()
            if platform and platform not in seen:
                ordered.append(platform)
                seen.add(platform)

    return ordered


def _extract_rows(coverage_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = _load_json(coverage_path)
    brand_key = str(payload.get("brand_key") or "").strip()
    product_key = str(payload.get("product_key") or "").strip()
    baseline_platform = str(payload.get("baseline_platform") or "all").strip() or "all"
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError(f"Expected rows array in {coverage_path}")

    platform_keys = _collect_platforms(payload, rows)
    extracted: list[dict[str, Any]] = []
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

        matched_platforms = {
            platform: str((cell or {}).get("url") or "")
            for platform, cell in coverage.items()
            if bool((cell or {}).get("matched"))
        }

        item = {
            "brand_key": brand_key,
            "product_key": product_key,
            "baseline_platform": baseline_platform,
            "category": row.get("category") or "",
            "sub_category": row.get("sub_category") or "",
            "topic": row.get("topic") or "",
        }
        for platform in platform_keys:
            matched_url = matched_platforms.get(platform) or ""
            item[platform.upper()] = _sheet_hyperlink(matched_url, "YES") if matched_url else "NO"

        extracted.append(item)

    return extracted, platform_keys


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
            str(row["product_key"]),
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


def post_payload(payload: dict[str, Any], url: str, token: str | None) -> tuple[int, str]:
    query = {}
    if token:
        query["token"] = token

    endpoint = url
    if query:
        endpoint = f"{url}?{urllib.parse.urlencode(query)}"

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text
