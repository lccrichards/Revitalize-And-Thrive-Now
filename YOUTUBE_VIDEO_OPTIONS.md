# YouTube Video Generation Options for Reclaim & Rise

**Decision needed**: How to convert daily images into YouTube-ready videos.

---

## Option A: Generate Short Videos (Higgsfield Video Generation)

**Flow**: Image → Higgsfield video generation → YouTube upload

### How it works:
1. Generate portrait image (existing flow)
2. Use `mcp__higgsfield__generate_video` with model `kling3_0_turbo`
3. Pass image as `start_image` or `image` reference
4. Add motion/animation + caption overlay
5. Export as MP4
6. Upload to YouTube via `YOUTUBE_MULTIPART_UPLOAD_VIDEO`

### Higgsfield Video Models Available:
- **`kling3_0_turbo`** — Fast text-to-video from image + prompt (30-60 sec clips)
- **`kling3_0`** — Full video generation with motion transfer and audio support
- **`marketing_studio_video`** — Product/promotional video templates

### Example Prompt for Reclaim Evening Post:
```
Professional man, morning light, well-rested and sharp, transforms
into confident boardroom executive, closes deal by noon, energy and drive
at 8 PM. Smooth camera pan, motivational atmosphere. Text overlay:
"Complete Reclaim Reset Bundle - $249 - Rebuild Your Edge"
```

### Pros:
- ✅ Professional, engaging video content
- ✅ High production value (motion + effects)
- ✅ Captures attention in YouTube feed
- ✅ Can include audio/music
- ✅ Reusable for TikTok/Reels later

### Cons:
- ❌ Takes 30-120 seconds per video to generate (slower)
- ❌ Uses more Higgsfield credits
- ❌ Requires waiting for video processing before upload
- ❌ More complex prompt engineering

### Cost estimate:
- Image generation: ~$0.05 per image
- Video generation: ~$0.15-0.30 per 30-60 sec video
- **Total per day**: ~$0.60-0.90 for 3 video generations

---

## Option B: Simple Image-to-Video Conversion

**Flow**: Image → Static MP4 with caption/music → YouTube upload

### How it works:
1. Generate portrait image (existing flow)
2. Convert static image to MP4 using FFmpeg or simple video container
3. Add caption text overlay + background music
4. Duration: 15-30 seconds
5. Upload to YouTube via `YOUTUBE_MULTIPART_UPLOAD_VIDEO`

### Format:
```
Frame 0-15s: Static image with caption text overlay (music plays)
Frame 15-30s: Fade to product/CTA slide with pricing

MP4 Codec: H.264 (YouTube-compatible)
Resolution: 1920×1080 (YouTube standard)
Audio: Royalty-free background music track
```

### Example Video Timeline (30 sec):
```
00:00-02:00  | Fade in image
02:00-28:00  | Display image + caption overlay + background music
28:00-30:00  | Fade to CTA slide with URL + price
30:00        | End
```

### Pros:
- ✅ Fast generation (< 5 seconds per video)
- ✅ Low resource usage (minimal Higgsfield cost)
- ✅ Simple, clean, professional look
- ✅ Fully deterministic (no AI variation)
- ✅ YouTube-compliant (static image OK for education/awareness)

### Cons:
- ❌ Less engaging than motion video
- ❌ Requires external video encoding tool (FFmpeg)
- ❌ Music licensing considerations
- ❌ Not suitable for high-motion content

### Cost estimate:
- Image generation: ~$0.05 per image
- Video encoding: ~$0 (local FFmpeg, free)
- **Total per day**: ~$0.15 for 3 image generations only

---

## Hybrid Approach (Recommended)

**Combine both for maximum impact:**

- **Option A for "Hero" posts** (1-2x per week): Full motion videos for viral potential
- **Option B for regular posts** (3-4x per week): Simple, efficient image-to-video

### Implementation:
```
Monday evening (Reclaim): Option A — Full motion video (hero)
Tuesday evening: Option B — Simple image-to-video (efficient)
Wednesday evening: Option B — Simple image-to-video
Thursday evening: Option A — Full motion video (hero)
Friday evening: Option B — Simple image-to-video
Saturday evening: Option A — Full motion video (hero)
Sunday evening: Option B — Simple image-to-video
```

**Weekly cost**: ~$0.90 (3 × Option A) + $0.60 (4 × Option B) = **$1.50/week**

---

## Technical Implementation

### Option A Code (Higgsfield Video):
```python
# Step 1: Import the image we generated
image_media_id = "3d6ea145-fe11-474d-844a-8b6e03577b1c"  # from earlier

# Step 2: Generate video with motion
video_result = mcp__higgsfield__generate_video({
    "params": {
        "model": "kling3_0_turbo",
        "duration": 30,
        "medias": [
            {
                "role": "start_image",
                "value": image_media_id
            }
        ],
        "prompt": "Professional man, transformed and glowing, end-of-day calm empowerment. Smooth camera movement showing confidence and energy. Text overlay: 'Complete Reclaim Reset Bundle - $249 - Rebuild Your Edge'"
    }
})

# Step 3: Poll job status
video_job_id = video_result["results"][0]["id"]
# Poll mcp__higgsfield__job_display until status=completed

# Step 4: Extract video URL and upload to YouTube
video_url = video_result["results"]["rawUrl"]
youtube_response = YOUTUBE_MULTIPART_UPLOAD_VIDEO({
    "title": "Complete Reclaim Reset Bundle - $249",
    "description": "Rebuild your edge. Sleep recovery, testosterone optimization, strength protocol, mindset code.",
    "categoryId": "22",  # People & Blogs
    "privacyStatus": "public",
    "tags": ["wellness", "mens health", "recovery"],
    "videoFile": {
        "name": "reclaim_evening.mp4",
        "mimetype": "video/mp4",
        "s3key": video_s3_key  # from media_import_url
    }
})
```

### Option B Code (Image-to-MP4):
```bash
#!/bin/bash

# Input: image_url, caption, price, url
image_url="https://d8j0ntlcm91z4.cloudfront.net/..."
caption="Complete Reclaim Reset Bundle"
price="$249"
url="rivitalize.gumroad.com/l/nxqlwr"

# Step 1: Download image
wget -O /tmp/frame.jpg "$image_url"

# Step 2: Create video with FFmpeg
ffmpeg -loop 1 -i /tmp/frame.jpg \
  -c:v libx264 -t 30 -pix_fmt yuv420p \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  /tmp/video_temp.mp4

# Step 3: Add caption overlay + background music
ffmpeg -i /tmp/video_temp.mp4 \
  -i background_music.mp3 \
  -filter_complex "[0]drawtext=text='$caption':fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2:fontcolor=white[v]" \
  -map "[v]" -map 1:a -c:v libx264 -c:a aac \
  /tmp/output.mp4

# Step 4: Upload to YouTube
youtube_response = YOUTUBE_MULTIPART_UPLOAD_VIDEO({
    "title": caption,
    "description": f"Price: {price}\nOrder now: {url}",
    "categoryId": "22",
    "privacyStatus": "public",
    "videoFile": {
        "name": "reclaim_video.mp4",
        "mimetype": "video/mp4",
        "s3key": s3_key_from_upload
    }
})
```

---

## Recommendation

**For Reclaim & Rise on YouTube:**

1. **Start with Option B** (simple image-to-video)
   - Low cost, fast, reliable
   - Builds audience with consistent posting
   - Test YouTube algorithm acceptance

2. **After 2-3 weeks, introduce Option A**
   - Add 1-2 hero motion videos per week
   - Gauge audience response to higher production value
   - Adjust cadence based on performance

3. **Monitor metrics**
   - Click-through rates to Gumroad
   - Watch time and average view duration
   - Subscriber growth trends

---

## Decision Matrix

| Factor | Option A | Option B |
|--------|----------|----------|
| **Speed** | Slow (30-120s) | Very fast (<5s) |
| **Cost** | Higher ($0.15-0.30/video) | Lower ($0/video locally) |
| **Quality** | Professional, engaging | Clean, professional |
| **Engagement** | High (motion attracts) | Medium (static is safe) |
| **Complexity** | Medium (AI prompt tuning) | Low (deterministic) |
| **Best for** | Hero posts, viral potential | Regular cadence, efficiency |

---

## What do you choose?

1. **Option A only** — Go premium, use Higgsfield for all videos
2. **Option B only** — Keep it simple and cost-effective
3. **Hybrid** — Mix both strategies (recommended)
4. **Skip YouTube** — Stick with Instagram + Facebook only
