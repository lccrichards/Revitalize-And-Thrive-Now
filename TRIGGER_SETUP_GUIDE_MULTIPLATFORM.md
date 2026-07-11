# Multi-Platform Trigger Setup Guide (Instagram + Facebook + YouTube)

**Status**: Extended automation ready for deployment. Includes Instagram, Facebook, and YouTube posting.

**Updated**: July 8, 2026

---

## Overview

Three daily triggers (7 AM, 3 PM, 7 PM ET) will:
1. Spawn fresh Claude sessions
2. Generate on-brand captions for both brands
3. Generate Higgsfield portrait images (women for Revitalize, men for Reclaim)
4. Post to Instagram and Facebook simultaneously (cross-post)
5. Generate and post YouTube videos (Reclaim only, evening slot)
6. Log all post IDs and results
7. Commit and push to branch

---

## Platform Strategy

| Platform | Revitalize | Reclaim | Timing |
|----------|-----------|--------|--------|
| Instagram | ✅ All slots | ✅ All slots | Immediate |
| Facebook | ✅ All slots | ❌ None | Immediate |
| YouTube | ❌ None | ✅ Evening only | Evening (7 PM ET) |

---

## Trigger Setup Instructions

### Access Project Settings

1. Go to **claude.ai → Projects → Revitalize/Reclaim Daily Posting**
2. Click **Project Settings**
3. Navigate to **Triggers**
4. Click **Create Trigger** (3 times, one per schedule)

---

## Trigger 1: Morning Post (7 AM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 7 AM ET (Morning)`
- **Cron Expression**: `0 11 * * *` (11 UTC = 7 AM ET)
- **Create new session**: ✅ Yes
- **Notifications**: ✅ Email on trigger

**Prompt:**

```
MASTER ORCHESTRATOR — Morning Post (7 AM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post morning content to Instagram + Facebook.

━━━ EXECUTION STEPS ━━━

1. **Determine today's schedule:**
   cd /home/user/revitalize-and-thrive-now
   python3 scripts/master_orchestrator.py morning
   
   Output: day, products, themes, angle (education), tone

2. **Generate captions** (inline):
   - Revitalize: 150-200 words, warm/woman-to-woman voice
     * Hook: research stat or question
     * 1-3 emojis, 12-15 hashtags, product price/URL
     * If product has bundle bonus, mention it
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: research insight
     * 12-15 hashtags, product price/URL

3. **Generate images** via mcp__higgsfield__generate_image:
   - Model: nano_banana_pro, Aspect: 1:1
   - Revitalize:
     * Prompt template: "Professional woman aged 45-65, energized and focused, morning light, fresh start energy, {setting}, radiant expression, wellness lifestyle, clean composition. STRICTLY WOMEN ONLY — no men in frame."
     * Replace {setting} from orchestrator-config.json higgsfield.revitalize_settings[theme]
   - Reclaim:
     * Prompt template: "Professional man aged 45-55, energized and focused, morning light, fresh start energy, {setting}, sharp expression, high-performance lifestyle. STRICTLY MEN ONLY — no women in frame."
     * Replace {setting} from orchestrator-config.json higgsfield.reclaim_settings[theme]
   - Poll job_display until status = completed
   - Extract rawUrl from results

4. **Post to Instagram** via Composio:
   - Revitalize:
     * Tool: INSTAGRAM_POST_IG_USER_MEDIA
     * account: revitalize_thrive_now_business
     * ig_user_id: 27164026169935796
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Call INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH with creation_id
     * Capture published media_id → ig_post_id
   - Reclaim:
     * account: reclaim_and_rise_now
     * ig_user_id: 27634679816148097
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Capture published media_id → ig_post_id

5. **Post to Facebook** (Revitalize only) via Composio:
   - Tool: FACEBOOK_CREATE_PHOTO_POST
   - page_id: 130419383084779
   - account_id: revitalize_thrive_now_business
   - image_url: [rawUrl from Revitalize image generation]
   - message: [caption from step 2]
   - Capture post_id → fb_post_id

6. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[YYYY-MM-DD ET]",
     "slot": "morning",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "education",
       "ig_post_id": "[instagram media_id]",
       "fb_post_id": "[facebook post_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "education",
       "ig_post_id": "[instagram media_id]",
       "status": "posted"
     }
   }
   ```

7. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Morning post: [day] - Revitalize + Reclaim (IG + FB)"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## Trigger 2: Afternoon Post (3 PM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 3 PM ET (Afternoon)`
- **Cron Expression**: `0 19 * * *` (19 UTC = 3 PM ET)
- **Create new session**: ✅ Yes

**Prompt:**

```
MASTER ORCHESTRATOR — Afternoon Post (3 PM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post afternoon content to Instagram + Facebook.

━━━ EXECUTION STEPS ━━━

1. **Determine today's schedule:**
   python3 scripts/master_orchestrator.py afternoon
   
   Output: day, products, themes, angle (pain_point), tone

2. **Generate captions** (inline):
   - Revitalize: 150-200 words, warm/woman-to-woman voice
     * Hook: name the exact 3 PM pain (exhaustion, brain fog, energy crash)
     * Hit the pain precisely, then solve with product
     * 1-3 emojis, 12-15 hashtags, product price/URL
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: 3 PM exhaustion, mental fatigue, afternoon slump
     * Name it precisely, product is the direct solution
     * 12-15 hashtags, product price/URL

3. **Generate images** via mcp__higgsfield__generate_image:
   - Model: nano_banana_pro, Aspect: 1:1
   - Revitalize:
     * Prompt: "Professional woman aged 45-65, determined despite fatigue, mid-day resilience, purposeful, {setting}, confident expression, wellness lifestyle. STRICTLY WOMEN ONLY — no men in frame."
     * Replace {setting} from orchestrator-config.json
   - Reclaim:
     * Prompt: "Professional man aged 45-55, determined despite fatigue, mid-day resilience, purposeful, {setting}, focused expression, high-performance lifestyle. STRICTLY MEN ONLY — no women in frame."
     * Poll job_display until status = completed
     * Extract rawUrl

4. **Post to Instagram** (same as morning trigger):
   - Revitalize: INSTAGRAM_POST_IG_USER_MEDIA + PUBLISH
   - Reclaim: INSTAGRAM_POST_IG_USER_MEDIA + PUBLISH
   - Capture both media_ids

5. **Post to Facebook** (Revitalize only):
   - FACEBOOK_CREATE_PHOTO_POST with afternoon caption
   - Capture post_id

6. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[YYYY-MM-DD ET]",
     "slot": "afternoon",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "pain_point",
       "ig_post_id": "[instagram media_id]",
       "fb_post_id": "[facebook post_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "pain_point",
       "ig_post_id": "[instagram media_id]",
       "status": "posted"
     }
   }
   ```

7. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Afternoon post: [day] - Revitalize + Reclaim (IG + FB)"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## Trigger 3: Evening Post (7 PM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 7 PM ET (Evening)`
- **Cron Expression**: `0 23 * * *` (23 UTC = 7 PM ET)
- **Create new session**: ✅ Yes

**Prompt:**

```
MASTER ORCHESTRATOR — Evening Post (7 PM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post evening content to Instagram + Facebook + YouTube.

━━━ EXECUTION STEPS ━━━

1. **Determine today's schedule:**
   python3 scripts/master_orchestrator.py evening
   
   Output: day, products, themes, angle (transformation_and_cta), tone

2. **Generate captions** (inline):
   - Revitalize: 150-200 words, warm/woman-to-woman voice
     * Hook: aspiration or before/after transformation
     * Tone: Transformation is possible, urgency, specific price, full URL
     * 1-3 emojis, 12-15 hashtags, product price/URL
     * CRITICAL: If product has bundle bonus, mention it (e.g., "Order today and receive the Energy Restoration Guide (FREE)")
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: before/after performance narrative
     * Tone: Urgency through logic, specific price, full URL, conversion focus
     * 12-15 hashtags, product price/URL

3. **Generate images** via mcp__higgsfield__generate_image:
   - Model: nano_banana_pro, Aspect: 1:1
   - Revitalize:
     * Prompt: "Professional woman aged 45-65, transformed and glowing, relaxed confidence, end-of-day calm empowerment, {setting}, radiant and peaceful expression, wellness lifestyle. STRICTLY WOMEN ONLY — no men in frame."
   - Reclaim:
     * Prompt: "Professional man aged 45-55, transformed and glowing, relaxed confidence, end-of-day calm empowerment, {setting}, composed and accomplished expression, high-performance lifestyle. STRICTLY MEN ONLY — no women in frame."
   - Poll job_display until status = completed
   - Extract rawUrl for both

4. **Post to Instagram**:
   - Revitalize: INSTAGRAM_POST_IG_USER_MEDIA + PUBLISH (capture ig_post_id)
   - Reclaim: INSTAGRAM_POST_IG_USER_MEDIA + PUBLISH (capture ig_post_id)

5. **Post to Facebook** (Revitalize only):
   - FACEBOOK_CREATE_PHOTO_POST with evening caption
   - Capture fb_post_id

6. **Generate and post YouTube video** (Reclaim only):
   - Use OPTION B: FFmpeg static image-to-video conversion
   - Download Reclaim image to /tmp/reclaim_video.jpg
   - Create MP4 using FFmpeg:
     * Duration: 30 seconds
     * Resolution: 1920×1080
     * Add caption overlay: Product name + price at center
     * Add royalty-free background music (wellness/motivational track)
     * Codec: libx264, format: MP4
   - Generated video path: /tmp/reclaim_video_final.mp4
   - Upload to YouTube via youtube.videos.insert:
     * title: "[Product Name] - Complete System for [Theme]"
     * description: "[Reclaim caption from step 2]\n\nOrder now: [product URL]\nPrice: [price]"
     * categoryId: "22" (People & Blogs)
     * privacyStatus: "public"
     * tags: ["wellness", "mens health", "reclaim", "sleep", "testosterone", "recovery"]
   - Capture youtube_video_id from response

7. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[YYYY-MM-DD ET]",
     "slot": "evening",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "transformation_and_cta",
       "ig_post_id": "[instagram media_id]",
       "fb_post_id": "[facebook post_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[theme]",
       "angle": "transformation_and_cta",
       "ig_post_id": "[instagram media_id]",
       "yt_video_id": "[youtube video id]",
       "status": "posted"
     }
   }
   ```

8. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Evening post: [day] - Revitalize (IG + FB) + Reclaim (IG + YT)"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## Daily Post Summary

**7 AM ET (Morning)**
- Revitalize: Instagram + Facebook
- Reclaim: Instagram
- Focus: Education, authority, trust-building

**3 PM ET (Afternoon)**
- Revitalize: Instagram + Facebook
- Reclaim: Instagram
- Focus: Pain point awareness, immediate relevance

**7 PM ET (Evening)**
- Revitalize: Instagram + Facebook
- Reclaim: Instagram + YouTube
- Focus: Transformation, urgency, conversion

**Weekly Volume**
- Instagram: 6 posts/day (3 slots × 2 brands)
- Facebook: 3 posts/day (3 slots × Revitalize only)
- YouTube: 1 video/day (7 PM Reclaim slot only)
- **Total: 10 posts/day across all platforms**

---

## Setup Verification Checklist

- [ ] Trigger 1 (7 AM ET) created and active
- [ ] Trigger 2 (3 PM ET) created and active
- [ ] Trigger 3 (7 PM ET) created and active
- [ ] Instagram accounts connected (both ACTIVE)
- [ ] Facebook account connected for Revitalize
- [ ] YouTube channel configured for Reclaim
- [ ] Higgsfield image generation tested
- [ ] First trigger fires at scheduled time
- [ ] Log entry appears in data/orchestrator-log.json
- [ ] Posts visible on Instagram (both accounts)
- [ ] Posts visible on Facebook (Revitalize)
- [ ] Video uploaded to YouTube (Reclaim evening slot)

---

## Troubleshooting

**Trigger doesn't fire:**
- Check Project Settings → Triggers (status should be "Active")
- Verify Composio + Higgsfield connectors enabled
- Check repository branch is `claude/laughing-darwin-cQTwH`

**Instagram post fails:**
- Verify account status (ACTIVE in Composio)
- Check image generation completed (job_display status = completed)
- Ensure caption and image URL provided to tool

**Facebook post fails:**
- Check Revitalize Facebook page is connected
- Verify page_id in orchestrator-config.json matches connected account
- Test posting manually via Composio workbench

**YouTube video upload fails:**
- Verify YouTube API credentials in Claude Project
- Check video file generated correctly (ffmpeg output)
- Ensure video duration is 30 seconds (YouTube minimum 15s, but 30s recommended)
- Check video resolution is 1920×1080 (standard YouTube)

---

## Post-Launch Monitoring

After triggers are live, monitor:
1. **Posting Cadence**: 3 posts per day on time
2. **Image Quality**: Consistent portrait generation
3. **Caption Quality**: Relevant to time slot and brand voice
4. **Post IDs Logged**: Each platform's post ID captured correctly
5. **Engagement**: Cross-check Instagram, Facebook, YouTube analytics weekly

---

## Next Steps

1. Create all three triggers in Claude Project UI (use prompts above)
2. Wait for first trigger fire (7 AM ET tomorrow)
3. Verify posts appear on Instagram, Facebook, YouTube
4. Monitor logs in data/orchestrator-log.json
5. Adjust caption or image generation prompts based on early results
