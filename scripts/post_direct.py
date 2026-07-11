#!/usr/bin/env python3
"""
post_direct.py
Generate AI content and post directly to Instagram and Facebook via Composio.
No Meta tokens. No GitHub. No Publer. No Buffer.

Requirements:
  pip install anthropic requests

Two API keys to set:
  export ANTHROPIC_API_KEY=sk-ant-...
  export COMPOSIO_API_KEY=your_composio_key    # app.composio.dev > Settings > API Keys
  export PEXELS_API_KEY=your_pexels_key        # optional, free at pexels.com/api

Your Composio connections (already active — do not change):
  Revitalize Instagram  : revitalize_thrive_now_business  (IG 27164026169935796)
  Reclaim    Instagram  : reclaim_and_rise_now             (IG 27634679816148097)
  Revitalize Facebook   : revitalize_thrive_now_business

Usage:
  # Post 1 post to Instagram right now
  python scripts/post_direct.py --brand revitalize --platform ig

  # Post to both platforms (Revitalize)
  python scripts/post_direct.py --brand revitalize --platform both

  # Post for Reclaim brand (Instagram only — Facebook connection added later)
  python scripts/post_direct.py --brand reclaim --platform ig

  # Theme or product focus
  python scripts/post_direct.py --brand revitalize --theme "hormone balance" --count 5
  python scripts/post_direct.py --brand reclaim --product "masterclass" --count 3

  # Generate content only — save to JSON, no posting
  python scripts/post_direct.py --brand revitalize --count 7 --generate-only

  # Dry run — full preview, no API calls
  python scripts/post_direct.py --brand revitalize --count 3 --dry-run
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    import anthropic
except ImportError:
    sys.exit("ERROR: Run:  pip install anthropic requests")

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"

ANTHROPIC_MODEL = "claude-sonnet-4-6"
PEXELS_API = "https://api.pexels.com/v1/search"
COMPOSIO_API = "https://backend.composio.dev/api/v1/actions"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
POST_FORMATS = ["reel", "feed", "feed", "reel", "feed", "reel", "feed"]
POST_TIMES = ["7:00 AM", "8:00 AM", "9:00 AM", "7:00 AM", "8:00 AM", "7:00 AM", "10:00 AM"]
TIME_TO_HM = {
    "7:00 AM": (7, 0), "8:00 AM": (8, 0), "9:00 AM": (9, 0),
    "10:00 AM": (10, 0), "11:00 AM": (11, 0), "12:00 PM": (12, 0),
}

# Fallback images when no Pexels key is set
BRAND_FALLBACK_IMAGE = {
    "revitalize": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "reclaim":    "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=1080",
}

# Composio entity IDs — already connected, no token setup needed
COMPOSIO_CONFIG = {
    "revitalize": {
        "ig_entity_id": "revitalize_thrive_now_business",
        "ig_user_id":   "27164026169935796",
        "fb_entity_id": "revitalize_thrive_now_business",
        "fb_page_id":   None,  # fetched automatically on first FB post
    },
    "reclaim": {
        "ig_entity_id": "reclaim_and_rise_now",
        "ig_user_id":   "27634679816148097",
        "fb_entity_id": None,  # Facebook connection — add later via Composio
        "fb_page_id":   None,
    },
}


# ── Config ────────────────────────────────────────────────────────────────────

def load_config(brand: str) -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"ERROR: brand config not found at {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        all_cfg = json.load(f)
    if brand not in all_cfg:
        sys.exit(f"ERROR: brand '{brand}' not found. Available: {list(all_cfg)}")
    return all_cfg[brand]


# ── Composio REST helper ──────────────────────────────────────────────────────

def composio_execute(api_key: str, action: str, entity_id: str, params: dict) -> dict:
    """Call a Composio action via the REST API — no SDK required."""
    resp = requests.post(
        f"{COMPOSIO_API}/{action}/execute",
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json={"entityId": entity_id, "input": params},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Composio {action} error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


# ── Image fetching ────────────────────────────────────────────────────────────

def fetch_pexels_image(query: str, pexels_key: str) -> str:
    try:
        resp = requests.get(
            PEXELS_API,
            headers={"Authorization": pexels_key},
            params={"query": query, "per_page": 5, "orientation": "square"},
            timeout=10,
        )
        if resp.ok:
            photos = resp.json().get("photos", [])
            if photos:
                return photos[0]["src"]["large"]
    except Exception as e:
        print(f"  Pexels fetch failed: {e}")
    return ""


def resolve_image(post: dict, brand: str, pexels_key: str) -> str:
    if post.get("image_url"):
        return post["image_url"]
    if pexels_key and post.get("image_suggestion"):
        url = fetch_pexels_image(post["image_suggestion"], pexels_key)
        if url:
            return url
    return BRAND_FALLBACK_IMAGE.get(brand, "")


# ── Content generation ────────────────────────────────────────────────────────

def build_system_prompt(cfg: dict) -> str:
    products_text = "\n".join(
        f"  * {p['name']} -- {p['price_short']}  |  URL: {p['url']}  |  CTA: \"{p['cta']}\""
        for p in cfg["products"]
    )
    core_tags = " ".join(cfg["hashtag_pools"]["core"][:12])
    themes = ", ".join(cfg["content_themes"][:6])
    return f"""You are a social media content strategist for {cfg['name']}.

BRAND: {cfg['name']}
TAGLINE: {cfg['tagline']}
AUDIENCE: {cfg['audience']}

VOICE:
{cfg['voice']}

PRODUCTS AND CTAs (use exactly as shown):
{products_text}

HASHTAGS -- use 12 to 15 per post, mixing core + theme-specific:
Core: {core_tags}

THEMES: {themes}

RULES:
1. Speak to a real specific pain point. Never generic.
2. End with CTA: product name, price, full URL on its own line.
3. Short punchy lines with line breaks -- never dense paragraphs.
4. 1 to 3 emojis maximum.
5. Reel: strong hook line 1, then value, then CTA. Max 150 words.
6. Feed: story or list format, then CTA. Max 200 words.
7. Hashtags after two blank lines at the very end.

OUTPUT: Valid JSON only -- no code fences, no extra text:
{{"title":"Post title 5-8 words","caption":"Full caption with CTA and URL","hashtags":"#Tag1 #Tag2 ...","post_format":"reel or feed","image_suggestion":"One sentence describing ideal visual"}}"""


def build_user_prompt(cfg: dict, theme: str, product_filter: str, idx: int) -> str:
    if product_filter:
        product = next(
            (p for p in cfg["products"] if product_filter.lower() in p["name"].lower()),
            None,
        )
        if not product:
            print(f"  WARNING: no product matched '{product_filter}', using rotation.")
            product = cfg["products"][idx % len(cfg["products"])]
    else:
        product = cfg["products"][idx % len(cfg["products"])]

    theme_line = f"Theme: {theme}" if theme else \
        f"Theme: {cfg['content_themes'][(idx - 1) % len(cfg['content_themes'])]}"

    return (
        f"Generate post #{idx} for {cfg['name']}.\n"
        f"{theme_line}\n"
        f"Product: {product['name']} -- {product['price_short']} -- {product['url']}\n"
        f"Format: {POST_FORMATS[(idx - 1) % len(POST_FORMATS)]}\n\n"
        "Real, specific, urgent. Every word earns its place."
    )


def generate_post(client, cfg: dict, theme: str, product_filter: str, idx: int) -> dict:
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=build_system_prompt(cfg),
        messages=[{"role": "user", "content": build_user_prompt(cfg, theme, product_filter, idx)}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1][4:].strip() if len(parts) > 1 and parts[1].startswith("json") else parts[1].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"\n  WARNING: JSON parse failed for post {idx}. Raw:\n{raw[:300]}")
        return None
    return {
        "day": idx,
        "day_of_week": DAY_ORDER[(idx - 1) % 7],
        "post_time": POST_TIMES[(idx - 1) % len(POST_TIMES)],
        "post_format": data.get("post_format", POST_FORMATS[(idx - 1) % len(POST_FORMATS)]),
        "title": data.get("title", f"Post {idx}"),
        "caption": data.get("caption", ""),
        "hashtags": data.get("hashtags", ""),
        "image_url": "",
        "image_suggestion": data.get("image_suggestion", ""),
    }


# ── Composio — Instagram ──────────────────────────────────────────────────────

def post_instagram(
    composio_key: str,
    entity_id: str,
    ig_user_id: str,
    caption: str,
    image_url: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        print(f"    [DRY RUN] Instagram ({entity_id})")
        print(f"    Caption preview: {caption[:100]}...")
        return True

    if not image_url:
        print("    SKIP — Instagram requires an image URL.")
        print("    Set PEXELS_API_KEY for auto image fetching.")
        return False

    # Step 1 — Create media container
    try:
        result = composio_execute(
            composio_key,
            "INSTAGRAM_POST_IG_USER_MEDIA",
            entity_id,
            {"ig_user_id": ig_user_id, "image_url": image_url, "caption": caption},
        )
    except RuntimeError as e:
        print(f"    {e}")
        return False

    data = result.get("data") or result
    container_id = data.get("id") or data.get("creation_id")
    if not container_id:
        print(f"    IG error: no container ID in response: {str(result)[:200]}")
        return False

    time.sleep(3)

    # Step 2 — Publish immediately
    try:
        result2 = composio_execute(
            composio_key,
            "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
            entity_id,
            {"ig_user_id": ig_user_id, "creation_id": container_id},
        )
    except RuntimeError as e:
        print(f"    {e}")
        return False

    data2 = result2.get("data") or result2
    post_id = data2.get("id", "unknown")
    print(f"    Posted — ID: {post_id}")
    return True


# ── Composio — Facebook ───────────────────────────────────────────────────────

_fb_page_id_cache: dict[str, str] = {}

def get_facebook_page_id(composio_key: str, entity_id: str) -> str:
    if entity_id in _fb_page_id_cache:
        return _fb_page_id_cache[entity_id]
    try:
        result = composio_execute(
            composio_key,
            "FACEBOOK_LIST_MANAGED_PAGES",
            entity_id,
            {},
        )
        data = result.get("data") or result
        pages = data.get("data", [])
        if pages:
            page_id = pages[0].get("id", "")
            page_name = pages[0].get("name", "")
            print(f"    Facebook Page: {page_name} (ID: {page_id})")
            _fb_page_id_cache[entity_id] = page_id
            return page_id
    except RuntimeError as e:
        print(f"    Could not fetch Facebook page ID: {e}")
    return ""


def post_facebook(
    composio_key: str,
    entity_id: str,
    page_id: str,
    message: str,
    image_url: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        print(f"    [DRY RUN] Facebook ({entity_id or 'NOT CONNECTED'})")
        print(f"    Caption preview: {message[:100]}...")
        return True

    if not entity_id:
        print("    SKIP — no Facebook Composio connection for this brand yet.")
        return False

    if not page_id:
        page_id = get_facebook_page_id(composio_key, entity_id)
        if not page_id:
            print("    SKIP — could not determine Facebook Page ID.")
            return False

    params = {"page_id": page_id, "message": message}
    if image_url:
        params["url"] = image_url

    try:
        result = composio_execute(
            composio_key,
            "FACEBOOK_CREATE_PHOTO_POST",
            entity_id,
            params,
        )
    except RuntimeError as e:
        print(f"    {e}")
        return False

    data = result.get("data") or result
    post_id = data.get("id", "unknown")
    print(f"    Posted — ID: {post_id}")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI content and post to Instagram / Facebook via Composio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--brand", required=True, choices=["revitalize", "reclaim"],
        help="revitalize = Revitalize and Thrive Now (women)  |  reclaim = Reclaim and Rise (men)",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of posts to generate and send (default: 1)",
    )
    parser.add_argument(
        "--platform", default="ig", choices=["ig", "fb", "both"],
        help="ig=Instagram  fb=Facebook  both=both  (default: ig)",
    )
    parser.add_argument("--theme", help="Content theme, e.g. 'hormone balance', 'sleep', 'mindset'")
    parser.add_argument("--product", help="Product to feature, partial name e.g. 'sleep', 'masterclass'")
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Generate content and save to JSON — do not post",
    )
    parser.add_argument(
        "--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Anthropic API key (or set ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--composio-key", default=os.environ.get("COMPOSIO_API_KEY", ""),
        help="Composio API key — get from app.composio.dev > Settings > API Keys",
    )
    parser.add_argument(
        "--pexels-key", default=os.environ.get("PEXELS_API_KEY", ""),
        help="Pexels API key for auto image fetching (optional)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview everything without calling any API",
    )
    args = parser.parse_args()

    # Validate
    if not args.anthropic_key and not args.dry_run:
        sys.exit("ERROR: ANTHROPIC_API_KEY required (or pass --anthropic-key)")
    if not args.composio_key and not args.generate_only and not args.dry_run:
        sys.exit(
            "ERROR: COMPOSIO_API_KEY required (or pass --composio-key)\n"
            "Get yours at: app.composio.dev > Settings > API Keys"
        )

    cfg = load_config(args.brand)
    cmp = COMPOSIO_CONFIG[args.brand]

    client = anthropic.Anthropic(api_key=args.anthropic_key) if not args.dry_run else None

    # Header
    mode = "DRY RUN" if args.dry_run else ("GENERATE ONLY" if args.generate_only else "POSTING")
    print(f"\n[{mode}]  {cfg['name'].upper()}")
    print(f"Platform : {args.platform.upper()}")
    print(f"Posts    : {args.count}")
    print(f"Via      : Composio (no Meta tokens needed)")
    if args.theme:
        print(f"Theme    : {args.theme}")
    if args.product:
        print(f"Product  : {args.product}")
    print("-" * 60)

    posts = []
    ig_ok = fb_ok = ig_fail = fb_fail = 0

    for i in range(1, args.count + 1):
        print(f"\nPost {i}/{args.count} — generating...", end=" ", flush=True)

        if args.dry_run:
            post = {
                "day": i,
                "day_of_week": DAY_ORDER[(i - 1) % 7],
                "post_time": POST_TIMES[(i - 1) % len(POST_TIMES)],
                "post_format": POST_FORMATS[(i - 1) % len(POST_FORMATS)],
                "title": f"[DRY RUN] Post {i}",
                "caption": "Dry run — no API called.",
                "hashtags": "#DryRun",
                "image_url": BRAND_FALLBACK_IMAGE.get(args.brand, ""),
                "image_suggestion": "Dry run placeholder",
            }
        else:
            post = generate_post(client, cfg, args.theme or "", args.product or "", i)
            if not post:
                print("FAILED — skipping")
                continue

        posts.append(post)
        print(f"OK — {post['title'][:55]}")

        if args.generate_only:
            continue

        caption = post["caption"]
        if post.get("hashtags"):
            caption += "\n\n" + post["hashtags"]

        image_url = resolve_image(post, args.brand, args.pexels_key)

        if args.platform in ("ig", "both"):
            print(f"  → Instagram")
            ok = post_instagram(
                args.composio_key, cmp["ig_entity_id"], cmp["ig_user_id"],
                caption, image_url, args.dry_run,
            )
            ig_ok += ok; ig_fail += not ok

        if args.platform in ("fb", "both"):
            print(f"  → Facebook")
            ok = post_facebook(
                args.composio_key, cmp.get("fb_entity_id") or "",
                cmp.get("fb_page_id") or "", caption, image_url, args.dry_run,
            )
            fb_ok += ok; fb_fail += not ok

        if i < args.count and not args.dry_run:
            time.sleep(2)

    # Save JSON output
    json_path = DATA_DIR / f"bot-posts-{args.brand}.json"
    with open(json_path, "w") as f:
        json.dump(posts, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print(f"Generated : {len(posts)} posts  →  {json_path.name}")
    if not args.generate_only and not args.dry_run:
        if args.platform in ("ig", "both"):
            print(f"Instagram : {ig_ok} OK  /  {ig_fail} failed")
        if args.platform in ("fb", "both"):
            print(f"Facebook  : {fb_ok} OK  /  {fb_fail} failed")
    print("Done.")


if __name__ == "__main__":
    main()
