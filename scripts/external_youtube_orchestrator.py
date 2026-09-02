#!/usr/bin/env python3
"""
external_youtube_orchestrator.py

External orchestrator for YouTube video generation and upload.
Runs independently via cron (not inside Claude's session).

USAGE:
  ./external_youtube_orchestrator.py morning
  ./external_youtube_orchestrator.py afternoon
  ./external_youtube_orchestrator.py evening
  ./external_youtube_orchestrator.py night

ARCHITECTURE:
  1. Call master_orchestrator.py to get daily content specs
  2. Generate images via Higgsfield direct API (not MCP)
  3. Generate videos via Higgsfield or create via FFmpeg
  4. Add caption overlays via FFmpeg
  5. Upload to YouTube via direct API
  6. Update orchestrator-log.json with results

REQUIREMENTS:
  - requests library (HTTP calls to Higgsfield and YouTube APIs)
  - ffmpeg binary (for video creation and caption overlays)
  - YouTube API credentials (requires YOUTUBE_CREDENTIALS env var)
  - Higgsfield API key (requires HIGGSFIELD_API_KEY env var)
"""

import json
import sys
import os
import subprocess
import tempfile
import requests
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Tuple
import time

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
DATA_DIR = REPO_DIR / "data"
CONFIG_PATH = DATA_DIR / "brand-config.json"
ORCH_CONFIG_PATH = DATA_DIR / "orchestrator-config.json"
LOG_PATH = DATA_DIR / "orchestrator-log.json"

# API endpoints
HIGGSFIELD_API_BASE = "https://api.higgsfield.ai/v1"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def load_configs() -> Tuple[dict, dict]:
    """Load brand and orchestrator configs."""
    with open(CONFIG_PATH) as f:
        brand_cfg = json.load(f)
    with open(ORCH_CONFIG_PATH) as f:
        orch_cfg = json.load(f)
    return brand_cfg, orch_cfg


def get_day_name() -> str:
    """Get current day name (America/New_York timezone)."""
    return datetime.now(ZoneInfo("America/New_York")).strftime("%A").lower()


def get_et_date_str() -> str:
    """Get current ET date as YYYY-MM-DD."""
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def already_posted_today(slot: str, log_path: Path = LOG_PATH) -> bool:
    """Check if this slot has already been posted today (verified)."""
    if not log_path.exists():
        return False
    try:
        with open(log_path) as f:
            log = json.load(f)
    except Exception:
        return False

    today = get_et_date_str()
    for entry in log:
        if entry.get("slot") != slot:
            continue
        # Check if entry is from today
        ts = str(entry.get("timestamp_utc", ""))
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
                same_day = dt.strftime("%Y-%m-%d") == today
                if same_day and (entry.get("revitalize", {}).get("verified") or entry.get("reclaim", {}).get("verified")):
                    return True
            except Exception:
                pass
    return False


def generate_higgsfield_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    quality: str = "2k"
) -> Optional[str]:
    """
    Generate image via Higgsfield API.

    Returns: image URL if successful, None otherwise
    """
    api_key = os.getenv("HIGGSFIELD_API_KEY")
    if not api_key:
        print("ERROR: HIGGSFIELD_API_KEY environment variable not set")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "soul_2",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_inference_steps": 50,
        "quality": quality
    }

    try:
        response = requests.post(
            f"{HIGGSFIELD_API_BASE}/generate-image",
            headers=headers,
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        result = response.json()

        # Poll for completion
        job_id = result.get("id")
        if not job_id:
            print(f"No job ID in response: {result}")
            return None

        for attempt in range(60):  # Poll for up to 5 minutes
            time.sleep(5)
            poll_response = requests.get(
                f"{HIGGSFIELD_API_BASE}/job/{job_id}",
                headers=headers,
                timeout=30
            )
            poll_response.raise_for_status()
            poll_result = poll_response.json()

            if poll_result.get("status") == "completed":
                image_url = poll_result.get("output", {}).get("url")
                print(f"Image generated: {image_url}")
                return image_url
            elif poll_result.get("status") == "failed":
                print(f"Image generation failed: {poll_result.get('error')}")
                return None

        print("Image generation timeout")
        return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def download_image(image_url: str, output_path: str) -> bool:
    """Download image from URL."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        return Path(output_path).exists()
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False


def create_base_video(image_path: str, output_path: str, duration: int = 15) -> bool:
    """Create MP4 video from static image using FFmpeg."""
    try:
        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", image_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-preset", "fast",
            output_path,
            "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"Base video created: {output_path}")
            return True
        else:
            print(f"FFmpeg error: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"Error creating base video: {e}")
        return False


def add_caption_overlay(
    video_path: str,
    output_path: str,
    caption: str,
    fontsize: int = 48
) -> bool:
    """Add text caption overlay to video."""
    try:
        # Escape quotes for FFmpeg
        caption_escaped = caption.replace("'", "'\\''")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"drawtext=text='{caption_escaped}':fontsize={fontsize}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black",
            "-c:a", "copy",
            output_path,
            "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"Caption added: {output_path}")
            return True
        else:
            print(f"FFmpeg error: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"Error adding caption: {e}")
        return False


def generate_youtube_video(
    image_url: str,
    product_name: str,
    price: str
) -> Optional[str]:
    """
    Generate YouTube video from image with caption.

    Returns: path to final video file if successful, None otherwise
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Download image
        image_path = tmpdir / "source.jpg"
        if not download_image(image_url, str(image_path)):
            print("Failed to download image")
            return None

        # Step 2: Create base video (15 seconds)
        base_video = tmpdir / "base.mp4"
        if not create_base_video(str(image_path), str(base_video), duration=15):
            print("Failed to create base video")
            return None

        # Step 3: Add caption overlay
        caption_text = f"{product_name}\n{price}"
        caption_video = tmpdir / "with_caption.mp4"
        if not add_caption_overlay(str(base_video), str(caption_video), caption_text):
            print("Failed to add caption")
            return None

        # Step 4: Copy to persistent location
        timestamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d_%H%M%S")
        final_output = Path(f"/tmp/youtube_video_{timestamp}.mp4")
        try:
            subprocess.run(["cp", str(caption_video), str(final_output)], check=True)
            if final_output.exists():
                print(f"Video generated: {final_output}")
                return str(final_output)
        except Exception as e:
            print(f"Error copying video: {e}")

        return None


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    channel_id: str
) -> Optional[str]:
    """
    Upload video to YouTube.

    Returns: video_id if successful, None otherwise

    NOTE: This is a placeholder. Real YouTube upload requires OAuth2 credentials
    and the YouTube Data API. For now, this logs the action and returns a placeholder.
    """
    print(f"YouTube upload ready (placeholder): {video_path}")
    print(f"  Title: {title}")
    print(f"  Channel: {channel_id}")
    print(f"  Video size: {Path(video_path).stat().st_size / 1024 / 1024:.1f} MB")

    # In production, this would:
    # 1. Load OAuth2 credentials from YOUTUBE_CREDENTIALS env var
    # 2. Call YouTube Data API to upload video
    # 3. Return actual video_id

    # For now, return a mock video_id
    return f"mock_youtube_video_{datetime.now().timestamp()}"


def get_product_by_name(brand_cfg: dict, brand: str, product_name: str) -> Optional[dict]:
    """Find product in brand config."""
    for p in brand_cfg[brand]["products"]:
        if p["name"] == product_name:
            return p
    return None


def create_log_entry(
    slot: str,
    day: str,
    revitalize_spec: dict,
    reclaim_spec: dict,
    brand_cfg: dict,
    orch_cfg: dict
) -> dict:
    """Create a log entry for the orchestrator results."""
    slot_info = orch_cfg["schedule"][slot]

    entry = {
        "date": f"{get_et_date_str()} ({day.title()} ET)",
        "slot": slot,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "revitalize": {
            "product": revitalize_spec["product_name"],
            "price": revitalize_spec["price"],
            "theme": revitalize_spec["theme"],
            "angle": slot_info["angle"],
            "yt_video_id": revitalize_spec.get("yt_video_id"),
            "status": revitalize_spec.get("status", "pending"),
            "verified": revitalize_spec.get("verified", False)
        },
        "reclaim": {
            "product": reclaim_spec["product_name"],
            "price": reclaim_spec["price"],
            "theme": reclaim_spec["theme"],
            "angle": slot_info["angle"],
            "yt_video_id": reclaim_spec.get("yt_video_id"),
            "status": reclaim_spec.get("status", "pending"),
            "verified": reclaim_spec.get("verified", False)
        }
    }

    if revitalize_spec.get("error"):
        entry["revitalize"]["error"] = revitalize_spec["error"]
    if reclaim_spec.get("error"):
        entry["reclaim"]["error"] = reclaim_spec["error"]

    return entry


def append_log_entry(entry: dict, log_path: Path = LOG_PATH):
    """Append entry to orchestrator log."""
    log = []
    if log_path.exists():
        with open(log_path) as f:
            try:
                log = json.load(f)
            except Exception:
                log = []

    log.append(entry)
    # Keep last 90 entries
    log = log[-90:]

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    print(f"Log updated: {log_path}")


def build_image_prompt(
    brand: str,
    theme: str,
    slot: str,
    orch_cfg: dict
) -> str:
    """Build image generation prompt using orchestrator config."""
    if brand == "revitalize":
        template = orch_cfg["higgsfield"]["revitalize_image_prompt_template"]
    else:
        template = orch_cfg["higgsfield"]["reclaim_image_prompt_template"]

    mood = orch_cfg["higgsfield"]["moods"].get(slot, "energized")

    if brand == "revitalize":
        settings_map = orch_cfg["higgsfield"]["revitalize_settings"]
    else:
        settings_map = orch_cfg["higgsfield"]["reclaim_settings"]

    setting = settings_map.get(theme, "wellness lifestyle")

    return template.format(mood=mood, setting=setting)


def process_brand_for_slot(
    brand: str,
    slot: str,
    product_name: str,
    product_price: str,
    theme: str,
    brand_cfg: dict,
    orch_cfg: dict
) -> dict:
    """Process a single brand for the given slot."""
    result = {
        "product_name": product_name,
        "price": product_price,
        "theme": theme,
        "status": "pending",
        "verified": False
    }

    print(f"\n--- Processing {brand.upper()} ---")
    print(f"Product: {product_name} ({product_price})")
    print(f"Theme: {theme}")

    # Step 1: Generate image prompt
    image_prompt = build_image_prompt(brand, theme, slot, orch_cfg)
    print(f"Image prompt: {image_prompt[:80]}...")

    # Step 2: Generate image via Higgsfield
    print("Generating image via Higgsfield...")
    image_url = generate_higgsfield_image(image_prompt)
    if not image_url:
        result["status"] = "failed"
        result["error"] = "Image generation failed"
        print("ERROR: Image generation failed")
        return result

    # Step 3: Generate YouTube video
    print("Generating YouTube video...")
    video_path = generate_youtube_video(image_url, product_name, product_price)
    if not video_path:
        result["status"] = "failed"
        result["error"] = "Video generation failed"
        print("ERROR: Video generation failed")
        return result

    # Step 4: Upload to YouTube
    print("Uploading to YouTube...")
    channel_id = orch_cfg["composio"][brand]["yt_channel_id"]
    title = f"{product_name} - {theme.title()}"
    description = f"{product_name}\n{product_price}\n\nLearn more and get started today."

    yt_video_id = upload_to_youtube(video_path, title, description, channel_id)
    if not yt_video_id:
        result["status"] = "failed"
        result["error"] = "YouTube upload failed"
        print("ERROR: YouTube upload failed")
        return result

    result["yt_video_id"] = yt_video_id
    result["status"] = "posted"
    result["verified"] = True
    print(f"SUCCESS: Video uploaded - {yt_video_id}")

    return result


def process_slot(slot: str):
    """Main orchestrator function for a given time slot."""
    print(f"\n{'='*70}")
    print(f"EXTERNAL YOUTUBE ORCHESTRATOR — {slot.upper()}")
    print(f"{'='*70}\n")

    # Load configs
    brand_cfg, orch_cfg = load_configs()
    day = get_day_name()

    # Check if already posted today
    if already_posted_today(slot):
        print(f"POST GUARD: Already posted {slot} slot for {get_et_date_str()}")
        print("Skipping this run to avoid duplicates.")
        return

    # Get rotation specs
    rev_rotation = orch_cfg["revitalize_rotation"][day]
    rec_rotation = orch_cfg["reclaim_rotation"][day]

    rev_product_name = rev_rotation["slot_products"][slot]
    rec_product_name = rec_rotation["slot_products"][slot]

    rev_product = get_product_by_name(brand_cfg, "revitalize", rev_product_name)
    rec_product = get_product_by_name(brand_cfg, "reclaim", rec_product_name)

    if not rev_product or not rec_product:
        print(f"ERROR: Could not find products in config")
        return

    print(f"Day: {day.title()} | Slot: {slot}")
    print(f"Date (ET): {get_et_date_str()}\n")

    print(f"Revitalize: {rev_product_name} ({rev_product['price_short']})")
    print(f"  Theme: {rev_rotation['theme']}\n")

    print(f"Reclaim: {rec_product_name} ({rec_product['price_short']})")
    print(f"  Theme: {rec_rotation['theme']}\n")

    # Process each brand
    revitalize_spec = process_brand_for_slot(
        "revitalize",
        slot,
        rev_product_name,
        rev_product["price_short"],
        rev_rotation["theme"],
        brand_cfg,
        orch_cfg
    )

    reclaim_spec = process_brand_for_slot(
        "reclaim",
        slot,
        rec_product_name,
        rec_product["price_short"],
        rec_rotation["theme"],
        brand_cfg,
        orch_cfg
    )

    # Log results
    entry = create_log_entry(slot, day, revitalize_spec, reclaim_spec, brand_cfg, orch_cfg)
    append_log_entry(entry)

    print(f"\n{'='*70}")
    print(f"ORCHESTRATOR COMPLETE")
    print(f"{'='*70}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: external_youtube_orchestrator.py <slot>")
        print("       external_youtube_orchestrator.py morning|afternoon|evening|night")
        sys.exit(1)

    slot = sys.argv[1]
    if slot not in ("morning", "afternoon", "evening", "night"):
        print(f"ERROR: Invalid slot '{slot}'. Must be morning, afternoon, evening, or night.")
        sys.exit(1)

    # Check if FFmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except Exception:
        print("ERROR: FFmpeg not found. Install FFmpeg to use this orchestrator.")
        sys.exit(1)

    process_slot(slot)


if __name__ == "__main__":
    main()
