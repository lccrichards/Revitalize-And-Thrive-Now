#!/usr/bin/env python3
"""
master_orchestrator.py

Daily content automation for Revitalize and Thrive Now + Reclaim and Rise.
Runs inside the Claude Code environment — uses Higgsfield (via MCP) for images
and Composio (via REST API) for posting. Claude itself generates captions.

This script is NOT meant to be run directly from the terminal.
It is the instruction set that Claude follows when a daily trigger fires.

TRIGGER SCHEDULE (ET):
  Morning   7:00 AM  — education / authority / trust-building
  Afternoon 3:00 PM  — pain point / problem awareness
  Evening   7:00 PM  — transformation / CTA / conversion

HOW IT WORKS:
  1. Determine today's day of week and time slot (morning/afternoon/evening)
  2. Load rotation schedule from orchestrator-config.json
  3. Generate on-brand captions for both brands (Claude does this inline)
  4. Generate Higgsfield images (women for Revitalize, men for Reclaim)
  5. Post via Composio to Instagram
  6. Log results to data/orchestrator-log.json

CLAUDE EXECUTION INSTRUCTIONS:
When this trigger fires, Claude must:
  a) Read /home/user/revitalize-and-thrive-now/data/brand-config.json
  b) Read /home/user/revitalize-and-thrive-now/data/orchestrator-config.json
  c) Determine today's date, day name, and time slot from the trigger label
  d) Generate captions for both brands using the brand voice and today's product
  e) Call mcp__higgsfield__generate_image for each brand
  f) Poll mcp__higgsfield__job_display until status = completed
  g) Call mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL:
       INSTAGRAM_POST_IG_USER_MEDIA (create container)
       then INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH (publish)
  h) Append results to data/orchestrator-log.json
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"


def get_time_slot(hour_utc: int) -> str:
    """Map UTC hour to posting slot name."""
    if hour_utc == 11:
        return "morning"
    elif hour_utc == 19:
        return "afternoon"
    elif hour_utc == 23:
        return "evening"
    else:
        # Default to morning if called outside schedule
        return "morning"


def get_day_name() -> str:
    return datetime.now(timezone.utc).strftime("%A").lower()


def load_configs():
    with open(CONFIG_PATH) as f:
        brand_cfg = json.load(f)
    with open(ORCH_CONFIG_PATH) as f:
        orch_cfg = json.load(f)
    return brand_cfg, orch_cfg


def get_product(brand_cfg: dict, brand: str, product_name: str) -> dict:
    """Find a product by name in the brand config."""
    for p in brand_cfg[brand]["products"]:
        if p["name"] == product_name:
            return p
    return brand_cfg[brand]["products"][0]


def get_bundle_note(brand_cfg: dict, product_name: str) -> str:
    """Return bundle bonus text if this product triggers a bundle."""
    for p in brand_cfg["revitalize"]["products"]:
        if p["name"] == product_name and p.get("bundle_bonus"):
            return f"\n\n🎁 BONUS: Purchase today and receive the {p['bundle_bonus']} — added automatically."
    return ""


def build_revitalize_caption(product: dict, theme: str, slot: str, orch_cfg: dict) -> str:
    """
    Claude generates this inline when running the orchestrator.
    This function is a template reference — actual generation happens via Claude.
    """
    bundle_note = get_bundle_note({}, product["name"])
    slot_tone = orch_cfg["schedule"][slot]["tone"]
    return f"[Claude generates: theme={theme}, product={product['name']}, price={product['price_short']}, tone={slot_tone}, bundle={bundle_note}]"


def log_result(entry: dict):
    log = []
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            try:
                log = json.load(f)
            except Exception:
                log = []
    log.append(entry)
    # Keep last 90 entries
    log = log[-90:]
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def print_daily_brief(day: str, slot: str, brand_cfg: dict, orch_cfg: dict):
    """Print what Claude will execute today."""
    rev_rotation = orch_cfg["revitalize_rotation"][day]
    rec_rotation = orch_cfg["reclaim_rotation"][day]
    rev_product_name = rev_rotation["slot_products"][slot]
    rec_product_name = rec_rotation["slot_products"][slot]
    slot_info = orch_cfg["schedule"][slot]

    print(f"\n{'='*60}")
    print(f"MASTER ORCHESTRATOR — {slot.upper()} SLOT")
    print(f"Day: {day.title()}  |  Time: {slot_info['time_et']} ET")
    print(f"{'='*60}")
    print(f"\nREVITALIZE AND THRIVE NOW")
    print(f"  Theme   : {rev_rotation['theme']}")
    print(f"  Product : {rev_product_name}")
    print(f"  Angle   : {slot_info['angle']}")
    print(f"\nRECLAIM AND RISE")
    print(f"  Theme   : {rec_rotation['theme']}")
    print(f"  Product : {rec_product_name}")
    print(f"  Angle   : {slot_info['angle']}")
    print(f"\nTone: {slot_info['tone']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # When run directly, print the daily brief so Claude knows what to execute
    import sys
    hour_utc = datetime.now(timezone.utc).hour
    slot_arg = sys.argv[1] if len(sys.argv) > 1 else None
    slot = slot_arg if slot_arg in ("morning", "afternoon", "evening") else get_time_slot(hour_utc)
    day = get_day_name()

    brand_cfg, orch_cfg = load_configs()
    print_daily_brief(day, slot, brand_cfg, orch_cfg)
