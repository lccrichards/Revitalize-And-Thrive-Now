#!/usr/bin/env python3
"""
post_direct.py
Generate AI content and post directly to Instagram and Facebook via Composio.
No Meta tokens. No GitHub. No Publer. No Buffer.

Requirements:
  pip install anthropic composio-core

Composio is already connected to both Instagram accounts and the Facebook page.
You only need two API keys:

  export ANTHROPIC_API_KEY=sk-ant-...
  export COMPOSIO_API_KEY=your_composio_key   (get from app.composio.dev > Settings > API Keys)
  export PEXELS_API_KEY=your_pexels_key       (optional — free at pexels.com/api)

Usage:
  # Post 1 post to Instagram right now
  python scripts/post_direct.py --brand revitalize --platform ig

  # Schedule 7 posts to Instagram starting next Monday
  python scripts/post_direct.py --brand revitalize --count 7 --start-date 2026-07-07 --platform ig

  # Post to both Instagram and Facebook
  python scripts/post_direct.py --brand revitalize --platform both

  # Focus on a specific theme
  python scripts/post_direct.py --brand revitalize --theme "hormone balance" --count 5 --platform ig

  # Push one product across all posts
  python scripts/post_direct.py --brand reclaim --product "masterclass" --count 10 --platform both

  # Generate content only — save to JSON, do not post
  python scripts/post_direct.py --brand revitalize --count 7 --generate-only

  # Dry run — preview everything without any API calls
  python scripts/post_direct.py --brand revitalize --count 3 --dry-run

Composio entity IDs (already configured — do not change):
  revitalize Instagram  : revitalize_thrive_now_business  (IG user ID 27164026169935796)
  reclaim    Instagram  : reclaim_and_rise_now             (IG user ID 27634679816148097)
  revitalize Facebook   : revitalize_thrive_now_business
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
    sys.exit("ERROR: Run:  pip install anthropic composio-core")

try:
    from composio import ComposioToolSet, Action
except ImportError:
    sys.exit("ERROR: Run:  pip install composio-core")

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"

ANTHROPIC_MODEL = "claude-sonnet-4-6"
PEXELS_API = "https://api.pexels.com/v1/search"

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

# Composio entity IDs and platform IDs — already connected, no tokens needed
COMPOSIO_CONFIG = {
    "revitalize": {
        "ig_entity_id": "revitalize_thrive_now_business",
        "ig_user_id":   "27164026169935796",
        "fb_entity_id": "revitalize_thrive_now_business",
        "fb_page_id":   None,  # fetched automatically via list_managed_pages
    },
    "reclaim": {
        "ig_entity_id": "reclaim_and_rise_now",
        "ig_user_id":   "27634679816148097",
        "fb_entity_id": None,  # no Facebook connection for Reclaim — add via Composio if needed
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

def post_instagram_composio(
    toolset: "ComposioToolSet",
    entity_id: str,
    ig_user_id: str,
    caption: str,
    image_url: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        print(f"    [DRY RUN] Instagram — immediate (Composio entity: {entity_id})")
        print(f"    Caption preview: {caption[:80]}...")
        return True

    if not image_url:
        print("    SKIP — Instagram requires an image URL.")
        print("    Add PEXELS_API_KEY env var or set image_url in your post data.")
        return False

    # Step 1 — Create media container
    try:
        result = toolset.execute_action(
            action=Action.INSTAGRAM_POST_IG_USER_MEDIA,
            params={
                "ig_user_id": ig_user_id,
                "image_url": image_url,
                "caption": caption,
            },
            entity_id=entity_id,
        )
    except Exception as e:
        print(f"    IG container error: {e}")
        return False

    data = result if isinstance(result, dict) else {}
    # Composio wraps results in a data key
    if "data" in data:
        data = data["data"]
    container_id = data.get("id") or data.get("creation_id")
    if not container_id:
        print(f"    IG error: no container ID in response: {str(result)[:200]}")
        return False

    time.sleep(3)

    # Step 2 — Publish
    try:
        result2 = toolset.execute_action(
            action=Action.INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH,
            params={
                "ig_user_id": ig_user_id,
                "creation_id": container_id,
            },
            entity_id=entity_id,
        )
    except Exception as e:
        print(f"    IG publish error: {e}")
        return False

    data2 = result2 if isinstance(result2, dict) else {}
    if "data" in data2:
        data2 = data2["data"]
    post_id = data2.get("id", "unknown")
    print(f"    Posted — ID: {post_id}")
    return True


# ── Composio — Facebook ───────────────────────────────────────────────────────

def get_facebook_page_id(toolset: "ComposioToolSet", entity_id: str) -> str:
    """Fetch the managed Facebook Page ID via Composio."""
    try:
        result = toolset.execute_action(
            action=Action.FACEBOOK_LIST_MANAGED_PAGES,
            params={},
            entity_id=entity_id,
        )
        data = result if isinstance(result, dict) else {}
        if "data" in data:
            data = data["data"]
        pages = data.get("data", [])
        if pages:
            page_id = pages[0].get("id", "")
            print(f"    Facebook Page ID: {page_id} ({pages[0].get('name', '')})")
            return page_id
    except Exception as e:
        print(f"    Could not fetch Facebook page ID: {e}")
    return ""


def post_facebook_composio(
    toolset: "ComposioToolSet",
    entity_id: str,
    page_id: str,
    message: str,
    image_url: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        print(f"    [DRY RUN] Facebook — immediate (Composio entity: {entity_id})")
        print(f"    Caption preview: {message[:80]}...")
        return True

    if not entity_id:
        print("    SKIP — no Facebook Composio connection for this brand.")
        print("    Connect your Facebook Page at app.composio.dev > Apps > Facebook.")
        return False

    if not page_id:
        print("    Fetching Facebook Page ID...")
        page_id = get_facebook_page_id(toolset, entity_id)
        if not page_id:
            print("    SKIP — could not determine Facebook Page ID.")
            return False

    params = {"page_id": page_id, "message": message}
    if image_url:
        params["url"] = image_url

    try:
        result = toolset.execute_action(
            action=Action.FACEBOOK_CREATE_PHOTO_POST,
            params=params,
            entity_id=entity_id,
        )
    except Exception as e:
        print(f"    FB post error: {e}")
        return False

    data = result if isinstance(result, dict) else {}
    if "data" in data:
        data = data["data"]
    post_id = data.get("id", "unknown")
    print(f"    Posted — ID: {post_id}")
    return True


# ── Scheduling helpers ────────────────────────────────────────────────────────

def build_scheduled_time(start_date: datetime, day_num: int, post_time: str) -> datetime:
    h, m = TIME_TO_HM.get(post_time, (9, 0))
    week_offset = (day_num - 1) // 7
    dow_index = (day_num - 1) % 7
    post_dt = start_date + timedelta(weeks=week_offset, days=dow_index)
    post_dt = post_dt.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=timezone.utc)
    return post_dt


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI content and post directly to Instagram / Facebook via Composio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--brand", required=True, choices=["revitalize", "reclaim"],
        help="Brand to generate content for",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of posts to generate and send (default: 1)",
    )
    parser.add_argument(
        "--platform", default="ig", choices=["ig", "fb", "both"],
        help="ig=Instagram  fb=Facebook  both=both  (default: ig)",
    )
    parser.add_argument(
        "--theme",
        help="Content theme, e.g. 'hormone balance', 'sleep', 'mindset'",
    )
    parser.add_argument(
        "--product",
        help="Product to feature -- partial name, e.g. 'sleep', 'masterclass', 'energy'",
    )
    parser.add_argument(
        "--start-date",
        help="(Note) Scheduling display only -- Composio posts immediately. Format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Generate content and save to JSON only -- do not post to any platform",
    )
    parser.add_argument(
        "--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--composio-key", default=os.environ.get("COMPOSIO_API_KEY", ""),
        help="Composio API key (or set COMPOSIO_API_KEY env var) -- get from app.composio.dev",
    )
    parser.add_argument(
        "--pexels-key", default=os.environ.get("PEXELS_API_KEY", ""),
        help="Pexels API key for auto image fetching (or set PEXELS_API_KEY env var)",
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
            "Get your key at: app.composio.dev > Settings > API Keys"
        )

    cfg = load_config(args.brand)
    cmp_cfg = COMPOSIO_CONFIG[args.brand]

    # Resolve start date (display only — used for post metadata)
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    client = anthropic.Anthropic(api_key=args.anthropic_key) if not args.dry_run else None
    toolset = ComposioToolSet(api_key=args.composio_key) if not args.dry_run and not args.generate_only else None

    # Cached Facebook page ID (fetched once on first FB post)
    fb_page_id_cache = cmp_cfg.get("fb_page_id")

    # Header
    label = "DRY RUN" if args.dry_run else ("GENERATE ONLY" if args.generate_only else "POSTING")
    print(f"\n[{label}]  {cfg['name'].upper()}")
    print(f"Platform : {args.platform.upper()}")
    print(f"Posts    : {args.count}")
    print(f"Via      : Composio (no Meta tokens needed)")
    if start_date:
        print(f"Schedule : starting {start_date.strftime('%A %d %B %Y')}")
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
                "image_suggestion": "Dry run",
            }
        else:
            post = generate_post(client, cfg, args.theme or "", args.product or "", i)
            if not post:
                print("FAILED — skipping")
                continue

        posts.append(post)
        print(f"OK — {post['title'][:50]}")

        if args.generate_only:
            continue

        # Build full caption
        caption = post["caption"]
        if post.get("hashtags"):
            caption += "\n\n" + post["hashtags"]

        # Resolve image
        image_url = resolve_image(post, args.brand, args.pexels_key)

        # Post to Instagram
        if args.platform in ("ig", "both"):
            print(f"  → Instagram ({cmp_cfg['ig_entity_id']})")
            success = post_instagram_composio(
                toolset,
                cmp_cfg["ig_entity_id"],
                cmp_cfg["ig_user_id"],
                caption,
                image_url,
                args.dry_run,
            )
            if success:
                ig_ok += 1
            else:
                ig_fail += 1

        # Post to Facebook
        if args.platform in ("fb", "both"):
            fb_entity = cmp_cfg.get("fb_entity_id")
            print(f"  → Facebook ({fb_entity or 'NOT CONNECTED'})")
            success = post_facebook_composio(
                toolset,
                fb_entity or "",
                fb_page_id_cache or "",
                caption,
                image_url,
                args.dry_run,
            )
            if success:
                fb_ok += 1
            else:
                fb_fail += 1

        if i < args.count and not args.dry_run:
            time.sleep(2)

    # Save JSON
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
