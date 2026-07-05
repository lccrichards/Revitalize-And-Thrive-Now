#!/usr/bin/env python3
"""
post_direct.py
Generate AI content and post directly to Instagram and Facebook.
No GitHub. No Publer. No Buffer.

Requirements:
  pip install anthropic requests

One-time setup — get your Meta credentials:
  1. Go to developers.facebook.com and create a free App (type: Business)
  2. Add "Instagram Graph API" and "Pages API" products to your app
  3. Connect your Instagram Business account to your Facebook Page
     (Instagram app > Settings > Linked Accounts)
  4. Get your access token:
     - Go to developers.facebook.com/tools/explorer
     - Select your App, select your Page
     - Add permissions: pages_manage_posts, pages_read_engagement,
       instagram_basic, instagram_content_publish
     - Click "Generate Access Token" and copy it
  5. Find your IDs:
     - Instagram Business Account ID:
         curl "https://graph.facebook.com/v20.0/me/accounts?access_token=TOKEN"
         then: curl "https://graph.facebook.com/v20.0/PAGE_ID?fields=instagram_business_account&access_token=TOKEN"
     - Facebook Page ID: returned from the /me/accounts call above
  6. (Optional) Get a free Pexels API key at pexels.com/api for auto image fetching

Set environment variables:
  export ANTHROPIC_API_KEY=sk-ant-...
  export META_ACCESS_TOKEN=your_page_access_token
  export META_IG_USER_ID=your_instagram_business_account_id
  export META_PAGE_ID=your_facebook_page_id
  export PEXELS_API_KEY=your_pexels_key   (optional — enables auto image fetching)

Usage:
  # Post 1 post to Instagram right now
  python scripts/post_direct.py --brand revitalize --platform ig

  # Schedule 7 posts to Instagram starting next Monday
  python scripts/post_direct.py --brand revitalize --count 7 --start-date 2026-06-02 --platform ig

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
META_API = "https://graph.facebook.com/v20.0"
PEXELS_API = "https://api.pexels.com/v1/search"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
POST_FORMATS = ["reel", "feed", "feed", "reel", "feed", "reel", "feed"]
POST_TIMES = ["7:00 AM", "8:00 AM", "9:00 AM", "7:00 AM", "8:00 AM", "7:00 AM", "10:00 AM"]
TIME_TO_HM = {
    "7:00 AM": (7, 0), "8:00 AM": (8, 0), "9:00 AM": (9, 0),
    "10:00 AM": (10, 0), "11:00 AM": (11, 0), "12:00 PM": (12, 0),
}

# Fallback images if no Pexels key and no image_url on the post
BRAND_FALLBACK_IMAGE = {
    "revitalize": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "reclaim": "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=1080",
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
    """Fetch a relevant square image from Pexels using the post's image_suggestion."""
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
    """Return the best available image URL for a post."""
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


# ── Meta API — Instagram ──────────────────────────────────────────────────────

def post_instagram(
    ig_user_id: str,
    access_token: str,
    caption: str,
    image_url: str,
    scheduled_time: datetime | None,
    dry_run: bool,
) -> bool:
    if dry_run:
        timing = f"scheduled {scheduled_time.strftime('%Y-%m-%d %H:%M')}" if scheduled_time else "immediate"
        print(f"    [DRY RUN] Instagram — {timing}")
        print(f"    Caption preview: {caption[:80]}...")
        return True

    if not image_url:
        print("    SKIP — Instagram requires an image URL.")
        print("    Add PEXELS_API_KEY env var or set image_url in your post data.")
        return False

    # Step 1 — Create media container
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }
    if scheduled_time:
        params["published"] = "false"
        params["scheduled_publish_time"] = str(int(scheduled_time.timestamp()))
    else:
        params["published"] = "true"

    resp = requests.post(f"{META_API}/{ig_user_id}/media", params=params, timeout=20)
    if not resp.ok:
        print(f"    IG container error {resp.status_code}: {resp.text[:200]}")
        return False

    container_id = resp.json().get("id")
    if not container_id:
        print("    IG error: no container ID returned")
        return False

    if scheduled_time:
        print(f"    Scheduled for {scheduled_time.strftime('%A %Y-%m-%d %H:%M')} UTC")
        return True

    # Step 2 — Publish immediately
    time.sleep(3)
    resp2 = requests.post(
        f"{META_API}/{ig_user_id}/media_publish",
        params={"creation_id": container_id, "access_token": access_token},
        timeout=20,
    )
    if not resp2.ok:
        print(f"    IG publish error {resp2.status_code}: {resp2.text[:200]}")
        return False

    post_id = resp2.json().get("id", "unknown")
    print(f"    Posted — ID: {post_id}")
    return True


# ── Meta API — Facebook ───────────────────────────────────────────────────────

def post_facebook(
    page_id: str,
    access_token: str,
    message: str,
    image_url: str,
    scheduled_time: datetime | None,
    dry_run: bool,
) -> bool:
    if dry_run:
        timing = f"scheduled {scheduled_time.strftime('%Y-%m-%d %H:%M')}" if scheduled_time else "immediate"
        print(f"    [DRY RUN] Facebook — {timing}")
        print(f"    Caption preview: {message[:80]}...")
        return True

    params = {"access_token": access_token, "message": message}
    if scheduled_time:
        params["published"] = "false"
        params["scheduled_publish_time"] = str(int(scheduled_time.timestamp()))

    if image_url:
        params["url"] = image_url
        endpoint = f"{META_API}/{page_id}/photos"
    else:
        endpoint = f"{META_API}/{page_id}/feed"

    resp = requests.post(endpoint, params=params, timeout=20)
    if not resp.ok:
        print(f"    FB error {resp.status_code}: {resp.text[:200]}")
        return False

    if scheduled_time:
        print(f"    Scheduled for {scheduled_time.strftime('%A %Y-%m-%d %H:%M')} UTC")
    else:
        post_id = resp.json().get("id", "unknown")
        print(f"    Posted — ID: {post_id}")
    return True


# ── Scheduling helpers ────────────────────────────────────────────────────────

def build_scheduled_time(start_date: datetime, day_num: int, post_time: str) -> datetime:
    h, m = TIME_TO_HM.get(post_time, (9, 0))
    week_offset = (day_num - 1) // 7
    dow_index = (day_num - 1) % 7
    post_dt = start_date + timedelta(weeks=week_offset, days=dow_index)
    post_dt = post_dt.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=timezone.utc)
    # Meta requires scheduled posts to be at least 10 minutes in the future
    min_future = datetime.now(timezone.utc) + timedelta(minutes=15)
    if post_dt < min_future:
        post_dt = min_future
    return post_dt


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI content and post directly to Instagram / Facebook",
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
        help="Schedule start date YYYY-MM-DD. If omitted, posts are published immediately.",
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
        "--access-token", default=os.environ.get("META_ACCESS_TOKEN", ""),
        help="Meta Page access token (or set META_ACCESS_TOKEN env var)",
    )
    parser.add_argument(
        "--ig-user-id", default=os.environ.get("META_IG_USER_ID", ""),
        help="Instagram Business Account ID (or set META_IG_USER_ID env var)",
    )
    parser.add_argument(
        "--page-id", default=os.environ.get("META_PAGE_ID", ""),
        help="Facebook Page ID (or set META_PAGE_ID env var)",
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

    # Validate credentials
    if not args.anthropic_key and not args.dry_run:
        sys.exit("ERROR: ANTHROPIC_API_KEY required (or pass --anthropic-key)")

    if not args.generate_only and not args.dry_run:
        if args.platform in ("ig", "both") and not args.ig_user_id:
            sys.exit("ERROR: META_IG_USER_ID required for Instagram (or pass --ig-user-id)")
        if args.platform in ("fb", "both") and not args.page_id:
            sys.exit("ERROR: META_PAGE_ID required for Facebook (or pass --page-id)")
        if not args.access_token:
            sys.exit("ERROR: META_ACCESS_TOKEN required (or pass --access-token)")

    # Parse start date
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    cfg = load_config(args.brand)
    client = anthropic.Anthropic(api_key=args.anthropic_key) if not args.dry_run else None

    # Header
    label = "DRY RUN" if args.dry_run else ("GENERATE ONLY" if args.generate_only else "POSTING")
    print(f"\n[{label}]  {cfg['name'].upper()}")
    print(f"Platform : {args.platform.upper()}")
    print(f"Posts    : {args.count}")
    if start_date:
        print(f"Schedule : starting {start_date.strftime('%A %d %B %Y')}")
    elif not args.generate_only:
        print(f"Timing   : immediate")
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
                "caption": "Dry run — API not called.",
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

        # Build schedule time if requested
        sched = build_scheduled_time(start_date, i, post["post_time"]) if start_date else None

        # Post to Instagram
        if args.platform in ("ig", "both"):
            success = post_instagram(
                args.ig_user_id, args.access_token, caption, image_url, sched, args.dry_run
            )
            if success:
                ig_ok += 1
            else:
                ig_fail += 1

        # Post to Facebook
        if args.platform in ("fb", "both"):
            success = post_facebook(
                args.page_id, args.access_token, caption, image_url, sched, args.dry_run
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
