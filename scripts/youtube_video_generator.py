#!/usr/bin/env python3
"""
youtube_video_generator.py

Generates MP4 videos from portrait images for YouTube posting.
Uses FFmpeg for local, cost-free video encoding (Option B approach).

USAGE:
  Called from orchestrator during evening trigger (7 PM ET)
  when posting Reclaim brand content to YouTube.

WORKFLOW:
  1. Download image from URL
  2. Create MP4 base video (1920x1080, 30 seconds)
  3. Add caption overlay (product name + price)
  4. Add background music track
  5. Upload to YouTube via API
  6. Return video_id for logging
"""

import json
import subprocess
import urllib.request
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def download_image(image_url: str, output_path: str) -> bool:
    """Download image from URL and save locally."""
    try:
        urllib.request.urlretrieve(image_url, output_path)
        return Path(output_path).exists()
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False


def create_base_video(image_path: str, output_path: str, duration: int = 30) -> bool:
    """Create MP4 from static image using FFmpeg."""
    try:
        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", image_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            output_path,
            "-y"  # Overwrite output file
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0 and Path(output_path).exists()
    except Exception as e:
        print(f"Error creating base video: {e}")
        return False


def add_caption_overlay(
    video_path: str,
    output_path: str,
    caption: str,
    fontsize: int = 60
) -> bool:
    """Add text caption overlay to video (product name + price)."""
    try:
        # Escape single quotes in caption for FFmpeg filter
        caption_escaped = caption.replace("'", "'\\''")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"drawtext=text='{caption_escaped}':fontsize={fontsize}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black",
            "-c:a", "copy",
            output_path,
            "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0 and Path(output_path).exists()
    except Exception as e:
        print(f"Error adding caption: {e}")
        return False


def add_audio_track(
    video_path: str,
    audio_path: str,
    output_path: str
) -> bool:
    """Add background music to video."""
    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path,
            "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0 and Path(output_path).exists()
    except Exception as e:
        print(f"Error adding audio: {e}")
        return False


def generate_youtube_video(
    image_url: str,
    product_name: str,
    price: str,
    caption: str,
    theme: str
) -> tuple[str, bool]:
    """
    Main function: Generate complete YouTube video from image.

    Returns: (video_file_path, success_flag)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Download image
        image_path = tmpdir / "source.jpg"
        if not download_image(image_url, str(image_path)):
            print(f"Failed to download image from {image_url}")
            return "", False

        # Step 2: Create base video
        base_video = tmpdir / "base.mp4"
        if not create_base_video(str(image_path), str(base_video), duration=30):
            print("Failed to create base video")
            return "", False

        # Step 3: Add caption (product name + price)
        caption_text = f"{product_name} - {price}"
        caption_video = tmpdir / "with_caption.mp4"
        if not add_caption_overlay(str(base_video), str(caption_video), caption_text):
            print("Failed to add caption overlay")
            return "", False

        # Step 4: Add audio (use placeholder path - will be provided by trigger)
        # For now, return video with caption (audio is optional)
        final_video = tmpdir / "reclaim_video_final.mp4"

        # Copy caption video to final location in /tmp for persistence
        final_output = Path(f"/tmp/reclaim_video_{datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d_%H%M%S')}.mp4")
        subprocess.run(["cp", str(caption_video), str(final_output)], check=True)

        if final_output.exists():
            print(f"Video generated successfully: {final_output}")
            return str(final_output), True
        else:
            print("Failed to copy video to final location")
            return "", False


def get_youtube_metadata(
    product_name: str,
    price: str,
    product_url: str,
    caption: str,
    theme: str
) -> dict:
    """Build YouTube video metadata for upload."""
    return {
        "snippet": {
            "title": f"{product_name} - Complete System for {theme.title()}",
            "description": f"{caption}\n\nOrder now: {product_url}\nPrice: {price}\n\n#wellness #menshealth #recovery #sleep #testosterone",
            "tags": ["wellness", "mens health", "recovery", "sleep", "testosterone", "performance", "health"],
            "categoryId": "22"  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False
        }
    }


if __name__ == "__main__":
    # Test mode
    print("YouTube Video Generator (Option B: FFmpeg)")
    print("Ready to be called from orchestrator trigger")
    print("Supports: Static image + caption + optional audio → MP4 for YouTube")
