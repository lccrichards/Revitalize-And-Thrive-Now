#!/usr/bin/env python3
"""
unified_automation.py

Single entry point for Dr. Lori's content automation pipeline.
Runs the master orchestrator to generate captions, then pushes them
to Buffer for cross-platform posting (Instagram + Facebook + YouTube).

This script is designed to be called by Hermes cron jobs.

USAGE:
  python3 unified_automation.py morning
  python3 unified_automation.py afternoon
  python3 unified_automation.py evening
  python3 unified_automation.py --dry-run morning

PIPELINE:
  1. Run master_orchestrator.py [slot] → generates captions + product info
  2. Save captions to data/pending-posts-[date]-[slot].json
  3. Run auto_post_cross_platform.py → pushes to Buffer (IG + FB + YT)
  4. Log results to data/orchestrator-log.json

ENVIRONMENT:
  BUFFER_API_KEY        — required for live posting
  BUFFER_IG_CHANNEL_ID  — optional (auto-discovered)
  BUFFER_FB_CHANNEL_ID  — optional (auto-discovered)
  BUFFER_YT_CHANNEL_ID  — optional (auto-discovered)
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
REPO = Path("/Users/drlori/revitalize-and-thrive-now")
SCRIPTS = REPO / "scripts"
DATA = REPO / "data"


def run_orchestrator(slot: str) -> dict:
    """Run master_orchestrator.py to get today's product schedule."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "master_orchestrator.py"), slot],
        capture_output=True, text=True, cwd=str(REPO)
    )
    print(result.stdout)
    if result.stderr:
        print(f"  ⚠ Orchestrator stderr: {result.stderr[:200]}")

    # Check if already posted
    if "ALREADY POSTED TODAY" in result.stdout:
        return {"already_posted": True}

    return {"already_posted": False, "output": result.stdout}


def generate_pending_posts(slot: str, orch_output: str) -> list:
    """
    Parse orchestrator output and generate pending post JSON.
    In production, Claude/Hermes would generate the actual captions.
    For now, create a template that the cron job will fill.
    """
    today = datetime.now(ET).strftime("%Y-%m-%d")

    # Read brand config for product details
    config_path = DATA / "brand-config.json"
    if not config_path.exists():
        print(f"  ⚠ brand-config.json not found at {config_path}")
        return []

    with open(config_path) as f:
        brand_cfg = json.load(f)

    # Read orchestrator config for schedule
    orch_config_path = DATA / "orchestrator-config.json"
    with open(orch_config_path) as f:
        orch_cfg = json.load(f)

    # Determine day of week
    day_name = datetime.now(ET).strftime("%A").lower()

    # Get products for today's slot
    posts = []
    for brand in ["revitalize", "reclaim"]:
        if brand not in brand_cfg:
            continue

        rotation_key = f"{brand}_rotation"
        if rotation_key not in orch_cfg:
            continue
        if day_name not in orch_cfg[rotation_key]:
            continue

        rotation = orch_cfg[rotation_key][day_name]
        slot_products = rotation.get("slot_products", {})
        if slot not in slot_products:
            continue

        product_name = slot_products[slot]
        # Find product in brand config
        products = brand_cfg[brand].get("products", [])
        product = next((p for p in products if p["name"] == product_name), products[0] if products else None)

        if not product:
            continue

        slot_info = orch_cfg["schedule"].get(slot, {})
        tone = slot_info.get("tone", "educational")

        post = {
            "brand": brand,
            "product": product_name,
            "price": product.get("price_short", ""),
            "url": product.get("url", ""),
            "image_url": "",  # Will be filled by Higgsfield
            "caption": "",  # Will be filled by Claude/Hermes
            "title": f"{product_name} — {brand.title()}",
            "slot": slot,
            "tone": tone,
            "date": today,
            "status": "pending"
        }
        posts.append(post)

    # Save to pending posts file
    if posts:
        pending_path = DATA / f"pending-posts-{today}-{slot}.json"
        with open(pending_path, "w") as f:
            json.dump(posts, f, indent=2)
        print(f"  📝 Saved {len(posts)} pending posts to {pending_path}")

    return posts


def run_cross_platform_post(slot: str, dry_run: bool = False):
    """Run the cross-platform posting script."""
    cmd = [sys.executable, str(SCRIPTS / "auto_post_cross_platform.py"),
           "--brand", "both", "--slot", slot]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO))
    print(result.stdout)
    if result.stderr:
        print(f"  ⚠ Cross-platform stderr: {result.stderr[:200]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unified content automation pipeline")
    parser.add_argument("slot", choices=["morning", "afternoon", "evening"],
                        help="Time slot for content generation")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate captions but don't post to Buffer")
    parser.add_argument("--skip-orchestrator", action="store_true",
                        help="Skip orchestrator, use existing pending posts")
    args = parser.parse_args()

    today = datetime.now(ET).strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"UNIFIED AUTOMATION PIPELINE — {args.slot.upper()} SLOT")
    print(f"Date: {today} | Dry run: {args.dry_run}")
    print(f"{'='*60}\n")

    # Step 1: Run orchestrator
    if not args.skip_orchestrator:
        print("STEP 1: Running master orchestrator...")
        orch_result = run_orchestrator(args.slot)
        if orch_result.get("already_posted"):
            print("  ⏭ Already posted today. Exiting.")
            return

    # Step 2: Generate pending posts
    print("\nSTEP 2: Generating pending posts...")
    posts = generate_pending_posts(args.slot, "")

    if not posts:
        print("  ⚠ No posts generated. Check orchestrator config.")
        return

    # Step 3: Cross-platform posting
    print(f"\nSTEP 3: Cross-platform posting via Buffer...")
    run_cross_platform_post(args.slot, args.dry_run)

    print(f"\n{'='*60}")
    print(f"Pipeline complete. Check data/orchestrator-log.json for results.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
