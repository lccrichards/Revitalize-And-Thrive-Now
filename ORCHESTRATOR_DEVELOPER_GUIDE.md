# Orchestrator Developer Guide

Guide for developers extending or customizing the YouTube orchestrator.

## Architecture Overview

The orchestrator is modular and designed for extensibility:

```
external_youtube_orchestrator.py
├── Configuration Loading
│   ├── load_configs()          # Load brand-config.json + orchestrator-config.json
│   └── get_day_name()          # Determine current day
│
├── Image Generation
│   ├── build_image_prompt()    # Construct Higgsfield prompt
│   └── generate_higgsfield_image()  # Call Higgsfield API
│
├── Video Creation
│   ├── download_image()        # Save image locally
│   ├── create_base_video()     # Convert image to MP4 via FFmpeg
│   └── add_caption_overlay()   # Add text overlay via FFmpeg
│
├── Upload
│   └── upload_to_youtube()     # Upload to YouTube (placeholder)
│
├── Logging
│   ├── create_log_entry()      # Structure results
│   └── append_log_entry()      # Write to orchestrator-log.json
│
└── Main Orchestration
    ├── process_brand_for_slot()  # Single brand pipeline
    └── process_slot()            # Process morning/afternoon/evening/night
```

## Extending the Orchestrator

### Adding a New Brand

To add a third brand (e.g., "Thrive Plus"):

1. **Update data/orchestrator-config.json:**

```json
{
  "schedule": { ... },
  "revitalize_rotation": { ... },
  "reclaim_rotation": { ... },
  "thrive_plus_rotation": {
    "monday": {
      "theme": "wellness basics",
      "slot_products": {
        "morning": "Product Name",
        "afternoon": "Product Name",
        ...
      }
    },
    ...
  },
  "higgsfield": {
    "thrive_plus_image_prompt_template": "...",
    ...
  },
  "composio": {
    "thrive_plus": {
      "yt_channel_id": "UCxxxxx...",
      "yt_composio_account": "Thrive Plus",
      ...
    }
  }
}
```

2. **Update data/brand-config.json:**

```json
{
  "revitalize": { ... },
  "reclaim": { ... },
  "thrive_plus": {
    "name": "Thrive Plus",
    "tagline": "...",
    "audience": "...",
    "voice": "...",
    "products": [ ... ]
  }
}
```

3. **Modify external_youtube_orchestrator.py:**

```python
def process_slot(slot: str):
    # ... existing code ...
    
    thrive_rotation = orch_cfg.get("thrive_plus_rotation", {}).get(day, {})
    thrive_product_name = thrive_rotation.get("slot_products", {}).get(slot)
    thrive_product = get_product_by_name(brand_cfg, "thrive_plus", thrive_product_name)
    
    thrive_spec = process_brand_for_slot(
        "thrive_plus",
        slot,
        thrive_product_name,
        thrive_product["price_short"],
        thrive_rotation["theme"],
        brand_cfg,
        orch_cfg
    )
    
    entry = create_log_entry(slot, day, revitalize_spec, reclaim_spec, thrive_spec, brand_cfg, orch_cfg)
```

### Using Different Image Models

The orchestrator currently uses `soul_2` for Higgsfield. To switch to a different model:

```python
def generate_higgsfield_image(
    prompt: str,
    model: str = "soul_2",  # Add model parameter
    aspect_ratio: str = "1:1",
    quality: str = "2k"
) -> Optional[str]:
    payload = {
        "model": model,  # Use parameter instead of hardcoded
        "prompt": prompt,
        ...
    }
```

Call with different models:
```python
# Portrait images (default)
image_url = generate_higgsfield_image(prompt, model="soul_2")

# Landscape images
image_url = generate_higgsfield_image(prompt, model="landscape_pro", aspect_ratio="16:9")
```

### Custom Video Processing

Extend `create_base_video()` to add effects:

```python
def create_base_video_with_effects(
    image_path: str,
    output_path: str,
    duration: int = 15,
    effects: list = None
) -> bool:
    """Create video with optional effects (zoom, fade, etc)."""
    
    # Base FFmpeg command
    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", image_path,
    ]
    
    # Add effects to filter chain
    filters = []
    if effects:
        if "zoom" in effects:
            filters.append("scale=iw*1.1:ih*1.1")  # Ken burns effect
        if "fade_in" in effects:
            filters.append("fade=t=in:st=0:d=2")
    
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    
    cmd.extend([
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output_path,
        "-y"
    ])
    
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    return result.returncode == 0 and Path(output_path).exists()
```

Usage:
```python
# Create video with zoom effect
create_base_video_with_effects(
    str(image_path),
    str(base_video),
    duration=15,
    effects=["zoom", "fade_in"]
)
```

### Adding Music Tracks

Extend `add_caption_overlay()` to include `add_audio_track()`:

```python
def generate_youtube_video(
    image_url: str,
    product_name: str,
    price: str,
    add_music: bool = False
) -> Optional[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # ... existing steps ...
        
        # New: Add music track if enabled
        if add_music:
            audio_path = Path("/path/to/royalty_free_track.mp3")
            if audio_path.exists():
                final_with_audio = tmpdir / "with_audio.mp4"
                add_audio_track(str(caption_video), str(audio_path), str(final_with_audio))
                caption_video = final_with_audio
        
        # ... rest of function ...
```

### Batch Processing

Extend to process multiple slots in one run:

```python
def process_multiple_slots(slots: list = None):
    """Process multiple slots at once."""
    if slots is None:
        slots = ["morning", "afternoon", "evening", "night"]
    
    for slot in slots:
        print(f"\nProcessing {slot}...")
        process_slot(slot)
        # Add delay between slots to avoid rate limiting
        time.sleep(30)
    
    print(f"\nCompleted {len(slots)} slots")
```

Update `main()` to support:
```python
def main():
    if len(sys.argv) > 1:
        slot_arg = sys.argv[1]
        if slot_arg == "all":
            process_multiple_slots()
        elif slot_arg in ("morning", "afternoon", "evening", "night"):
            process_slot(slot_arg)
    else:
        # Default to current slot
        slot = get_time_slot()
        process_slot(slot)

# Usage: ./scripts/external_youtube_orchestrator.py all
```

### Integrating with Composio for YouTube Upload

Replace the placeholder `upload_to_youtube()`:

```python
import json
import requests

def upload_to_youtube_via_composio(
    video_path: str,
    title: str,
    description: str,
    channel_id: str,
    composio_account: str  # e.g., "Revitalize & Thrive Now"
) -> Optional[str]:
    """Upload video to YouTube using Composio."""
    
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY not set")
        return None
    
    # Step 1: Create upload job
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    create_payload = {
        "account": composio_account,
        "title": title,
        "description": description,
        "privacy_status": "public",
        "channel_id": channel_id
    }
    
    response = requests.post(
        "https://api.composio.dev/v1/youtube/create-upload",
        headers=headers,
        json=create_payload
    )
    response.raise_for_status()
    upload_job_id = response.json().get("id")
    
    # Step 2: Upload file
    with open(video_path, "rb") as f:
        files = {"video": f}
        upload_response = requests.post(
            f"https://api.composio.dev/v1/youtube/upload/{upload_job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files
        )
        upload_response.raise_for_status()
    
    # Step 3: Get video ID
    poll_response = requests.get(
        f"https://api.composio.dev/v1/youtube/upload/{upload_job_id}/status",
        headers=headers
    )
    poll_response.raise_for_status()
    
    video_id = poll_response.json().get("video_id")
    return video_id
```

Update process_brand_for_slot():
```python
# Step 4: Upload to YouTube
yt_video_id = upload_to_youtube_via_composio(
    video_path,
    title,
    description,
    channel_id,
    orch_cfg["composio"][brand]["yt_composio_account"]
)
```

### Adding Slack Notifications

```python
import requests

def notify_slack(channel: str, message: str, status: str = "success"):
    """Send notification to Slack."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    color = "#00AA00" if status == "success" else "#AA0000"
    
    payload = {
        "attachments": [{
            "color": color,
            "title": f"Orchestrator {status.upper()}",
            "text": message,
            "ts": int(time.time())
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

Use in process_brand_for_slot():
```python
if result.get("status") == "posted":
    notify_slack(
        "#videos",
        f"✓ {brand.upper()} video posted: {result['yt_video_id']}"
    )
else:
    notify_slack(
        "#errors",
        f"✗ {brand.upper()} video failed: {result.get('error')}",
        status="error"
    )
```

### Analytics Integration

Log video performance back to database:

```python
def log_video_performance(
    video_id: str,
    brand: str,
    performance_data: dict
):
    """Log views, engagement metrics."""
    
    log_entry = {
        "yt_video_id": video_id,
        "brand": brand,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "views": performance_data.get("views"),
        "likes": performance_data.get("likes"),
        "comments": performance_data.get("comments"),
        "shares": performance_data.get("shares"),
        "click_through_rate": performance_data.get("ctr")
    }
    
    # Append to analytics log
    with open(DATA_DIR / "analytics.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## Testing

### Unit Testing

Create `tests/test_orchestrator.py`:

```python
import unittest
from scripts.external_youtube_orchestrator import *

class TestOrchestrator(unittest.TestCase):
    def test_load_configs(self):
        """Test config loading."""
        brand_cfg, orch_cfg = load_configs()
        self.assertIn("revitalize", brand_cfg)
        self.assertIn("schedule", orch_cfg)
    
    def test_get_day_name(self):
        """Test day name determination."""
        day = get_day_name()
        self.assertIn(day, [
            "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday"
        ])
    
    def test_product_lookup(self):
        """Test product finding."""
        brand_cfg, _ = load_configs()
        product = get_product_by_name(
            brand_cfg, "revitalize",
            "Hormone Reset Masterclass"
        )
        self.assertIsNotNone(product)
        self.assertEqual(product["price_short"], "$59")

if __name__ == "__main__":
    unittest.main()
```

Run tests:
```bash
python3 -m unittest tests.test_orchestrator -v
```

### Integration Testing

Test with mock APIs:

```bash
# Test with mock Higgsfield (returns dummy image URL)
HIGGSFIELD_API_KEY="mock_key" \
MOCK_MODE=true \
python3 scripts/external_youtube_orchestrator.py morning

# Check logs
cat data/orchestrator-log.json | jq '.[-1]'
```

## Performance Tuning

### Optimize FFmpeg Encoding

For faster video creation, adjust FFmpeg preset:

```python
cmd = [
    "ffmpeg",
    "-preset", "ultrafast",  # faster but larger file
    # vs "fast", "medium", "slow"
    ...
]
```

Preset times:
- `ultrafast` — ~2s (largest file)
- `fast` — ~5s (recommended)
- `medium` — ~10s
- `slow` — ~15s (smallest file)

### Parallel Processing

Process multiple brands in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def process_slot(slot: str):
    # ... load config ...
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        rev_future = executor.submit(
            process_brand_for_slot,
            "revitalize", slot, ...
        )
        rec_future = executor.submit(
            process_brand_for_slot,
            "reclaim", slot, ...
        )
        
        revitalize_spec = rev_future.result()
        reclaim_spec = rec_future.result()
    
    # ... log results ...
```

### Caching

Cache downloaded images to avoid re-downloading:

```python
import hashlib

def get_cached_image(url: str, cache_dir: Path = Path("/tmp/image_cache")) -> Path:
    """Get cached image or download."""
    cache_dir.mkdir(exist_ok=True)
    
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = cache_dir / f"{url_hash}.jpg"
    
    if cache_path.exists():
        return cache_path
    
    download_image(url, str(cache_path))
    return cache_path
```

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/orchestrator_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def generate_higgsfield_image(...):
    logger.debug(f"Generating image with prompt: {prompt}")
    # ... rest of function ...
    logger.debug(f"Image URL: {image_url}")
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_orchestrator():
    profiler = cProfile.Profile()
    profiler.enable()
    
    process_slot("morning")
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20 functions
```

Run:
```bash
python3 -c "from scripts.external_youtube_orchestrator import profile_orchestrator; profile_orchestrator()"
```

## Contributing

To contribute improvements:

1. **Fork and branch** — Create feature branch from this repo
2. **Test locally** — Run `validate_orchestrator_setup.py` and manual tests
3. **Document changes** — Update this guide and ORCHESTRATOR_SETUP.md
4. **Submit PR** — Include test results and rationale

## Future Roadmap

- [ ] Direct YouTube API v3 integration (replace Composio)
- [ ] Multi-brand support (easy extensibility)
- [ ] Scheduled uploads to playlists
- [ ] Analytics dashboard
- [ ] Automatic thumbnail generation
- [ ] A/B testing framework
- [ ] Caption localization
- [ ] Audio track library
- [ ] Video preview generation
- [ ] Mobile app integration

---

**Last Updated**: September 2, 2026  
**Maintainer**: lccrichards
