"""
schedule_posts_buffer.py
Reads a posts JSON file and schedules all 30 posts to Buffer via their GraphQL API.

Usage:
  python schedule_posts_buffer.py \
    --brand revitalize \
    --start-date 2026-05-11 \
    --api-key YOUR_BUFFER_API_KEY

  --brand          revitalize | reclaim
  --start-date     Monday date to begin (YYYY-MM-DD). Must be a Monday.
  --api-key        Buffer API key (or set BUFFER_API_KEY env var)
  --ig-channel-id  Buffer Instagram channel ID (skips API discovery).
                   Set via BUFFER_IG_CHANNEL_ID env var to avoid rate limits.
  --yt-channel-id  Buffer YouTube channel ID (optional, reclaim only).
                   Set via BUFFER_YT_CHANNEL_ID env var.
  --discover       Print org and channel IDs then exit (use once to get IDs).
  --dry-run        Print scheduled posts without calling Buffer API
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BUFFER_API = "https://api.buffer.com"

TIME_MAP = {
    "7:00 AM": 7,  "7:30 AM": 7.5, "8:00 AM": 8,  "9:00 AM": 9,
    "10:00 AM": 10, "11:00 AM": 11, "12:00 PM": 12, "6:00 PM": 18,
    "7:00 PM": 19,  "8:00 PM": 20,
    "7am": 7, "9am": 9, "10am": 10, "11am": 11,
    "12pm": 12, "2pm": 14, "5pm": 17, "6pm": 18,
    "7pm": 19, "8am": 8, "7:30am": 7.5,
}

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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


def build_schedule_date(start_monday: datetime, day_num: int, day_of_week: str, post_time: str) -> datetime:
    week_offset = (day_num - 1) // 7
    dow_index = DAY_ORDER.index(day_of_week) if day_of_week in DAY_ORDER else (day_num - 1) % 7
    post_date = start_monday + timedelta(weeks=week_offset, days=dow_index)
    hour = parse_hour(post_time)
    return post_date.replace(hour=hour, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def graphql(api_key: str, query: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    body = {"query": query}
    if variables:
        body["variables"] = variables
    wait = 60
    for attempt in range(6):
        resp = requests.post(BUFFER_API, json=body, headers=headers, timeout=15)
        if resp.status_code != 429:
            break
        print("  Rate limited — sleeping {}s (attempt {}/6)".format(wait, attempt + 1))
        time.sleep(wait)
        wait = min(wait * 2, 300)
    if not resp.ok:
        print("  HTTP {} error. Response body: {}".format(resp.status_code, resp.text[:1000]))
    resp.raise_for_status()
    return resp.json()


def get_org_id(api_key: str) -> str:
    data = graphql(api_key, "query { account { organizations { id name } } }")
    orgs = data["data"]["account"]["organizations"]
    if not orgs:
        sys.exit("ERROR: No Buffer organizations found")
    print("  Org: " + orgs[0]["name"] + " (" + orgs[0]["id"] + ")")
    return orgs[0]["id"]


def get_channel_ids(api_key: str, org_id: str) -> dict:
    query = """
    query GetChannels($input: ChannelsInput!) {
      channels(input: $input) { id name service }
    }
    """
    data = graphql(api_key, query, {"input": {"organizationId": org_id}})
    channels = data["data"]["channels"]
    result = {}
    for ch in channels:
        svc = ch["service"]
        if svc not in result:
            result[svc] = ch["id"]
        print("  Channel: " + ch["service"] + " — " + ch["name"] + " (" + ch["id"] + ")")
    return result


def schedule_post(api_key: str, channel_id: str, text: str, due_at: datetime,
                  image_url: str = None, dry_run: bool = False) -> dict:
    if dry_run:
        return {"dry_run": True, "preview": text[:80]}

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id text dueAt status }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    post_input = {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "scheduled",
        "dueAt": due_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    if image_url:
        post_input["media"] = [{"url": image_url, "type": "IMAGE"}]
    else:
        print("  WARNING: No image_url for this post — Instagram requires an image")

    data = graphql(api_key, mutation, {"input": post_input})
    if "errors" in data:
        print("  GraphQL errors: " + str(data["errors"]))
        return {}
    result = data.get("data", {}).get("createPost", {})
    if "message" in result:
        print("  Buffer error: " + result["message"])
        return {}
    return result.get("post", {})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True, choices=["revitalize", "reclaim"])
    parser.add_argument("--start-date", help="Monday start date YYYY-MM-DD")
    parser.add_argument("--api-key", default=os.environ.get("BUFFER_API_KEY", ""))
    parser.add_argument("--ig-channel-id", default=os.environ.get("BUFFER_IG_CHANNEL_ID", ""),
                        help="Buffer Instagram channel ID (skips discovery)")
    parser.add_argument("--yt-channel-id", default=os.environ.get("BUFFER_YT_CHANNEL_ID", ""),
                        help="Buffer YouTube channel ID (skips discovery)")
    parser.add_argument("--discover", action="store_true",
                        help="Print org and channel IDs then exit")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        sys.exit("ERROR: --api-key or BUFFER_API_KEY env var required")

    # Discovery-only mode: print channel IDs and exit
    if args.discover:
        print("Discovering Buffer channels...")
        org_id = get_org_id(args.api_key)
        channels = get_channel_ids(args.api_key, org_id)
        print("\nAdd these as GitHub Secrets to skip discovery on future runs:")
        if channels.get("instagram"):
            print("  BUFFER_IG_CHANNEL_ID = " + channels["instagram"])
        if channels.get("youtube"):
            print("  BUFFER_YT_CHANNEL_ID = " + channels["youtube"])
        return

    if not args.start_date:
        sys.exit("ERROR: --start-date required")

    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    if start.weekday() != 0:
        sys.exit("ERROR: start date must be a Monday (got " + start.strftime("%A") + ")")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "posts-" + args.brand + ".json")
    with open(data_path) as f:
        posts = json.load(f)

    prefix = "DRY RUN — " if args.dry_run else ""
    print("\n" + prefix + "Scheduling " + str(len(posts)) + " posts for [" + args.brand.upper() + "] via Buffer")
    print("Start date : " + start.strftime("%A %d %B %Y"))
    print("-" * 60)

    ig_channel = args.ig_channel_id or None
    yt_channel = args.yt_channel_id or None

    if not args.dry_run:
        if ig_channel:
            print("Instagram channel: " + ig_channel + " (from env/arg — skipping discovery)")
            if yt_channel:
                print("YouTube channel  : " + yt_channel + " (from env/arg — skipping discovery)")
        else:
            print("Discovering Buffer channels...")
            org_id = get_org_id(args.api_key)
            channels = get_channel_ids(args.api_key, org_id)
            ig_channel = channels.get("instagram")
            yt_channel = channels.get("youtube")
            if not ig_channel:
                sys.exit("ERROR: No Instagram channel found in Buffer. Connect your Instagram Business account first.")
            print("Instagram channel: " + ig_channel)
            if yt_channel:
                print("YouTube channel  : " + yt_channel)
            print("\nTIP: Add BUFFER_IG_CHANNEL_ID=" + ig_channel + " as a GitHub Secret to skip this discovery step next time.")
    print("-" * 60)

    success = 0
    for post in posts:
        due_at = build_schedule_date(start, post["day"], post["day_of_week"], post["post_time"])
        caption = post["caption"] + ("\n\n" + post["hashtags"] if post.get("hashtags") else "")
        image_url = post.get("image_url")

        result = schedule_post(args.api_key, ig_channel or "dry_run", caption,
                               due_at, image_url, args.dry_run)
        status = "OK" if result else "FAIL"
        print("Day " + str(post["day"]).zfill(2) + " [" + post["day_of_week"][:3] + "] " +
              due_at.strftime("%Y-%m-%dT%H:%M") + "  IG " + status + "  " + post["title"][:40])
        if result:
            success += 1

        if yt_channel and args.brand == "reclaim":
            yt_text = post["title"] + "\n\n" + caption
            result = schedule_post(args.api_key, yt_channel, yt_text, due_at, image_url, args.dry_run)
            status = "OK" if result else "FAIL"
            print("Day " + str(post["day"]).zfill(2) + " [" + post["day_of_week"][:3] + "] " +
                  due_at.strftime("%Y-%m-%dT%H:%M") + "  YT " + status + "  " + post["title"][:40])
            if result:
                success += 1

        if not args.dry_run:
            time.sleep(4)

    print("-" * 60)
    done_msg = "queued (dry run)" if args.dry_run else "scheduled in Buffer"
    print("Done. " + str(success) + " posts " + done_msg + ".")


if __name__ == "__main__":
    main()
