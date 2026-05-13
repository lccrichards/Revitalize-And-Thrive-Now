"""
generate_buffer_csv.py
Generates Publer bulk-upload CSV files from posts JSON data.

Publer CSV format: Date, Time, Message, Photo 1
Upload at: publer.io > Bulk Schedule > Import CSV

Usage:
  python scripts/generate_buffer_csv.py --brand revitalize --start-date 2026-05-18
  python scripts/generate_buffer_csv.py --brand reclaim --start-date 2026-05-18
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TIME_MAP = {
    "7:00 AM": 7,  "7:30 AM": 7.5, "8:00 AM": 8,  "9:00 AM": 9,
    "10:00 AM": 10, "11:00 AM": 11, "12:00 PM": 12, "6:00 PM": 18,
    "7:00 PM": 19,  "8:00 PM": 20,
    "7am": 7, "9am": 9, "10am": 10, "11am": 11,
    "12pm": 12, "2pm": 14, "5pm": 17, "6pm": 18,
    "7pm": 19, "8am": 8, "7:30am": 7.5,
}


def parse_hour(time_str):
    t = time_str.strip().upper().replace(" ", "")
    for k, v in TIME_MAP.items():
        if k.upper().replace(" ", "") == t:
            return int(v), int((v % 1) * 60)
    try:
        dt = datetime.strptime(time_str.strip(), "%I:%M %p")
        return dt.hour, dt.minute
    except ValueError:
        pass
    return 9, 0


def build_date(start_monday, day_num, day_of_week, post_time):
    week_offset = (day_num - 1) // 7
    dow_index = DAY_ORDER.index(day_of_week) if day_of_week in DAY_ORDER else (day_num - 1) % 7
    post_date = start_monday + timedelta(weeks=week_offset, days=dow_index)
    hour, minute = parse_hour(post_time)
    return post_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True, choices=["revitalize", "reclaim"])
    parser.add_argument("--start-date", required=True, help="Monday start date YYYY-MM-DD")
    args = parser.parse_args()

    try:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        sys.exit("ERROR: --start-date must be YYYY-MM-DD")

    if start.weekday() != 0:
        sys.exit("ERROR: start date must be a Monday (got " + start.strftime("%A") + ")")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "posts-" + args.brand + ".json")
    out_path = os.path.join(script_dir, "..", "data", "buffer-upload-" + args.brand + ".csv")

    with open(data_path) as f:
        posts = json.load(f)

    with open(out_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        # Publer bulk upload headers (exact Publer format)
        writer.writerow(["Date", "Message", "Link", "Media URLs"])

        for post in posts:
            dt = build_date(start, post["day"], post["day_of_week"], post["post_time"])
            caption = post["caption"]
            if post.get("hashtags"):
                caption += "\n\n" + post["hashtags"]

            writer.writerow([
                dt.strftime("%Y-%m-%d %H:%M"),  # Publer format: YYYY-MM-DD HH:MM
                caption,
                "",                              # Link (empty)
                post.get("image_url", ""),
            ])

    print("CSV saved to: " + out_path)
    print("Posts exported: " + str(len(posts)))
    print("\nTo upload to Publer:")
    print("1. Go to publer.io > Bulk Schedule")
    print("2. Select your Instagram account")
    print("3. Click 'Import CSV'")
    print("4. Upload: " + os.path.basename(out_path))


if __name__ == "__main__":
    main()
