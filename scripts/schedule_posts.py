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

PUBLER_API = "https://app.publer.com/api/v1"

TIME_MAP = {
    "7:00 AM":  7,  "7:30 AM":  7.5, "8:00 AM":  8,  "9:00 AM":  9,
    "10:00 AM": 10, "11:00 AM": 11,  "12:00 PM": 12, "6:00 PM":  18,
    "7:00 PM":  19, "8:00 PM":  20,
    "7am": 7, "9am": 9, "10am": 10, "11am": 11,
    "12pm": 12, "2pm": 14, "5pm": 17, "6pm": 18,
    "7pm": 19, "8am": 8, "7:30am": 7.5,
}

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def parse_hour(time_str: str) -> int:
    t = time_str.strip().upper().replace(" ", "")
    for k, v in TIME_MAP.items():
        if k.upper().replace(" ", "") == t:
            return int(v)
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
    return 9


def build_schedule_date(start_monday: datetime, day_num: int, day_of_week: str, post_time: str) -> str:
    week_offset = (day_num - 1) // 7
    dow_index = DAY_ORDER.index(day_of_week) if day_of_week in DAY_ORDER else (day_num - 1) % 7
    post_date = start_monday + timedelta(weeks=week_offset, days=dow_index)
    hour = parse_hour(post_time)
    post_datetime = post_date.replace(hour=hour, minute=0, second=0, microsecond=0)
    return post_datetime.strftime("%Y-%m-%dT%H:%M:%S")


def get_workspace_id(api_key: str) -> str:
    headers = {
        "Authorization": "Bearer-API " + api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.get(PUBLER_API + "/workspaces", headers=headers, timeout=15)
    print("Workspaces API " + str(resp.status_code) + ": " + resp.text[:500])
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return str(data[0].get("id", data[0].get("_id", "")))
        if isinstance(data, dict):
            workspaces = data.get("workspaces", data.get("data", []))
            if workspaces:
                return str(workspaces[0].get("id", workspaces[0].get("_id", "")))
    return ""


def schedule_post(api_key: str, workspace_id: str, account_ids: list, platform: str,
                  text: str, scheduled_at: str, dry_run: bool) -> dict:
    if dry_run:
        return {"dry_run": True, "scheduled_at": scheduled_at, "preview": text[:80]}

    if platform == "yt":
        network_key = "youtube"
        network_payload = {"text": text}
    else:
        network_key = "instagram"
        network_payload = {"type": "feed", "text": text}

    payload = {
        "bulk": {
            "state": "scheduled",
            "posts": [
                {
                    "networks": {network_key: network_payload},
                    "accounts": [{"id": aid, "scheduled_at": scheduled_at + "Z"} for aid in account_ids],
                }
            ]
        }
    }

    headers = {
        "Authorization": "Bearer-API " + api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if workspace_id:
        headers["Publer-Workspace-Id"] = workspace_id

    resp = requests.post(PUBLER_API + "/posts/schedule", json=payload, headers=headers, timeout=15)
    print("  API " + str(resp.status_code) + ": " + resp.text[:300])
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

    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    if start.weekday() != 0:
        sys.exit("ERROR: start date must be a Monday (got " + start.strftime("%A") + ")")

    ig_profiles = []
    yt_profiles = []
    for p in args.profile_ids:
        if p.startswith("ig:"):
            ig_profiles.append(p[3:])
        elif p.startswith("yt:"):
            yt_profiles.append(p[3:])
        else:
            ig_profiles.append(p)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "posts-" + args.brand + ".json")
    with open(data_path) as f:
        posts = json.load(f)

    prefix = "DRY RUN — " if args.dry_run else ""
    print("\n" + prefix + "Scheduling " + str(len(posts)) + " posts for [" + args.brand.upper() + "]")
    print("Start date : " + start.strftime("%A %d %B %Y"))
    print("IG profiles: " + str(ig_profiles))
    if yt_profiles:
        print("YT profiles: " + str(yt_profiles))
    print("-" * 60)

    workspace_id = ""
    if not args.dry_run:
        workspace_id = os.environ.get("PUBLER_WORKSPACE_ID", "")
        if not workspace_id:
            print("No PUBLER_WORKSPACE_ID set — auto-discovering workspace...")
            workspace_id = get_workspace_id(args.api_key)
            print("Using workspace ID: " + workspace_id)

    success = 0
    for post in posts:
        scheduled_at = build_schedule_date(start, post["day"], post["day_of_week"], post["post_time"])
        caption_with_tags = post["caption"] + ("\n\n" + post["hashtags"] if post["hashtags"] else "")

        if ig_profiles:
            result = schedule_post(args.api_key, workspace_id, ig_profiles, "ig",
                                   caption_with_tags, scheduled_at, args.dry_run)
            status = "OK" if result else "FAIL"
            print("Day " + str(post["day"]).zfill(2) + " [" + post["day_of_week"][:3] + "] " +
                  scheduled_at + "  IG " + status + "  " + post["title"][:40])
            if result:
                success += 1

        if yt_profiles and args.brand == "reclaim":
            yt_text = post["title"] + "\n\n" + caption_with_tags
            result = schedule_post(args.api_key, workspace_id, yt_profiles, "yt",
                                   yt_text, scheduled_at, args.dry_run)
            status = "OK" if result else "FAIL"
            print("Day " + str(post["day"]).zfill(2) + " [" + post["day_of_week"][:3] + "] " +
                  scheduled_at + "  YT " + status + "  " + post["title"][:40])
            if result:
                success += 1

        if not args.dry_run:
            time.sleep(0.5)

    print("-" * 60)
    done_msg = "queued (dry run)" if args.dry_run else "scheduled in Publer"
    print("Done. " + str(success) + " posts " + done_msg + ".")


if __name__ == "__main__":
    main()
