#!/usr/bin/env python3
"""
Daily collection of GA4 + GSC data into content/dashboard_insights.json,
for the dashboard's "New Request" form insight panel (per brand|Product|
Platform: existing performance + untapped search opportunity).

Brands are onboarded one at a time as GA4 access is granted - see
ONBOARDED_BRANDS below. Each brand is collected independently: one
brand's GA4/GSC failure is logged and that brand's previous snapshot is
kept as-is, it never blanks out its own data or blocks the other brands
(see services/insights_collector.collect_brand_insights's docstring).

Usage:
  python scripts/collect_dashboard_insights.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "agent_engine" / "blog_generator"))

from config import settings  # noqa: E402
from services.insights_collector import collect_brand_insights  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "content" / "dashboard_insights.json"

# brand -> GA4 property ID setting. Add a brand here (and its
# GA4_PROPERTY_ID_<BRAND> setting in config.py) once its service account
# access is granted - no other code change needed.
ONBOARDED_BRANDS = {
    "groupdocs.cloud": settings.GA4_PROPERTY_ID_GROUPDOCS_CLOUD,
}


def _log(message: str) -> None:
    print(f"[collect_dashboard_insights] {message}", flush=True)


def main() -> None:
    if not settings.INSIGHTS_ENABLED:
        _log("INSIGHTS_ENABLED is false, skipping (kill-switch)")
        return

    previous: dict = {}
    if SNAPSHOT_PATH.exists():
        previous = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    snapshot = dict(previous)  # brands not in ONBOARDED_BRANDS keep whatever was there before
    for brand, property_id in ONBOARDED_BRANDS.items():
        if not property_id:
            _log(f"{brand}: no GA4 property ID configured, skipping")
            continue
        snapshot[brand] = collect_brand_insights(brand, property_id, previous.get(brand))

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    _log(f"wrote {SNAPSHOT_PATH} ({len(snapshot)} brand(s))")


if __name__ == "__main__":
    main()
