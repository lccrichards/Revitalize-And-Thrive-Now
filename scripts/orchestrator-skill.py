#!/usr/bin/env python3
"""
Orchestrator Post Skill

Automated content generation and publishing for Revitalize & Thrive Now
and Reclaim & Rise across Instagram, Facebook, and YouTube.

Usage:
  orchestrator-skill --slot=morning --brand=both --dry_run=false
  orchestrator-skill --slot=afternoon --brand=revitalize --date=2026-08-14
  orchestrator-skill --slot=evening --brand=reclaim --dry_run=true
"""

import json
import sys
import argparse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, Dict, Tuple

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"

# Compliance gate keywords (forbidden)
FORBIDDEN_KEYWORDS = {
    "fix", "cure", "heal", "reverse", "fixed", "cured", "healing",
    "guarantee", "guaranteed", "proven", "proof", "medically proven",
    "weight loss", "lost pounds", "lost lbs", "lose weight",
    "boost testosterone", "balance hormones", "medical condition",
    "blood pressure", "off medication", "discontinue", "diagnosis",
    "before and after", "before/after", "transformation",
}

class OrchestratorPost:
    """Orchestrator posting workflow executor"""

    def __init__(self, slot: str, brand: str, date: Optional[str] = None, dry_run: bool = False):
        self.slot = slot
        self.brands = [brand] if brand != "both" else ["revitalize", "reclaim"]
        self.date = self._parse_date(date)
        self.dry_run = dry_run
        self.day_name = self.date.strftime("%A").lower()
        self.et_date_str = self.date.strftime("%Y-%m-%d")

        self.brand_cfg = {}
        self.orch_cfg = {}
        self.results = {"revitalize": {}, "reclaim": {}}

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date string or use today (ET)."""
        et_tz = ZoneInfo("America/New_York")
        if not date_str:
            return datetime.now(et_tz)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.replace(tzinfo=et_tz)
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    def load_configs(self) -> bool:
        """Load config files."""
        try:
            with open(CONFIG_PATH) as f:
                self.brand_cfg = json.load(f)
            with open(ORCH_CONFIG_PATH) as f:
                self.orch_cfg = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Failed to load configs: {e}")
            return False

    def check_post_guard(self) -> bool:
        """Check if already posted today (POST GUARD)."""
        if not LOG_PATH.exists():
            return False

        try:
            with open(LOG_PATH) as f:
                log = json.load(f)
        except Exception:
            return False

        # Check for existing post this slot + day
        for entry in log:
            if entry.get("date", "").startswith(self.et_date_str):
                # Slot is at top level, not nested per brand
                if entry.get("slot") == self.slot:
                    print(f"⚠️  POST GUARD: Already posted {self.slot} slot on {self.et_date_str}")
                    print(f"   Skipping to prevent duplicates.")
                    return True
        return False

    def get_product(self, brand: str) -> Dict:
        """Get product for this brand/slot/day."""
        try:
            rotation = self.orch_cfg[f"{brand}_rotation"][self.day_name]
            product_name = rotation["slot_products"][self.slot]
            theme = rotation["theme"]

            for p in self.brand_cfg[brand]["products"]:
                if p["name"] == product_name:
                    return {"product": p, "theme": theme}

            print(f"❌ Product not found: {product_name}")
            return {}
        except (KeyError, IndexError) as e:
            print(f"❌ Failed to get product for {brand}/{self.day_name}/{self.slot}: {e}")
            return {}

    def get_slot_info(self) -> Dict:
        """Get slot tone, angle, hook style."""
        try:
            return self.orch_cfg["schedule"][self.slot]
        except KeyError:
            print(f"❌ Invalid slot: {self.slot}")
            return {}

    def generate_caption(self, brand: str, product: Dict, slot_info: Dict) -> str:
        """Generate on-brand caption (template — Claude fills in actual)."""
        if not product or not slot_info:
            return ""

        p = product["product"]
        theme = product["theme"]
        tone = slot_info.get("tone", "")
        hook = slot_info.get("hook_style", "")

        # Template for Claude to fill in
        template = f"""
Generate a compelling Instagram caption for {brand.capitalize()} brand:
- Product: {p['name']}
- Price: {p['price_short']}
- URL: {p['url']}
- Theme: {theme}
- Slot tone: {tone}
- Hook style: {hook}
- Brand voice: {self.brand_cfg[brand]['voice']}

Requirements:
✓ 2-3 short paragraphs, punchy lines
✓ Include product name, price, URL on separate lines
✓ Clear call to action
✓ 5-7 relevant hashtags
✗ NO medical claims, health diagnoses, weight-loss promises
✗ NO fabricated statistics or testimonials
✗ NO "fix/cure/heal/reverse/guarantee/proven"
✗ NO before/after body claims

Respond with caption only (no markdown, no explanation).
"""
        return template

    def validate_caption(self, caption: str) -> Tuple[bool, Optional[str]]:
        """Check caption against compliance gates."""
        caption_lower = caption.lower()

        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in caption_lower:
                return False, f"Forbidden keyword found: '{keyword}'"

        # Check for weight numbers
        if any(x in caption for x in ["lbs", "pounds", "kg", "lost ", "weight"]):
            if any(str(i) in caption for i in range(10)):
                return False, "Weight loss numbers detected"

        return True, None

    def generate_higgsfield_prompt(self, brand: str, slot_info: Dict, theme: str) -> Dict:
        """Build Higgsfield image generation prompt."""
        template = self.orch_cfg["higgsfield"][f"{brand}_image_prompt_template"]
        mood = self.orch_cfg["higgsfield"]["moods"].get(self.slot, "")
        settings_dict = self.orch_cfg["higgsfield"][f"{brand}_settings"]
        setting = settings_dict.get(theme, "wellness lifestyle")

        prompt = template.format(mood=mood, setting=setting)

        return {
            "model": "nano_banana_pro",
            "prompt": prompt,
            "aspect_ratio": "1:1"
        }

    def post_to_platform(self, brand: str, caption: str, image_url: Optional[str] = None) -> Dict:
        """Prepare platform posting (actual MCP calls happen in Claude execution)."""
        platforms = self.orch_cfg["composio"][brand]["platforms"]
        results = {}

        for platform in platforms:
            if platform == "instagram":
                results["instagram"] = {
                    "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
                    "actions": [
                        "INSTAGRAM_POST_IG_USER_MEDIA",
                        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH"
                    ],
                    "ig_user_id": self.orch_cfg["composio"][brand]["ig_user_id"],
                    "caption": caption,
                    "image_url": image_url
                }
            elif platform == "facebook" and brand == "revitalize":
                results["facebook"] = {
                    "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
                    "action": "FACEBOOK_CREATE_PHOTO_POST",
                    "fb_page_id": self.orch_cfg["composio"][brand]["fb_page_id"],
                    "caption": caption,
                    "image_url": image_url
                }
            elif platform == "youtube":
                results["youtube"] = {
                    "tool": "YouTube API",
                    "action": "Upload video",
                    "yt_channel_id": self.orch_cfg["composio"][brand]["yt_channel_id"],
                    "caption": caption,
                    "image_url": image_url,
                    "duration": 30
                }

        return results

    def log_result(self, entry: Dict):
        """Append result to orchestrator log."""
        log = []
        if LOG_PATH.exists():
            try:
                with open(LOG_PATH) as f:
                    log = json.load(f)
            except Exception:
                log = []

        log.append(entry)
        log = log[-90:]  # Keep last 90 entries

        try:
            with open(LOG_PATH, "w") as f:
                json.dump(log, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Failed to log result: {e}")
            return False

    def run(self) -> bool:
        """Execute the orchestrator workflow."""
        print("=" * 60)
        print("ORCHESTRATOR POST SKILL")
        print("=" * 60)
        print(f"Slot: {self.slot} | Date: {self.et_date_str} | Brands: {', '.join(self.brands)}")
        if self.dry_run:
            print("MODE: DRY RUN (preview only)")
        print()

        # Load configs
        if not self.load_configs():
            return False

        # Check POST GUARD
        if self.check_post_guard():
            return False

        # Process each brand
        all_valid = True
        entry = {
            "date": f"{self.et_date_str} ({self.day_name.capitalize()} ET)",
            "slot": self.slot,
            "timestamp": datetime.now(ZoneInfo("America/New_York")).isoformat(),
            "executed_by": "manual trigger" if not self.dry_run else "dry_run"
        }

        slot_info = self.get_slot_info()
        if not slot_info:
            return False

        for brand in self.brands:
            print(f"\n[{brand.upper()}]")

            # Get product
            product_info = self.get_product(brand)
            if not product_info:
                all_valid = False
                continue

            product = product_info["product"]
            theme = product_info["theme"]

            print(f"  Product: {product['name']}")
            print(f"  Price: {product['price_short']}")
            print(f"  Theme: {theme}")

            # Generate caption (template)
            caption_template = self.generate_caption(brand, product_info, slot_info)
            print(f"  Caption template ready for Claude generation")

            # Prepare Higgsfield prompt
            hf_prompt = self.generate_higgsfield_prompt(brand, slot_info, theme)
            print(f"  Higgsfield prompt ready")

            # Validate (once caption is generated)
            # In real execution, Claude will generate the actual caption and validate
            print(f"  ✓ Ready for compliance check")

            # Prepare platform posts
            platforms_ready = self.post_to_platform(brand, "[caption from Claude]", "[image from Higgsfield]")
            print(f"  Platforms: {', '.join(platforms_ready.keys())}")

            # Store in entry
            entry[brand] = {
                "product": product["name"],
                "price": product["price_short"],
                "url": product["url"],
                "theme": theme,
                "angle": slot_info.get("angle", ""),
                "hook_style": slot_info.get("hook_style", ""),
                "status": "ready_for_execution"
            }

        if not all_valid:
            print("\n❌ Some brands failed. Aborting.")
            return False

        # Log if not dry run
        if not self.dry_run:
            entry["approval_given_at"] = datetime.now(ZoneInfo("America/New_York")).isoformat()
            self.log_result(entry)

        print("\n" + "=" * 60)
        print("✅ ORCHESTRATOR POST PREPARED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Claude will generate captions (using brand voice + product details)")
        print("2. Claude will call Higgsfield to generate images")
        print("3. Claude will post via Composio to Instagram/Facebook/YouTube")
        print("4. Results logged to orchestrator-log.json")
        if self.dry_run:
            print("\n[DRY RUN] — No actual posts created.")

        return True


def main():
    parser = argparse.ArgumentParser(description="Orchestrator Post Skill")
    parser.add_argument("--slot", choices=["morning", "afternoon", "evening", "night"], required=True,
                        help="Post time slot")
    parser.add_argument("--brand", choices=["revitalize", "reclaim", "both"], default="both",
                        help="Brand(s) to post")
    parser.add_argument("--date", help="Date (YYYY-MM-DD, default: today ET)")
    parser.add_argument("--dry_run", action="store_true", help="Preview without posting")

    args = parser.parse_args()

    orchestrator = OrchestratorPost(
        slot=args.slot,
        brand=args.brand,
        date=args.date,
        dry_run=args.dry_run
    )

    success = orchestrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
