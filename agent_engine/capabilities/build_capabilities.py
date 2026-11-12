"""
Builds/refreshes content/capabilities/<brand>/ - the product capability
registry the dashboard's Recommended Actions uses to flag "Create" topics a
product can't actually do (e.g. "Decrypt PDF" suggested for Imaging Cloud).

Why: the dashboard's topic suggestions come from an LLM that only knows the
product's name, and the "Create" label only meant "no duplicate post exists"
- nothing checked the product supports the topic. A POC on 2026-11-03
(~/Desktop/capability-check-poc/PLAN.md) validated checking topics against
each product's official API description: 40/40 wrong-product topics caught,
0 correctly filed published posts wrongly flagged.

Output (repo files, NOT Redis - Redis was already 54/64 MB):
- <product>.json - one entry per API operation: id, short text, int8
  embedding (same quantization as the topic-duplicate index, see
  blog_generator/utils/topic_embeddings.py).
- _index.json - per-product source/version/hash/formats, format -> owning
  products, and the shared rule constants the dashboard reads.

A product is only re-embedded and rewritten when its content hash changes,
so most weekly runs commit nothing. A failed fetch keeps the product's
previous file untouched - an unattended run must never wipe capabilities.

Usage: python build_capabilities.py aspose.cloud|groupdocs.cloud [--summary-file=PATH] [--force] [--only=imaging,pdf]
Runs weekly via .github/workflows/capabilities_build.yml.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import date

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
sys.path.insert(0, os.path.join(ROOT, "agent_engine", "blog_generator"))
sys.path.insert(0, HERE)

from extract import (  # noqa: E402
    GENERIC_FORMATS,
    SHARED_FORMAT_THRESHOLD,
    STOPWORDS,
    build_format_owners,
    content_hash,
    features_from_spec,
    features_from_words_sdk,
    formats_from_spec,
    load_known_formats,
    operation_reference_url,
)
from spec_sources import BUNDLE_PRODUCTS, fetch_source  # noqa: E402

# Brand -> its configs/<folder> of product YAMLs. Each needs a BRAND_SOURCES
# entry in spec_sources.py too.
SUPPORTED_BRANDS = {"aspose.cloud": "aspose_cloud", "groupdocs.cloud": "groupdocs_cloud"}
# Minimum lead another product's best feature match needs over the selected
# product's before a topic counts as "another product's area". Tuned in the
# POC: good topics never exceeded 0.011, wrong-product ones were >= 0.061.
OTHER_AREA_MARGIN = 0.05


def _display_alias(display_name: str) -> str:
    """"Aspose.Imaging Cloud SDK" -> "Aspose.Imaging" (the product name the
    dashboard and topic index use)."""
    for suffix in (" Cloud SDK", " Cloud API", " Cloud"):
        if display_name.endswith(suffix):
            return display_name[: -len(suffix)]
    return display_name


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def _embed_features(features: list[dict]) -> list[dict]:
    from utils.topic_embeddings import embed_texts, pack_vector, quantize

    vectors = embed_texts([f["text"] for f in features])
    return [{**f, "vector": pack_vector(quantize(v))} for f, v in zip(features, vectors)]


def build(brand: str, force: bool = False, only: set[str] | None = None) -> list[str]:
    cfg_dir = os.path.join(ROOT, "configs", SUPPORTED_BRANDS[brand])
    out_dir = os.path.join(ROOT, "content", "capabilities", brand)
    os.makedirs(out_dir, exist_ok=True)
    index_path = os.path.join(out_dir, "_index.json")
    prior_index = _load_json(index_path, {})
    prior_products = prior_index.get("products") or {}

    known_formats = load_known_formats(_load_json(os.path.join(ROOT, "configs", "file_formats.json"), {}))
    configs = {}
    for path in sorted(glob.glob(os.path.join(cfg_dir, "*.yaml"))):
        cfg = yaml.safe_load(open(path, encoding="utf-8")) or {}
        if cfg.get("key") and cfg.get("enabled", True):
            configs[cfg["key"]] = cfg

    products: dict[str, dict] = {}
    lines: list[str] = []
    today = date.today().isoformat()

    for key, cfg in configs.items():
        if key in BUNDLE_PRODUCTS:
            continue
        prior = prior_products.get(key)
        file_path = os.path.join(out_dir, f"{key}.json")
        if only and key not in only:
            if prior:
                products[key] = prior
            continue

        src = fetch_source(key, (prior or {}).get("version", ""), brand)
        if src.status != "ok":
            if prior and os.path.exists(file_path):
                products[key] = prior
                lines.append(f"- ⚠️ **{key}**: {src.status} ({src.error}) - kept previous data")
            else:
                lines.append(f"- ❌ **{key}**: {src.status} ({src.error}) - no data")
            continue

        if src.kind == "sdk":
            features = features_from_words_sdk(src.sdk_source, key)
            spec_formats: list[str] = []
        else:
            features = features_from_spec(src.spec, key)
            spec_formats = formats_from_spec(src.spec, known_formats)
        yaml_formats = {str(f).lower() for f in cfg.get("formats") or []}
        formats = sorted((set(spec_formats) | yaml_formats) - STOPWORDS - GENERIC_FORMATS)
        if not features:
            lines.append(f"- ⚠️ **{key}**: source parsed to 0 features - kept previous data")
            if prior:
                products[key] = prior
            continue

        # Proof link per operation, shown on the dashboard next to a "create"
        # topic: a deep link when the reference page shows this exact spec,
        # otherwise the product's reference page.
        features = [
            {
                "id": f["id"],
                "text": f["text"],
                "ref": operation_reference_url(src.reference_url, src.reference_spec_name, f.get("_tag", ""), f.get("_operationId", ""))
                if src.deep_link else src.reference_url,
            }
            for f in features
        ]

        digest = content_hash(features, formats)
        entry = {
            "displayName": cfg.get("display_name") or key,
            "alias": _display_alias(cfg.get("display_name") or key),
            "sourceKind": src.kind,
            "source": src.url,
            "referenceUrl": src.reference_url,
            "version": src.version,
            "hash": digest,
            "featureCount": len(features),
            "formats": formats,
            "updatedAt": (prior or {}).get("updatedAt", today),
        }
        if not force and prior and prior.get("hash") == digest and os.path.exists(file_path):
            products[key] = entry
            lines.append(f"- ✓ **{key}**: unchanged ({len(features)} features, {src.version})")
            continue

        try:
            embedded = _embed_features(features)
        except Exception as exc:  # embedding endpoint down - keep previous data
            if prior:
                products[key] = prior
            lines.append(f"- ⚠️ **{key}**: embedding failed ({str(exc)[:120]}) - kept previous data")
            continue
        entry["updatedAt"] = today
        _write_json(file_path, {"product": key, **{k: entry[k] for k in ("displayName", "alias", "source", "referenceUrl", "version", "hash")},
                                "features": embedded})
        products[key] = entry
        note = f" - note: {src.error}" if src.error else ""
        lines.append(f"- 🔄 **{key}**: updated ({len(features)} features, {len(formats)} formats, {src.version}){note}")

    from config import settings  # blog_generator/config.py

    index = {
        "brand": brand,
        "embedding": {"model": settings.PROFESSIONALIZE_EMBEDDING_MODEL, "quantizeClamp": 0.3},
        "rules": {
            "stopwords": sorted(STOPWORDS),
            "genericFormats": sorted(GENERIC_FORMATS),
            "sharedFormatThreshold": SHARED_FORMAT_THRESHOLD,
            "otherAreaMargin": OTHER_AREA_MARGIN,
        },
        # Products with no API of their own - "all products combined" at check time.
        "bundles": {b: {"alias": _display_alias((configs.get(b) or {}).get("display_name") or b)} for b in sorted(BUNDLE_PRODUCTS) if b in configs},
        "products": dict(sorted(products.items())),
        "formatOwners": build_format_owners({k: v["formats"] for k, v in products.items()}),
    }
    if index != prior_index:
        _write_json(index_path, index)
    return lines


def main() -> None:
    brand = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "aspose.cloud"
    summary_file, force, only = None, False, None
    for arg in sys.argv[1:]:
        if arg.startswith("--summary-file="):
            summary_file = arg.split("=", 1)[1]
        elif arg == "--force":
            force = True
        elif arg.startswith("--only="):
            only = {p.strip() for p in arg.split("=", 1)[1].split(",") if p.strip()}

    if brand not in SUPPORTED_BRANDS:
        lines = [f"Brand {brand!r} is not supported yet (only: {', '.join(SUPPORTED_BRANDS)})."]
    else:
        lines = build(brand, force=force, only=only)

    text = f"Capability registry refresh for **{brand}**:\n\n" + "\n".join(lines) + "\n"
    print(text)
    if summary_file:
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
