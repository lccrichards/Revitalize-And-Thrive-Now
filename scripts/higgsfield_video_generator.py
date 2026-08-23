#!/usr/bin/env python3
"""
higgsfield_video_generator.py

Generates educational talking-head videos for Revitalize and Thrive Now + Reclaim and Rise.
Uses Higgsfield's native generate_video with two rotating styles:

1. FACELESS EXPLAINER — Educational narrated explainer (voiceover + graphics)
   - For explaining the core benefit or mechanism
   - Professional, focused on the value story
   - No on-camera talent needed

2. UGC TALKING-HEAD — Creator review video (real person on camera)
   - For peer-to-peer product review and demonstration
   - More authentic, relatable energy
   - Matches Reclaim's direct voice; adds warmth to Revitalize

USAGE:
  Called from video-reel triggers (Tue/Thu) when posting to Instagram Reels + YouTube.
  Alternates style per day or rotation setting.

WORKFLOW:
  1. Determine style (faceless vs ugc) based on day or rotation counter
  2. Load product from daily rotation (orchestrator-config.json)
  3. Generate educational script (hook + core claim + result)
  4. Call mcp__higgsfield__generate_video with appropriate workflow
  5. Poll job_display until completion
  6. Return video_id and hosted URL for logging

CLAUDE INTEGRATION:
  This script is NOT run locally; it guides Claude when a trigger fires.
  Claude reads this file, then:
    a) Reads orchestrator-config.json for today's product
    b) Generates the educational script inline (matching the angle and style)
    c) Calls mcp__higgsfield__generate_video with:
       - workflow: "faceless-channel-video" or "ugc-flow"
       - product: product_name, price, url from config
       - duration: 30 seconds (standard reel length)
       - style rotation: alternate Tue=faceless, Thu=ugc
    d) Polls mcp__higgsfield__job_display until status = completed
    e) Extracts hosted URL and video_id from result
    f) Logs to data/orchestrator-log.json
"""

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"


def get_day_name() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%A").lower()


def get_video_style(day_name: str, brand: str) -> str:
    """
    Determine video style for today's reel.
    Alternates Tuesday (faceless) and Thursday (ugc).
    """
    if day_name == "tuesday":
        return "faceless-channel-video"
    elif day_name == "thursday":
        return "ugc-flow"
    else:
        # Fallback: alternate based on weekday number
        return "faceless-channel-video" if int(datetime.now(ZoneInfo("America/New_York")).weekday()) % 2 == 1 else "ugc-flow"


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


def generate_faceless_script(product: dict, brand: str, angle_key: str) -> str:
    """
    Generate faceless explainer script (voiceover + graphics).
    Hook → Core Mechanism → Result/Benefit.
    """
    product_name = product.get("name", "Product")
    price = product.get("price_short", "Price")
    url = product.get("url", "")

    # Educational angle for faceless (mechanism-focused)
    if brand == "revitalize":
        script = f"""
[HOOK - First 5 seconds]
"Struggling with sleep? Here's why most solutions fail."

[MECHANISM - Middle 20 seconds]
"The Midlife Sleep Fix isn't about forcing yourself to bed. It's about understanding how your body's natural rhythms change after 45 — hormones, cortisol timing, temperature regulation. We built this guide on the exact mechanisms your sleep depends on."

[RESULT - Last 5 seconds]
"{product_name} — {price}. Learn the science, reclaim your sleep. Link in bio."
"""
    else:  # reclaim
        script = f"""
[HOOK - First 5 seconds]
"Your testosterone and energy don't have to decline at 50."

[MECHANISM - Middle 20 seconds]
"The Reclaim Masterclass cuts through the noise. Real neuroscience on cortisol, real data on testosterone optimization, real protocol on sleep recovery. No supplements, no hype — just the mechanisms your body actually responds to."

[RESULT - Last 5 seconds]
"{product_name} — {price}. Your edge is waiting. Link in bio."
"""

    return script.strip()


def generate_ugc_script(product: dict, brand: str, angle_key: str) -> str:
    """
    Generate UGC talking-head script (creator on camera).
    Hook → Problem/Use Case → Proof → CTA.
    """
    product_name = product.get("name", "Product")
    price = product.get("price_short", "Price")

    # Peer-to-peer angle for UGC (personal experience)
    if brand == "revitalize":
        script = f"""
[HOOK - 0-3 sec]
"I was skeptical about another sleep 'fix.'"

[PROBLEM - 3-10 sec]
"But at 50, my sleep was broken. Not just tired — my whole energy day was off. Brain fog, afternoon crashes, that 2 AM wake-up every single night."

[PROOF - 10-20 sec]
"I went through the {product_name}. The part that changed everything? Understanding why my body was fighting me, not against me. It's like finally reading the manual."

[CTA - 20-30 sec]
"If your sleep is costing you your day, you need to see this. {product_name} — {price}. Link in bio. You deserve this."
"""
    else:  # reclaim
        script = f"""
[HOOK - 0-3 sec]
"At 48, I realized I wasn't the same performer I used to be."

[PROBLEM - 3-10 sec]
"Energy dropped off. Strength wasn't there. And I thought that was just... getting older."

[PROOF - 10-20 sec]
"The {product_name} showed me it's not age — it's the mechanics. Once I understood the real drivers (cortisol, sleep quality, protein timing), everything clicked back."

[CTA - 20-30 sec]
"If you're feeling your edge slip, this is the reset. {product_name} — {price}. Your drive is in there. Link in bio."
"""

    return script.strip()


def generate_video_script(product: dict, brand: str, style: str, angle_key: str) -> str:
    """Generate the appropriate script based on video style."""
    if style == "faceless-channel-video":
        return generate_faceless_script(product, brand, angle_key)
    elif style == "ugc-flow":
        return generate_ugc_script(product, brand, angle_key)
    else:
        return ""


def build_video_prompt(
    product: dict,
    brand: str,
    style: str,
    script: str,
    angle_key: str
) -> str:
    """
    Build the Higgsfield prompt for generate_video.
    Includes product details, emotional angle, and video style.
    """
    product_name = product.get("name", "Product")
    price = product.get("price_short", "Price")
    url = product.get("url", "")

    if style == "faceless-channel-video":
        prompt = f"""
Educational explainer video: 30 seconds, {brand.title()} brand voice.

Product: {product_name} ({price})
URL: {url}

Script (voiceover narration):
{script}

Style: Professional educational narration + supporting graphics/visuals that illustrate the mechanism or benefit being explained. No on-camera talent. Warm, trustworthy, authoritative tone. Use visual metaphors for internal body processes (sleep cycles, cortisol, energy patterns).

Visual Concept: Clean, professional health/wellness aesthetic. Subtle animations showing the product benefit or the mechanism explained. Use typography that feels premium and trustworthy, not clinical.

Duration: 30 seconds exactly.
Aspect ratio: 9:16 (vertical reel format)
Resolution: 1080p
"""
    elif style == "ugc-flow":
        prompt = f"""
Creator talking-head product review video: 30 seconds, {brand.title()} brand voice.

Product: {product_name} ({price})
URL: {url}

Creator: Professional woman (Revitalize) or man (Reclaim), aged 45-55, confident, relatable energy. Direct eye contact. Natural setting (home, office, outdoor).

Script (on-camera dialogue):
{script}

Tone: Peer-to-peer, authentic, no sales energy. This creator genuinely uses this product and is sharing real experience. Conversational, direct, warm.

Visual Style: Real person on camera speaking directly. Product shown briefly in hand or on desk. Natural lighting, relatable environment. True creator energy, not polished/staged.

Duration: 30 seconds exactly.
Aspect ratio: 9:16 (vertical reel format)
Resolution: 1080p
"""
    else:
        prompt = ""

    return prompt.strip()


# When Claude calls this from the trigger:
# 1. Read orchestrator-config.json to get today's product for each brand
# 2. Read content-strategy.json to get today's emotional angle
# 3. Determine video style (faceless vs ugc based on day)
# 4. Generate script for each brand
# 5. Call mcp__higgsfield__generate_video with the prompt
# 6. Poll mcp__higgsfield__job_display until done
# 7. Log results to data/orchestrator-log.json with video URLs
