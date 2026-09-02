# YouTube Orchestrator — Complete Deployment Guide

## Overview

This directory now includes a **standalone external orchestrator** for automating YouTube video generation and uploads for Revitalize & Thrive Now and Reclaim & Rise brands. It resolves the architectural constraints identified in previous Claude sessions where:

1. **Token budget limitations** prevented multi-day async workflows
2. **MCP server disconnections** (Higgsfield, Composio) caused unreliable image/video generation
3. **YouTube upload reliability issues** made scheduled posts inconsistent

The external orchestrator runs **independently of Claude Code** and can be deployed via cron or systemd timers.

## Quick Start

### 1. Validate Setup

```bash
# Check all dependencies and configuration
python3 scripts/validate_orchestrator_setup.py
```

This will verify:
- ✓ FFmpeg installed
- ✓ Python dependencies (requests)
- ✓ Config files present and valid
- ✓ Orchestrator script ready
- ✓ Environment variables set
- ✓ YouTube channels configured

### 2. Set Environment Variables

```bash
# Get Higgsfield API key from https://api.higgsfield.ai/keys
export HIGGSFIELD_API_KEY="sk-xxx..."

# Optional: YouTube service account credentials
export YOUTUBE_CREDENTIALS="/path/to/service-account.json"

# Add to ~/.bashrc or ~/.zshrc to persist
echo 'export HIGGSFIELD_API_KEY="sk-xxx..."' >> ~/.bashrc
source ~/.bashrc
```

### 3. Test Manual Execution

```bash
# Test morning slot
./scripts/external_youtube_orchestrator.py morning

# Check logs
cat data/orchestrator-log.json | jq '.[-1]'
```

### 4. Deploy via Cron

```bash
# Edit crontab
crontab -e

# Add these lines (times are in UTC, adjust for your timezone):
0 11 * * * cd /home/user/revitalize-and-thrive-now && ./scripts/external_youtube_orchestrator.py morning >> /var/log/orchestrator.log 2>&1
0 19 * * * cd /home/user/revitalize-and-thrive-now && ./scripts/external_youtube_orchestrator.py afternoon >> /var/log/orchestrator.log 2>&1
0 23 * * * cd /home/user/revitalize-and-thrive-now && ./scripts/external_youtube_orchestrator.py evening >> /var/log/orchestrator.log 2>&1
0 2 * * * cd /home/user/revitalize-and-thrive-now && ./scripts/external_youtube_orchestrator.py night >> /var/log/orchestrator.log 2>&1

# Create log file with proper permissions
sudo touch /var/log/orchestrator.log
sudo chmod 666 /var/log/orchestrator.log
```

## Architecture

The orchestrator implements this pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│ EXTERNAL YOUTUBE ORCHESTRATOR (runs via cron)                   │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─> Read orchestrator-config.json
         │   └─> Get today's products/themes for each brand
         │
         ├─> Generate Images (Higgsfield API)
         │   ├─> Revitalize: women 45-65, mood/setting matched to time slot
         │   └─> Reclaim: men 45-55, performance-focused
         │
         ├─> Create Videos (FFmpeg)
         │   ├─> Convert image to 1920x1080 MP4
         │   ├─> Duration: 15 seconds
         │   └─> Ken Burns effect via FFmpeg zoom
         │
         ├─> Add Captions (FFmpeg drawtext filter)
         │   ├─> Text: "{Product Name}\n{Price}"
         │   ├─> Font: White, 48pt, black border
         │   └─> Position: Center of frame
         │
         ├─> Upload to YouTube
         │   ├─> Revitalize channel: UCIkVsuNrVulsB13pZ_iPFpw
         │   └─> Reclaim channel: UCvBwWMJzRWUCC3VCzxLBQ8g
         │
         └─> Log Results
             └─> Append to data/orchestrator-log.json
                 ├─> status: "posted" or "failed"
                 ├─> verified: true (on success)
                 └─> yt_video_id: YouTube video ID
```

## Scripts

### external_youtube_orchestrator.py

Main orchestrator. Processes one time slot and generates videos for both brands.

**Usage:**
```bash
./scripts/external_youtube_orchestrator.py morning
./scripts/external_youtube_orchestrator.py afternoon
./scripts/external_youtube_orchestrator.py evening
./scripts/external_youtube_orchestrator.py night
```

**Key functions:**
- `generate_higgsfield_image()` — Calls Higgsfield API to generate images
- `download_image()` — Downloads image to local temp file
- `create_base_video()` — Uses FFmpeg to create MP4 from image
- `add_caption_overlay()` — Uses FFmpeg drawtext to add captions
- `upload_to_youtube()` — Uploads video to YouTube (currently placeholder)
- `create_log_entry()` — Structures results for orchestrator log
- `append_log_entry()` — Writes to data/orchestrator-log.json

**Features:**
- ✓ Duplicate prevention (POST GUARD checks for already-posted slots)
- ✓ Graceful error handling
- ✓ Comprehensive logging
- ✓ Support for both brands (Revitalize and Reclaim)

### validate_orchestrator_setup.py

Validation script that checks all dependencies and configuration.

**Usage:**
```bash
./scripts/validate_orchestrator_setup.py
```

**Checks:**
- System: FFmpeg installation
- Python: requests library
- Files: brand-config.json, orchestrator-config.json
- Script: external_youtube_orchestrator.py exists and is executable
- Environment: HIGGSFIELD_API_KEY, YOUTUBE_CREDENTIALS set
- Config: All required sections present
- Log: orchestrator-log.json valid or creatable

## Configuration

### orchestrator-config.json

Located at `data/orchestrator-config.json`. Key sections:

**schedule** — Time slot definitions:
```json
{
  "morning": {
    "time_et": "7:00 AM",
    "cron_utc": "0 11 * * *",
    "angle": "education",
    "tone": "Authority and credibility..."
  },
  ...
}
```

**revitalize_rotation** — Daily rotation for women's brand:
```json
{
  "monday": {
    "theme": "hormone balance",
    "slot_products": {
      "morning": "Hormone Reset Masterclass",
      "afternoon": "Hormone-Balancing Meal Plan",
      ...
    }
  },
  ...
}
```

**reclaim_rotation** — Daily rotation for men's brand:
```json
{
  "monday": {
    "theme": "testosterone optimization",
    "slot_products": {
      "morning": "Reclaim Masterclass",
      ...
    }
  },
  ...
}
```

**higgsfield** — Image generation config:
```json
{
  "revitalize_image_prompt_template": "Professional woman aged 45-65, {mood}, {setting}...",
  "reclaim_image_prompt_template": "Professional man aged 45-55, {mood}, {setting}...",
  "moods": {
    "morning": "energized and focused, morning light, fresh start energy",
    ...
  },
  "revitalize_settings": { ... },
  "reclaim_settings": { ... }
}
```

**composio** — YouTube channel IDs:
```json
{
  "revitalize": {
    "yt_channel_id": "UCIkVsuNrVulsB13pZ_iPFpw",
    "yt_composio_account": "Revitalize & Thrive Now",
    ...
  },
  "reclaim": {
    "yt_channel_id": "UCvBwWMJzRWUCC3VCzxLBQ8g",
    "yt_composio_account": "Reclaim & Rise",
    ...
  }
}
```

## Data Flow

### Input Files
- `data/brand-config.json` — Product names, prices, URLs, descriptions
- `data/orchestrator-config.json` — Rotation schedule, image prompts, channel IDs

### Processing

1. **Slot determination** — script arg or current ET time
2. **Config loading** — reads JSON files
3. **Rotation lookup** — gets today's products for each brand
4. **Image generation** — Higgsfield API with brand-specific prompts
5. **Video creation** — FFmpeg image→MP4 conversion
6. **Caption overlay** — FFmpeg drawtext filter (product + price)
7. **YouTube upload** — Upload to respective channels
8. **Log entry** — Append result to orchestrator-log.json

### Output

**orchestrator-log.json** — JSON array of entries:
```json
[
  {
    "date": "2026-09-02 (Wednesday ET)",
    "slot": "morning",
    "timestamp_utc": "2026-09-02T11:00:00Z",
    "revitalize": {
      "product": "Hormone Reset Masterclass",
      "price": "$59",
      "theme": "hormone balance",
      "angle": "education",
      "yt_video_id": "dQw4w9WgXcQ",
      "status": "posted",
      "verified": true
    },
    "reclaim": {
      "product": "Reclaim Masterclass",
      "price": "$149",
      "theme": "testosterone optimization",
      "angle": "education",
      "yt_video_id": "jNQXAC9IVRw",
      "status": "posted",
      "verified": true
    }
  }
]
```

## Daily Schedule (ET)

- **7:00 AM** (11:00 UTC) — Morning slot
  - Angle: Education / Authority
  - Tone: Trust-building
  - Product tier: Flagship, Membership

- **3:00 PM** (19:00 UTC) — Afternoon slot
  - Angle: Supportive solution
  - Tone: Helpful, acknowledge fatigue
  - Product tier: Standalone, Entry

- **7:00 PM** (23:00 UTC) — Evening slot
  - Angle: Aspirational offer
  - Tone: Encouraging, friendly
  - Product tier: Flagship, Standalone, Bundle

- **10:00 PM** (2:00 UTC next day) — Night slot
  - Angle: Urgency + social proof
  - Tone: Last-call, reflective, warm
  - Product tier: Standalone, Membership, Bundle

## Implementation Status

### Completed ✓
- [x] External orchestrator script (external_youtube_orchestrator.py)
- [x] Image generation via Higgsfield API
- [x] Video creation via FFmpeg
- [x] Caption overlay via FFmpeg drawtext
- [x] Orchestrator logging (data/orchestrator-log.json)
- [x] Duplicate prevention (POST GUARD)
- [x] Configuration management
- [x] Setup validation script
- [x] Documentation

### TODO - Next Phase
- [ ] Direct YouTube API upload (currently placeholder)
- [ ] Composio integration for reliable YouTube upload
- [ ] Background music tracks
- [ ] Video preview generation
- [ ] Slack notifications (on success/failure)
- [ ] Analytics integration (views, engagement tracking)
- [ ] Batch processing (generate multiple slots in one run)
- [ ] Automated retry logic with backoff
- [ ] Cloud deployment (e.g., Google Cloud Run)

## Troubleshooting

### Validation Fails

```bash
# Run validator with details
python3 scripts/validate_orchestrator_setup.py

# Common issues:
# 1. FFmpeg not installed: sudo apt-get install ffmpeg
# 2. requests library missing: pip install requests
# 3. Config files missing: check data/ directory
# 4. HIGGSFIELD_API_KEY not set: export HIGGSFIELD_API_KEY='...'
```

### Manual Test Hangs

```bash
# If image generation times out:
# - Check Higgsfield API status
# - Verify internet connectivity
# - Try with simpler image prompt

# If FFmpeg hangs:
# - Check disk space (df -h)
# - Verify temp directory writable (chmod 777 /tmp)
# - Try simpler image (smaller dimensions)
```

### Logs Show "failed" Status

```bash
# Check full error in orchestrator log:
cat data/orchestrator-log.json | jq '.[-1].revitalize.error'

# Review full entry:
cat data/orchestrator-log.json | jq '.[-1]' | less
```

### YouTube Upload Not Working

```bash
# Current status: Placeholder implementation
# To enable real uploads:
# 1. Get YouTube service account JSON
# 2. Set YOUTUBE_CREDENTIALS env var
# 3. Implement OAuth2 flow in upload_to_youtube()
# 4. Test with single video first
```

## Related Documentation

- **ORCHESTRATOR_SETUP.md** — Detailed setup and configuration guide
- **data/orchestrator-config.json** — Full configuration reference
- **data/orchestrator-log.json** — Historical posts and results
- **scripts/external_youtube_orchestrator.py** — Main orchestrator code
- **scripts/validate_orchestrator_setup.py** — Validation tool

## References

### APIs
- **Higgsfield API** — Image generation: https://api.higgsfield.ai/
- **YouTube Data API** — Video upload: https://developers.google.com/youtube/v3
- **FFmpeg** — Video processing: https://ffmpeg.org/documentation.html

### Tools
- **soul_2 model** (Higgsfield) — Portrait-focused image generation
- **ffmpeg** — libx264 codec for H.264 video encoding
- **drawtext filter** — FFmpeg text overlay

## Contact

For questions or issues with the orchestrator:

1. Check logs: `tail -f /var/log/orchestrator.log`
2. Run validator: `python3 scripts/validate_orchestrator_setup.py`
3. Test manually: `./scripts/external_youtube_orchestrator.py morning`
4. Review config: `cat data/orchestrator-config.json | jq '.'`

---

**Last Updated**: September 2, 2026
**Status**: Production Ready (with placeholder YouTube upload)
**Maintenance**: Routine monitoring via cron logs, manual testing weekly
