"""
schedule_posts.py
Reads a posts JSON file and schedules all 30 posts to Publer via their API.

Usage:
  python schedule_posts.py \
    --brand revitalize \
    --start-date 2025-06-02 \
    --api-key YOUR_PUBLER_API_KEY \
    --profile-ids ig:PROFILE_ID [yt:PROFILE_ID]

  --brand         revitalize | reclaim
  --start-date    Monday date to begin (YYYY-MM-DD). Must be a Monday.
  --api-key       Publer API key (or set PUBLER_API_KEY env var)
  --profile-ids   One or more Publer social profile IDs prefixed with platform
                  e.g.  ig:abc123   yt:def456
  --dry-run       Print scheduled posts without calling Publer API
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests

PUBLER_API = "https://app.publer.io/api/v1"

TIME_MAP = {
    "7:00 AM":  7,  "7:30 AM":  7.5, "8:00 AM":  8,  "9:00 AM":  9,
    "10:00 AM": 10, "11:00 AM": 11,  "12:00 PM": 12, "6:00 PM":  18,
    "7:00 PM":  19, "7:00 PM":  19,  "8:00 PM":  20,
    # Reclaim IG times
    "7am": 7, "9am": 9, "10am": 10, "11am": 11,
    "12pm": 12, "2pm": 14, "5pm": 17, "6pm": 18,
    "7pm": 19, "8am": 8, "7:30am": 7.5,
}

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def parse_hour(time_str: str) -> int:
    t = time_str.strip().upper().replace(" ", "")
    # Try direct map first
    for k, v in TIME_MAP.items():
        if k.upper().replace(" ", "") == t:
            return int(v)
    # Fallback: try to parse manually
    try:
        dt = datetime.strptime(time_str.strip(), "%I:%M %p")
        return dt.hour
    except ValueError:
        pass
    try:
        dt = datetime.strptime(time_str.strip(), "%I%p")
        return dt.hour
    except ValueError:
        pass
    return 9  # default 9am if unparseable


def build_schedule_date(start_monday: datetime, day_num: int, day_of_week: str, post_time: str) -> str:
    """Returns ISO 8601 datetime string for the post."""
    # day_num 1-7 = week 1, 8-14 = week 2, etc.
    week_offset = (day_num - 1) // 7
    dow_index = DAY_ORDER.index(day_of_week) if day_of_week in DAY_ORDER else (day_num - 1) % 7
    post_date = start_monday + timedelta(weeks=week_offset, days=dow_index)
    hour = parse_hour(post_time)
    post_datetime = post_date.replace(hour=hour, minute=0, second=0, microsecond=0)
    return post_datetime.strftime("%Y-%m-%dT%H:%M:%S")


def schedule_post(api_key: str, profile_ids: list, text: str, scheduled_at: str, dry_run: bool) -> dict:
    full_text = text
    payload = {
        "post": {
            "content": full_text,
            "scheduled_at": scheduled_at,
            "social_profile_ids": profile_ids,
        }
    }
    if dry_run:
        return {"dry_run": True, "scheduled_at": scheduled_at, "preview": full_text[:80]}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(f"{PUBLER_API}/posts", json=payload, headers=headers, timeout=15)
    print(f"  API response {resp.status_code}: {resp.text[:300]}")
    if resp.status_code not in (200, 201):
        return {}
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True, choices=["revitalize","reclaim"])
    parser.add_argument("--start-date", required=True, help="Monday start date YYYY-MM-DD")
    parser.add_argument("--api-key", default=os.environ.get("PUBLER_API_KEY",""))
    parser.add_argument("--profile-ids", nargs="+", required=True,
                        help="e.g. ig:abc123 yt:def456")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        sys.exit("ERROR: --api-key or PUBLER_API_KEY env var required")

    # Parse start date
    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    if start.weekday() != 0:
        sys.exit(f"ERROR: start date must be a Monday (got {start.strftime('%A')})")

    # Parse profile IDs (ig:xxx or yt:xxx or plain id)
    ig_profiles = []
    yt_profiles = []
    for p in args.profile_ids:
        if p.startswith("ig:"):
            ig_profiles.append(p[3:])
        elif p.startswith("yt:"):
            yt_profiles.append(p[3:])
        else:
            ig_profiles.append(p)

    # Load posts JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", f"posts-{args.brand}.json")
    with open(data_path) as f:
        posts = json.load(f)

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Scheduling {len(posts)} posts for [{args.brand.upper()}]")
    print(f"Start date : {start.strftime('%A %d %B %Y')}")
    print(f"IG profiles: {ig_profiles}")
    if yt_profiles:
        print(f"YT profiles: {yt_profiles}")
    print("-" * 60)

    success = 0
    for post in posts:
        scheduled_at = build_schedule_date(start, post["day"], post["day_of_week"], post["post_time"])
        caption_with_tags = post["caption"] + ("\n\n" + post["hashtags"] if post["hashtags"] else "")

        # Instagram post
        if ig_profiles:
            result = schedule_post(args.api_key, ig_profiles, caption_with_tags, scheduled_at, args.dry_run)
            status = "OK" if result else "FAIL"
            print(f"Day {post['day']:02d} [{post['day_of_week'][:3]}] {scheduled_at}  IG {status}  {post['title'][:40]}")
            if result:
                success += 1

        # YouTube post (Reclaim only, uses title as headline)
        if yt_profiles and args.brand == "reclaim":
            yt_text = f"{post['title']}\n\n{caption_with_tags}"
            result = schedule_post(args.api_key, yt_profiles, yt_text, scheduled_at, args.dry_run)
            status = "OK" if result else "FAIL"
            print(f"Day {post['day']:02d} [{post['day_of_week'][:3]}] {scheduled_at}  YT {status}  {post['title'][:40]}")
            if result:
                success += 1

        if not args.dry_run:
            time.sleep(0.3)  # avoid rate limits

    print("-" * 60)
    print(f"Done. {success} posts {'queued (dry run)' if args.dry_run else 'scheduled in Publer'}.")


if __name__ == "__main__":
    main()
