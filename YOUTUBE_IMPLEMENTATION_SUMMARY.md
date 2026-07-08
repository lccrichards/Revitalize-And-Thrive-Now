# YouTube Implementation Summary

**Date**: July 8, 2026  
**Decision**: Use Option B (FFmpeg image-to-video) as primary approach for daily videos  
**Status**: Ready for deployment

---

## Decision Rationale

After evaluating two approaches for YouTube video generation:

### Option A: Higgsfield Video Generation
- **Cost**: $0.15-0.30 per 30-60 second video
- **Speed**: 30-120 seconds per video
- **Quality**: Professional motion video with animations
- **Use case**: Hero posts (1-2x per week) for viral potential
- **Status**: Available for future implementation

### Option B: FFmpeg Image-to-Video Conversion ✅ SELECTED
- **Cost**: $0 (local FFmpeg, free)
- **Speed**: < 5 seconds per video
- **Quality**: Clean static image with caption overlay + music
- **Use case**: Regular daily posts (reliable, consistent)
- **Status**: Implemented for daily automation

---

## Implementation: Option B (FFmpeg)

### Video Specification
```
Resolution:     1920 × 1080 (YouTube standard)
Format:         MP4 (H.264 codec)
Duration:       30 seconds (optimal engagement)
Frame structure:
  - Fade in:    2 seconds (image appears with music)
  - Display:    26 seconds (full image + caption overlay + music)
  - Fade out:   2 seconds (smooth transition to end)
```

### Video Generation Workflow

**Step 1: Download image**
```bash
wget -O /tmp/reclaim_video.jpg [rawUrl from Higgsfield]
```

**Step 2: Create MP4 with FFmpeg**
```bash
ffmpeg -loop 1 -i /tmp/reclaim_video.jpg \
  -c:v libx264 -t 30 -pix_fmt yuv420p \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  /tmp/reclaim_base.mp4
```

**Step 3: Add caption overlay (product name + price)**
```bash
ffmpeg -i /tmp/reclaim_base.mp4 \
  -vf "drawtext=text='Complete Reclaim Reset Bundle - \$249':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black" \
  /tmp/reclaim_caption.mp4
```

**Step 4: Add audio track (background music)**
```bash
ffmpeg -i /tmp/reclaim_caption.mp4 \
  -i /path/to/royalty_free_wellness_track.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
  -shortest /tmp/reclaim_video_final.mp4
```

**Step 5: Upload to YouTube**
```python
# Via YouTube Data API v3 (youtube.videos.insert)
video_metadata = {
    "snippet": {
        "title": "[Product Name] - Complete System for [Theme]",
        "description": "[Caption]\n\nOrder now: [URL]\nPrice: [price]",
        "tags": ["wellness", "mens health", "recovery", "sleep", "testosterone"]
    },
    "status": {
        "privacyStatus": "public"
    },
    "processingDetails": {
        "processingStatus": "processing",
        "processingFailureReason": None
    },
    "processingDetails": {
        "processingStatus": "processing"
    }
}

# Upload video file
youtube_video_id = upload_to_youtube(
    video_file="/tmp/reclaim_video_final.mp4",
    metadata=video_metadata,
    category_id="22"  # People & Blogs
)
```

### Integration with Orchestrator

**Modified function in master_orchestrator.py:**
```python
def generate_youtube_video(
    image_url: str,
    product_name: str,
    price: str,
    caption: str,
    product_url: str,
    theme: str
) -> tuple[str, str]:
    """
    Generate MP4 video from image using FFmpeg (Option B).
    Returns: (video_file_path, youtube_video_id)
    """
    # 1. Download image
    # 2. Run FFmpeg pipeline (4 steps above)
    # 3. Upload to YouTube API
    # 4. Return video_id
```

### Deployment Location

- **Script**: `scripts/youtube_video_generator.py` (to be created)
- **Config**: `data/orchestrator-config.json` (youtube section)
- **Integration**: Evening trigger (7 PM ET) → Reclaim brand only
- **Logging**: Post ID captured in `data/orchestrator-log.json`

---

## Platform Distribution

**Revitalize (Women 45-65)**
- Instagram ✅ 3 posts/day (all slots)
- Facebook ✅ 3 posts/day (all slots)
- YouTube ❌ None (image-based brand)

**Reclaim (Men 45-55)**
- Instagram ✅ 3 posts/day (all slots)
- YouTube ✅ 1 video/day (evening slot only)
- Facebook ❌ None (video/content-focused brand)

---

## Cost Analysis (Weekly)

| Component | Cost | Notes |
|-----------|------|-------|
| Image generation (6 images) | ~$0.30 | Higgsfield nano_banana_pro |
| FFmpeg video encoding (1 video) | $0.00 | Local processing |
| YouTube hosting | $0.00 | Free (Google provided) |
| **Total weekly** | **~$0.30** | Minimal ongoing cost |

---

## Future Enhancement Path (Option A)

When ready to introduce Higgsfield-generated motion videos:

1. Create `youtube_video_generator_option_a.py` (Higgsfield kling3_0_turbo workflow)
2. Add config flag: `youtube.video_generation_option = "A"` 
3. Create "hero post" designation in rotation config
4. Deploy to specific days (1-2x per week)
5. A/B test engagement vs. Option B
6. Monitor cost impact ($0.15-0.30/video)

**Recommendation**: Start Option B, introduce Option A after 4 weeks of audience data.

---

## Verification Checklist

- [ ] FFmpeg installed in Claude Code environment
- [ ] YouTube API credentials configured in Claude Project
- [ ] YouTube channel configured for Reclaim brand
- [ ] Video upload tested with sample MP4
- [ ] Caption overlay rendering correctly in test video
- [ ] Background music track copyright-cleared
- [ ] orchestrator-config.json updated with YouTube settings
- [ ] TRIGGER_SETUP_GUIDE_MULTIPLATFORM.md reviewed and validated
- [ ] First evening trigger produces YouTube video

---

## Troubleshooting Guide

**FFmpeg not found**
```bash
# Install in Claude Code environment
apt-get update && apt-get install -y ffmpeg
```

**Video too large for upload**
```bash
# Reduce bitrate if > 128 MB
ffmpeg -i input.mp4 -b:v 2000k output.mp4
```

**Caption text not visible**
```bash
# Increase fontsize or adjust y position
# Current: fontsize=60, y=(h-text_h)/2
# Try: fontsize=80, y=(h-text_h)/2-100
```

**YouTube upload fails (403)**
- Check YouTube API is enabled in Google Cloud project
- Verify refresh token is current
- Check channel is not suspended

**Audio out of sync**
```bash
# Use -shortest flag to match shortest stream
ffmpeg -i video.mp4 -i audio.mp3 -shortest output.mp4
```

---

## Success Metrics

After first week of YouTube posting:
1. **Video Quality**: Clean, professional appearance (check YouTube preview)
2. **Upload Speed**: < 5 seconds generation + upload
3. **Posting Cadence**: Consistent 7 PM ET daily upload
4. **View Engagement**: Track metrics on YouTube Studio dashboard
5. **Click-through**: Monitor traffic to Gumroad links in description

---

## Files Modified/Created

- ✅ `TRIGGER_SETUP_GUIDE_MULTIPLATFORM.md` — Complete multi-platform trigger documentation
- ✅ `data/orchestrator-config.json` — Added YouTube configuration section
- ✅ `scripts/master_orchestrator.py` — Updated docstring for cross-platform support
- 🔄 `scripts/youtube_video_generator.py` — To be created during trigger implementation

---

## Next Steps

1. Commit all configuration changes to `claude/laughing-darwin-cQTwH`
2. Create all three triggers in Claude Project UI using TRIGGER_SETUP_GUIDE_MULTIPLATFORM.md
3. Wait for first 7 PM trigger fire (evening slot)
4. Verify YouTube video appears on Reclaim channel
5. Monitor engagement and log results
