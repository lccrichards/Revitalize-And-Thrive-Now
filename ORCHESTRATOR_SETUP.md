# External YouTube Orchestrator Setup Guide

## Overview

The external YouTube orchestrator is a standalone Python script that automates video generation and YouTube upload for the Revitalize & Thrive Now and Reclaim & Rise brands. It runs independently of Claude Code sessions and can be scheduled via cron.

## Architecture

The orchestrator follows this pipeline:

1. **Daily Content Specs**: Calls `master_orchestrator.py` to get product/theme for the day/slot
2. **Image Generation**: Calls Higgsfield API directly to generate brand-specific images
3. **Video Creation**: Creates MP4 videos from images using FFmpeg
4. **Caption Overlay**: Adds product name and price as text overlay
5. **YouTube Upload**: Uploads to respective YouTube channels (via Composio or direct API)
6. **Logging**: Records results in `data/orchestrator-log.json`

## Prerequisites

### System Dependencies

```bash
# Install FFmpeg (required for video creation)
sudo apt-get update
sudo apt-get install -y ffmpeg

# Verify installation
ffmpeg -version
```

### Python Dependencies

```bash
pip install requests
```

### API Credentials

The orchestrator requires two environment variables:

#### 1. Higgsfield API Key

```bash
export HIGGSFIELD_API_KEY="your-higgsfield-api-key-here"
```

Get your key from: https://api.higgsfield.ai/keys

#### 2. YouTube API Credentials

For direct YouTube uploads, create a service account:

```bash
export YOUTUBE_CREDENTIALS="/path/to/youtube-service-account.json"
```

**Steps to create service account:**
1. Go to Google Cloud Console
2. Create a new project
3. Enable YouTube Data API v3
4. Create a Service Account
5. Generate a JSON key file
6. Add the service account as channel manager for both YouTube channels

## Installation

1. **Copy the script** (already done):
```bash
scripts/external_youtube_orchestrator.py
```

2. **Make it executable**:
```bash
chmod +x scripts/external_youtube_orchestrator.py
```

3. **Set up environment variables** in your shell profile:
```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export HIGGSFIELD_API_KEY="your-key"
export YOUTUBE_CREDENTIALS="/path/to/service-account.json"
```

## Usage

### Manual Execution

```bash
# Run for morning slot
./scripts/external_youtube_orchestrator.py morning

# Run for afternoon slot
./scripts/external_youtube_orchestrator.py afternoon

# Run for evening slot
./scripts/external_youtube_orchestrator.py evening

# Run for night slot
./scripts/external_youtube_orchestrator.py night
```

### Cron Job Setup

Add these lines to your crontab (`crontab -e`):

```bash
# Revitalize & Thrive Now + Reclaim & Rise YouTube Orchestrator
# Times are in UTC. Adjust to your timezone as needed.

# Morning: 7 AM ET = 11 UTC
0 11 * * * cd /home/user/revitalize-and-thrive-now && /home/user/revitalize-and-thrive-now/scripts/external_youtube_orchestrator.py morning >> /var/log/orchestrator.log 2>&1

# Afternoon: 3 PM ET = 19 UTC  
0 19 * * * cd /home/user/revitalize-and-thrive-now && /home/user/revitalize-and-thrive-now/scripts/external_youtube_orchestrator.py afternoon >> /var/log/orchestrator.log 2>&1

# Evening: 7 PM ET = 23 UTC
0 23 * * * cd /home/user/revitalize-and-thrive-now && /home/user/revitalize-and-thrive-now/scripts/external_youtube_orchestrator.py evening >> /var/log/orchestrator.log 2>&1

# Night: 10 PM ET = 2 UTC (next day)
0 2 * * * cd /home/user/revitalize-and-thrive-now && /home/user/revitalize-and-thrive-now/scripts/external_youtube_orchestrator.py night >> /var/log/orchestrator.log 2>&1
```

Make sure the log directory is writable:
```bash
sudo touch /var/log/orchestrator.log
sudo chmod 666 /var/log/orchestrator.log
```

## Configuration

The orchestrator reads from these config files:

- `data/brand-config.json` — Product names, prices, URLs, brand voice
- `data/orchestrator-config.json` — Rotation schedule, themes, Higgsfield prompts, YouTube channel IDs
- `data/orchestrator-log.json` — Running log of all posts (created/updated by orchestrator)

### Key Config Sections

**orchestrator-config.json**:
- `schedule` — Time slot settings (angle, tone, product tiers)
- `revitalize_rotation` — Daily product rotation for women's brand
- `reclaim_rotation` — Daily product rotation for men's brand
- `higgsfield` — Image prompt templates and mood descriptions
- `composio` — YouTube channel IDs and account info

## Workflow

### Duplicate Prevention

The orchestrator includes a POST GUARD that prevents duplicate posts:

1. Before processing a slot, checks if that slot already has a verified post for today's date (ET)
2. If found, skips the run with a message
3. This prevents accidental duplicate posts if cron runs twice or is restarted

### Image Generation

Images are generated via Higgsfield's `soul_2` model with:
- 1:1 aspect ratio
- 2K quality
- Brand-specific prompts (women 45-65 for Revitalize, men 45-55 for Reclaim)
- Dynamic mood/setting based on time slot

### Video Creation

Each video is:
- 15 seconds long (conforming to YouTube Shorts format)
- 1920x1080 resolution
- Static image with ken burns effect (via FFmpeg zoom filter)
- Caption overlay: `{Product Name}\n{Price}`
- No audio (optional — can add via FFmpeg)

### YouTube Upload

Currently a placeholder implementation. To enable live uploads:

1. Uncomment the actual YouTube API call in `upload_to_youtube()`
2. Set up proper OAuth2 flow with service account
3. Configure upload settings (title, description, tags, playlist)

## Logging

All operations are logged to `data/orchestrator-log.json` with entries containing:

```json
{
  "date": "2026-09-02 (Wednesday ET)",
  "slot": "morning",
  "timestamp_utc": "2026-09-02T11:00:00Z",
  "revitalize": {
    "product": "Hormone Reset Masterclass",
    "price": "$59",
    "theme": "hormone balance",
    "angle": "education",
    "yt_video_id": "actual_youtube_video_id",
    "status": "posted",
    "verified": true
  },
  "reclaim": {
    "product": "Reclaim Masterclass",
    "price": "$149",
    "theme": "testosterone optimization",
    "angle": "education",
    "yt_video_id": "actual_youtube_video_id",
    "status": "posted",
    "verified": true
  }
}
```

Status values:
- `pending` — Processing started
- `posted` — Successfully uploaded to YouTube
- `failed` — Encountered an error
- `verified` — Post confirmed live on YouTube

## Troubleshooting

### FFmpeg Not Found

```
ERROR: FFmpeg not found. Install FFmpeg to use this orchestrator.
```

**Solution**: Install FFmpeg (see Prerequisites section)

### Higgsfield API Key Error

```
ERROR: HIGGSFIELD_API_KEY environment variable not set
```

**Solution**: Set the environment variable:
```bash
export HIGGSFIELD_API_KEY="your-key"
```

### Image Generation Timeout

```
Image generation timeout
```

**Possible causes**:
- Higgsfield API is slow or rate-limited
- Network connectivity issue
- Invalid prompt text

**Solution**: 
- Check Higgsfield status page
- Verify network connectivity
- Review prompt in logs

### Video Generation Fails

```
Failed to create base video
ERROR: FFmpeg error: ...
```

**Possible causes**:
- FFmpeg version incompatibility
- Corrupted downloaded image
- Insufficient disk space

**Solution**:
- Update FFmpeg: `sudo apt-get upgrade ffmpeg`
- Check `/tmp` disk space: `df -h /tmp`
- Review FFmpeg error message

### YouTube Upload Fails

```
ERROR: YouTube upload failed
```

**Solution**:
- Verify service account has channel manager role
- Check YouTube API is enabled in Google Cloud
- Verify channel IDs in config are correct
- Check rate limits (YouTube API has per-minute limits)

## Monitoring

Check the orchestrator log file:

```bash
# View latest log entries
tail -f /var/log/orchestrator.log

# View orchestrator database
cat data/orchestrator-log.json | jq '.[-5:]'  # Last 5 entries

# Check if today's morning post succeeded
grep "morning" data/orchestrator-log.json | tail -1 | jq '.'
```

## Performance Considerations

Typical runtimes (per slot):

- Image generation: 30-60 seconds (depends on Higgsfield API)
- Video creation: 10-15 seconds (FFmpeg)
- YouTube upload: 20-30 seconds
- **Total per slot: ~2-3 minutes**

## Future Enhancements

1. **Direct YouTube API integration** — Replace Composio with YouTube Data API v3
2. **Audio tracks** — Add royalty-free background music to videos
3. **Analytics** — Log video performance (views, engagement) back to database
4. **Caption customization** — Support multi-line captions with product URL
5. **Batch processing** — Generate multiple slots in one run
6. **Slack notifications** — Alert on successes/failures
7. **Retry logic** — Auto-retry failed uploads with backoff

## Support

For issues or questions:

1. Check logs: `/var/log/orchestrator.log`
2. Review config: `data/orchestrator-config.json`
3. Test manually: `./scripts/external_youtube_orchestrator.py morning`
4. Check API status: Higgsfield, YouTube, Composio dashboards
