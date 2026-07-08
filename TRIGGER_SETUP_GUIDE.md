# Persistent Trigger Setup Guide

**Status**: Automation fully tested and ready. Triggers require manual setup via Claude Project UI.

---

## Overview

Three daily triggers must be created to achieve full automation. Each trigger will:
1. Fire at a specific ET time (7 AM, 3 PM, 7 PM)
2. Spawn a fresh Claude session
3. Run the complete orchestrator flow
4. Post to both Instagram accounts
5. Log and commit results

---

## Manual Trigger Setup (Claude Project UI)

### Access Project Settings

1. Go to **claude.ai → Projects → Revitalize/Reclaim Daily Posting**
2. Click **Project Settings**
3. Navigate to **Triggers**
4. Click **Create Trigger** (repeat 3 times for each schedule)

---

## Trigger 1: Morning Post (7 AM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 7 AM ET (Morning)`
- **Schedule Type**: Cron expression (if available) OR Time-based
- **Cron Expression**: `0 11 * * *` (11 UTC = 7 AM ET)
- **Time** (alternative): `7:00 AM` with timezone `America/New_York`
- **Create new session on fire**: ✅ Yes
- **Notifications**: ✅ Email on trigger

**Prompt** (paste exactly):

```
MASTER ORCHESTRATOR — Daily Morning Post (7 AM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post morning content (7 AM ET) for Revitalize & Reclaim.

━━━ EXECUTION STEPS ━━━

1. **Determine today's slot and content:**
   cd /home/user/revitalize-and-thrive-now
   python3 scripts/master_orchestrator.py morning
   
   Output: day name, products, themes, angle (education), tone

2. **Generate captions** (Claude does this inline):
   - Revitalize: 150-200 words, warm/empowering/woman-to-woman voice
     * Hook: research stat or question (education)
     * Include 1-3 emojis, 12-15 hashtags from core + theme pools
     * Product info: name, price, URL, and bundle bonus if applicable
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: research insight or stat
     * Include 12-15 hashtags from core + theme pools
     * Product info: name, price, URL

3. **Generate images** using mcp__higgsfield__generate_image:
   - Model: nano_banana_pro
   - Aspect ratio: 1:1
   - Revitalize prompt: Use orchestrator-config.json -> higgsfield.revitalize_image_prompt_template
     * Replace {mood} with "energized and focused, morning light, fresh start energy"
     * Replace {setting} with value from higgsfield.revitalize_settings[today's theme]
     * End with: "STRICTLY WOMEN ONLY — no men in frame."
   - Reclaim prompt: Use orchestrator-config.json -> higgsfield.reclaim_image_prompt_template
     * Replace {mood} with "energized and focused, morning light, fresh start energy"
     * Replace {setting} with value from higgsfield.reclaim_settings[today's theme]
     * End with: "STRICTLY MEN ONLY — no women in frame."
   - Poll mcp__higgsfield__job_display until status = completed
   - Extract rawUrl from results

4. **Post to Instagram** via Composio (INSTAGRAM_POST_IG_USER_MEDIA → INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH):
   - Revitalize:
     * account: revitalize_thrive_now_business
     * ig_user_id: 27164026169935796
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id
   - Reclaim:
     * account: reclaim_and_rise_now
     * ig_user_id: 27634679816148097
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id

5. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[today's date, ET]",
     "slot": "morning",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "education",
       "post_id": "[published media_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "education",
       "post_id": "[published media_id]",
       "status": "posted"
     }
   }
   ```

6. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Morning post: [day] - [revitalize product] + [reclaim product]"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## Trigger 2: Afternoon Post (3 PM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 3 PM ET (Afternoon)`
- **Cron Expression**: `0 19 * * *` (19 UTC = 3 PM ET)
- **Time** (alternative): `3:00 PM` with timezone `America/New_York`
- **Create new session on fire**: ✅ Yes
- **Notifications**: ✅ Email on trigger

**Prompt** (paste exactly):

```
MASTER ORCHESTRATOR — Daily Afternoon Post (3 PM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post afternoon content (3 PM ET) for Revitalize & Reclaim.

━━━ EXECUTION STEPS ━━━

1. **Determine today's slot and content:**
   cd /home/user/revitalize-and-thrive-now
   python3 scripts/master_orchestrator.py afternoon
   
   Output: day name, products, themes, angle (pain_point), tone

2. **Generate captions** (Claude does this inline):
   - Revitalize: 150-200 words, warm/empowering/woman-to-woman voice
     * Hook: name the exact symptom/frustration at 3 PM (exhaustion, brain fog, energy crash)
     * Tone: Hit the pain precisely, then solve with product
     * Include 1-3 emojis, 12-15 hashtags from core + theme pools
     * Product info: name, price, URL, and bundle bonus if applicable
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: 3 PM exhaustion, mental fatigue, afternoon slump
     * Tone: Name it precisely, product is the direct solution
     * Include 12-15 hashtags from core + theme pools
     * Product info: name, price, URL

3. **Generate images** using mcp__higgsfield__generate_image:
   - Model: nano_banana_pro
   - Aspect ratio: 1:1
   - Revitalize prompt: Use orchestrator-config.json -> higgsfield.revitalize_image_prompt_template
     * Replace {mood} with "determined despite fatigue, mid-day resilience, purposeful"
     * Replace {setting} with value from higgsfield.revitalize_settings[today's theme]
     * End with: "STRICTLY WOMEN ONLY — no men in frame."
   - Reclaim prompt: Use orchestrator-config.json -> higgsfield.reclaim_image_prompt_template
     * Replace {mood} with "determined despite fatigue, mid-day resilience, purposeful"
     * Replace {setting} with value from higgsfield.reclaim_settings[today's theme]
     * End with: "STRICTLY MEN ONLY — no women in frame."
   - Poll mcp__higgsfield__job_display until status = completed
   - Extract rawUrl from results

4. **Post to Instagram** via Composio (INSTAGRAM_POST_IG_USER_MEDIA → INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH):
   - Revitalize:
     * account: revitalize_thrive_now_business
     * ig_user_id: 27164026169935796
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id
   - Reclaim:
     * account: reclaim_and_rise_now
     * ig_user_id: 27634679816148097
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id

5. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[today's date, ET]",
     "slot": "afternoon",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "pain_point",
       "post_id": "[published media_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "pain_point",
       "post_id": "[published media_id]",
       "status": "posted"
     }
   }
   ```

6. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Afternoon post: [day] - [revitalize product] + [reclaim product]"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## Trigger 3: Evening Post (7 PM ET)

**Settings:**
- **Name**: `Revitalize/Reclaim Daily — 7 PM ET (Evening)`
- **Cron Expression**: `0 23 * * *` (23 UTC = 7 PM ET)
- **Time** (alternative): `7:00 PM` with timezone `America/New_York`
- **Create new session on fire**: ✅ Yes
- **Notifications**: ✅ Email on trigger

**Prompt** (paste exactly):

```
MASTER ORCHESTRATOR — Daily Evening Post (7 PM ET)

Repo: /home/user/revitalize-and-thrive-now
Branch: claude/laughing-darwin-cQTwH
Configs: data/brand-config.json, data/orchestrator-config.json

TASK: Generate and post evening content (7 PM ET) for Revitalize & Reclaim.

━━━ EXECUTION STEPS ━━━

1. **Determine today's slot and content:**
   cd /home/user/revitalize-and-thrive-now
   python3 scripts/master_orchestrator.py evening
   
   Output: day name, products, themes, angle (transformation_and_cta), tone

2. **Generate captions** (Claude does this inline):
   - Revitalize: 150-200 words, warm/empowering/woman-to-woman voice
     * Hook: aspiration or before/after transformation
     * Tone: Transformation is possible, urgency, specific price, full URL
     * Include 1-3 emojis, 12-15 hashtags from core + theme pools
     * CRITICAL: Mention bundle bonus if product has one (e.g., "Order today and the Energy Restoration Guide ($29 value) is yours FREE")
     * Product info: name, price, URL
   - Reclaim: 120-150 words, direct/peer-to-peer voice
     * Hook: before/after performance narrative (e.g., "6 weeks ago he was running on 4 hours of sleep...")
     * Tone: Urgency through logic, specific price, full URL, conversion focus
     * Include 12-15 hashtags from core + theme pools
     * Product info: name, price, URL

3. **Generate images** using mcp__higgsfield__generate_image:
   - Model: nano_banana_pro
   - Aspect ratio: 1:1
   - Revitalize prompt: Use orchestrator-config.json -> higgsfield.revitalize_image_prompt_template
     * Replace {mood} with "transformed and glowing, relaxed confidence, end-of-day calm empowerment"
     * Replace {setting} with value from higgsfield.revitalize_settings[today's theme]
     * End with: "STRICTLY WOMEN ONLY — no men in frame."
   - Reclaim prompt: Use orchestrator-config.json -> higgsfield.reclaim_image_prompt_template
     * Replace {mood} with "transformed and glowing, relaxed confidence, end-of-day calm empowerment"
     * Replace {setting} with value from higgsfield.reclaim_settings[today's theme]
     * End with: "STRICTLY MEN ONLY — no women in frame."
   - Poll mcp__higgsfield__job_display until status = completed
   - Extract rawUrl from results

4. **Post to Instagram** via Composio (INSTAGRAM_POST_IG_USER_MEDIA → INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH):
   - Revitalize:
     * account: revitalize_thrive_now_business
     * ig_user_id: 27164026169935796
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id
   - Reclaim:
     * account: reclaim_and_rise_now
     * ig_user_id: 27634679816148097
     * image_url: [rawUrl from step 3]
     * caption: [caption from step 2]
     * Create container, then publish
     * Capture published media_id

5. **Log results** to data/orchestrator-log.json:
   ```json
   {
     "date": "[today's date, ET]",
     "slot": "evening",
     "revitalize": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "transformation_and_cta",
       "post_id": "[published media_id]",
       "status": "posted"
     },
     "reclaim": {
       "product": "[product name]",
       "price": "[price]",
       "theme": "[today's theme]",
       "angle": "transformation_and_cta",
       "post_id": "[published media_id]",
       "status": "posted"
     }
   }
   ```

6. **Commit and push**:
   ```bash
   git add -A
   git commit -m "Evening post: [day] - [revitalize product] + [reclaim product]"
   git push -u origin claude/laughing-darwin-cQTwH
   ```
```

---

## ✅ What's Ready

- **Timezone fix**: ✅ UTC → ET (get_day_name, get_time_slot)
- **Configs**: ✅ brand-config.json, orchestrator-config.json
- **Image generation**: ✅ Higgsfield tested (both brands, evening slot)
- **Instagram posting**: ✅ Composio tested (both accounts ACTIVE, posts live)
- **Logging**: ✅ orchestrator-log.json initialized with first entry
- **Git history**: ✅ Clean commit trail, all changes pushed

## 🚀 After Triggers Are Set Up

Once the three triggers are created in your Claude Project:

1. They will fire automatically at 7 AM, 3 PM, and 7 PM ET daily
2. Each spawns a fresh session with the orchestrator prompt
3. Full automation runs: caption generation → image creation → Instagram posting → logging
4. Results logged to data/orchestrator-log.json (rolling 90-day window)
5. All changes committed and pushed to `claude/laughing-darwin-cQTwH`

**Result**: 6 Instagram posts per day (3 × 2 brands), fully automated, timezone-aware, fully logged.

---

## Verification

After creating triggers, verify by:

1. Checking Project Settings → Triggers (should show 3 active triggers)
2. Waiting for first trigger fire (7 AM ET tomorrow)
3. Checking repo for new log entry in data/orchestrator-log.json
4. Verifying new post on both Instagram accounts

---

## Troubleshooting

**If a trigger fails to fire:**
- Check Project → Triggers (status should be "Active")
- Verify Composio + Higgsfield connectors are enabled in Project Settings → Connectors
- Check repository branch is still `claude/laughing-darwin-cQTwH`

**If post doesn't appear:**
- Check Instagram account status (should be ACTIVE in Composio connection settings)
- Verify image generation completed (poll job_display in logs)
- Ensure caption and image URL are provided to INSTAGRAM_POST_IG_USER_MEDIA

**If logging fails:**
- Verify data/orchestrator-log.json exists and is valid JSON
- Check git credentials/permissions for push
