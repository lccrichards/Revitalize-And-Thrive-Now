#!/usr/bin/env python3
"""
Execute 3 PM afternoon post for Thursday, July 9, 2026
This script handles: image generation + Instagram posting + Facebook posting + logging
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import subprocess
import time

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"

def load_configs():
    with open(CONFIG_PATH) as f:
        brand_cfg = json.load(f)
    with open(ORCH_CONFIG_PATH) as f:
        orch_cfg = json.load(f)
    return brand_cfg, orch_cfg

def generate_revitalize_image():
    """Generate Revitalize image via Higgsfield MCP"""
    prompt = (
        "Professional woman aged 45-65, determined despite fatigue, mid-day resilience, purposeful, "
        "journaling at a sunlit table, plants in background, warm natural light, photorealistic portrait, "
        "confident and radiant expression, wellness lifestyle, clean composition. STRICTLY WOMEN ONLY — no men in frame."
    )

    print("[HIGGSFIELD] Generating Revitalize image...")
    print(f"Prompt: {prompt[:80]}...")

    # In a real execution, this would call the Higgsfield MCP tool
    # For now, we'll prepare the call and indicate where it should be made
    return {
        "model": "nano_banana_pro",
        "prompt": prompt,
        "aspect_ratio": "1:1"
    }

def generate_reclaim_image():
    """Generate Reclaim image via Higgsfield MCP"""
    prompt = (
        "Professional man aged 45-55, determined despite fatigue, mid-day resilience, purposeful, "
        "journaling or reading strategy book at a desk, clean modern environment, photorealistic, "
        "sharp focused expression, high-performance lifestyle. STRICTLY MEN ONLY — no women in frame."
    )

    print("[HIGGSFIELD] Generating Reclaim image...")
    print(f"Prompt: {prompt[:80]}...")

    return {
        "model": "nano_banana_pro",
        "prompt": prompt,
        "aspect_ratio": "1:1"
    }

def post_to_instagram_revitalize(caption, image_url=None):
    """Post to Revitalize Instagram via Composio"""
    print("\n[COMPOSIO] Posting to Revitalize Instagram...")
    print(f"Caption preview: {caption[:50]}...")

    orch_config = load_configs()[1]
    ig_user_id = orch_config["composio"]["revitalize"]["ig_user_id"]
    account_alias = "revitalize_thrive_now_real"  # Fixed 2026-07-27: old alias pointed at Reclaim's account

    print(f"  IG User ID: {ig_user_id}")
    print(f"  Account Alias: {account_alias}")

    # This would call COMPOSIO_MULTI_EXECUTE_TOOL with:
    # 1. INSTAGRAM_POST_IG_USER_MEDIA (create container)
    # 2. INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH (publish)

    return {
        "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "ig_user_id": ig_user_id,
        "account": account_alias,
        "caption": caption,
        "image_url": image_url
    }

def post_to_facebook_revitalize(caption, image_url=None):
    """Post to Revitalize Facebook via Composio"""
    print("\n[COMPOSIO] Posting to Revitalize Facebook...")
    print(f"Caption preview: {caption[:50]}...")

    orch_config = load_configs()[1]
    fb_page_id = orch_config["composio"]["revitalize"]["fb_page_id"]

    print(f"  FB Page ID: {fb_page_id}")

    # This would call COMPOSIO_MULTI_EXECUTE_TOOL with:
    # FACEBOOK_CREATE_PHOTO_POST

    return {
        "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "fb_page_id": fb_page_id,
        "caption": caption,
        "image_url": image_url
    }

def post_to_instagram_reclaim(caption, image_url=None):
    """Post to Reclaim Instagram via Composio"""
    print("\n[COMPOSIO] Posting to Reclaim Instagram...")
    print(f"Caption preview: {caption[:50]}...")

    orch_config = load_configs()[1]
    ig_user_id = orch_config["composio"]["reclaim"]["ig_user_id"]

    print(f"  IG User ID: {ig_user_id}")

    return {
        "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "ig_user_id": ig_user_id,
        "caption": caption,
        "image_url": image_url
    }

def get_3pm_content():
    """Get 3 PM content schedule"""
    brand_cfg, orch_cfg = load_configs()

    revitalize_rotation = orch_cfg["revitalize_rotation"]["thursday"]
    reclaim_rotation = orch_cfg["reclaim_rotation"]["thursday"]

    rev_product_name = revitalize_rotation["slot_products"]["afternoon"]
    rec_product_name = reclaim_rotation["slot_products"]["afternoon"]

    # Get product details
    rev_product = next(p for p in brand_cfg["revitalize"]["products"] if p["name"] == rev_product_name)
    rec_product = next(p for p in brand_cfg["reclaim"]["products"] if p["name"] == rec_product_name)

    revitalize_caption = (
        "That 3 PM crash. 🫠\n\n"
        "Brain fog. Energy tank on empty. Your stress isn't a personality flaw—it's a biology problem. And it's solvable.\n\n"
        f"The Stress Management Workbook gives you the exact framework to reset your nervous system, even in the middle of a chaotic day. Thousands of women have used this to get their energy back.\n\n"
        f"{rev_product['price_short']}. No fluff. Just science + strategy.\n\n"
        f"Get the Stress Management Workbook → {rev_product['url']}\n\n"
        "#MidlifeWellness #StressManagement #MindsetReset #WomenOver45 #YouDeserveThis"
    )

    reclaim_caption = (
        "3 PM slump. Brain doesn't work like it used to. 🧠\n\n"
        "You built your career on execution. Now your mind feels sluggish. That's not weakness—it's cortisol and declining dopamine.\n\n"
        f"The Midlife Mindset Code isn't philosophy. It's neuroscience. 13 specific protocols to restore your mental sharpness by 4 PM every day.\n\n"
        f"{rec_product['price_short']}. Evidence-based. Built for high performers who don't have time for BS.\n\n"
        f"Access the Midlife Mindset Code → {rec_product['url']}\n\n"
        "#MenOver45 #MindsetCode #Performance #MidlifeMen #RecoverYourDrive"
    )

    return {
        "revitalize": {
            "product": rev_product_name,
            "price": rev_product["price_short"],
            "url": rev_product["url"],
            "caption": revitalize_caption,
            "theme": revitalize_rotation["theme"]
        },
        "reclaim": {
            "product": rec_product_name,
            "price": rec_product["price_short"],
            "url": rec_product["url"],
            "caption": reclaim_caption,
            "theme": reclaim_rotation["theme"]
        }
    }

def log_post(entry):
    """Add entry to orchestrator log"""
    log = []
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            try:
                log = json.load(f)
            except Exception:
                log = []

    log.append(entry)
    log = log[-90:]  # Keep last 90 entries

    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)

def main():
    print("="*60)
    print("EXECUTING 3 PM AFTERNOON POST")
    print("Thursday, July 9, 2026")
    print("="*60)

    content = get_3pm_content()

    print("\n[CONTENT]")
    print(f"REVITALIZE: {content['revitalize']['product']}")
    print(f"RECLAIM: {content['reclaim']['product']}")

    # Generate images
    rev_image_config = generate_revitalize_image()
    rec_image_config = generate_reclaim_image()

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Call Higgsfield generate_image for both brands")
    print("2. Wait for images to complete")
    print("3. Post to Instagram via Composio (with account alias)")
    print("4. Post to Facebook via Composio (Revitalize only)")
    print("5. Log results to orchestrator-log.json")
    print("="*60)

    print("\n[READY FOR MCP EXECUTION]")
    print("Revitalize Instagram ready")
    print("Revitalize Facebook ready")
    print("Reclaim Instagram ready")

    return {
        "content": content,
        "revitalize_image_config": rev_image_config,
        "reclaim_image_config": rec_image_config
    }

if __name__ == "__main__":
    result = main()
    print("\nScript prepared. Awaiting MCP tool execution...")
