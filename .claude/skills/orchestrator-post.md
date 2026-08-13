# Orchestrator Content Post Skill

**Description:** Automated content generation and publishing for Revitalize & Thrive Now and Reclaim & Rise Instagram/Facebook/YouTube routines with approval gate.

**Author:** Claude Code  
**Category:** Marketing Automation  
**Trigger:** Scheduled (7 AM, 3 PM, 7 PM, 10 PM ET) or manual invocation

---

## Parameters

- `slot` (required): One of `morning`, `afternoon`, `evening`, `night`
- `brand` (optional): One of `revitalize`, `reclaim`, or `both` (default: `both`)
- `date` (optional): YYYY-MM-DD in ET timezone (default: today)
- `dry_run` (optional): `true` to preview without posting (default: `false`)

---

## Workflow Steps

### 1. **Pre-flight Check**
```
Load orchestrator-config.json and brand-config.json
Check orchestrator-log.json for "ALREADY POSTED TODAY" guard
If guard exists for this slot + brand today → ABORT and report
```

**Tools:** Read files from `/data/`

---

### 2. **Determine Content**
```
Given slot and brand:
  - Look up day of week (ET timezone)
  - Fetch rotation schedule from orchestrator-config.json
    revitalize_rotation[day_name][slot_products][slot]
    reclaim_rotation[day_name][slot_products][slot]
  - Get product details from brand-config.json
  - Get slot tone, angle, hook_style from schedule[slot]
```

**Tools:** JSON reads

---

### 3. **Generate Caption**
```
For each brand:
  - Assemble caption prompt using:
    * Brand voice guidelines (from brand-config.json)
    * Product name, price, URL
    * Slot tone (authority/warm/aspirational/urgency)
    * Theme (hormone balance/sleep/energy/etc.)
    * Hook style (research stat/helpful tip/invitation/social proof)
  - Call Claude to generate on-brand caption
  - Include CTA, hashtags, pricing on separate lines
  - NO medical claims, NO weight-loss promises, NO fabricated testimonials
```

**Tools:** Claude text generation (inline)

---

### 4. **Generate Images**
```
For Revitalize:
  - Use higgsfield image prompt template (women 45-65)
  - Insert: mood (from slot), setting (from theme)
  - Generate via mcp__higgsfield__generate_image
  
For Reclaim:
  - Use higgsfield image prompt template (men 45-55)
  - Insert: mood (from slot), setting (from theme)
  - Generate via mcp__higgsfield__generate_image

Poll with mcp__higgsfield__job_display until status=completed
```

**Tools:** `mcp__higgsfield__generate_image`, `mcp__higgsfield__job_display`

---

### 5. **Post to Platforms**

#### Instagram (both brands)
```
Use mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL:
  Step 1: INSTAGRAM_POST_IG_USER_MEDIA (create container)
    - ig_user_id: from orchestrator-config.json
    - account_alias: "instagram_cardin-bulgar" (Revitalize), "instagram_medlar-slap" (Reclaim)
    - caption: generated caption
    - image_url: from Higgsfield result
  Step 2: INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH (publish)
Capture post_id from response
```

#### Facebook (Revitalize only)
```
Use mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL:
  FACEBOOK_CREATE_PHOTO_POST
    - page_id: from orchestrator-config.json (fb_page_id)
    - caption: generated caption
    - image_url: from Higgsfield result
Capture post_id from response
```

#### YouTube (Reclaim only)
```
Generate 30-second video:
  - Static image (from Higgsfield)
  - Caption overlay (using caption text)
  - Background music (royalty_free_wellness_track.mp3)
  - FFmpeg: fade in (2s) → display (26s) → fade out (2s)
Upload via YouTube API:
  - Channel: from orchestrator-config.json (yt_channel_id)
  - Title: Brand name + date
  - Description: Caption
  - Category: 22 (Nonprofits & Activism)
Capture video_id from response
```

**Tools:** `mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL`, YouTube API (if available)

---

### 6. **Verify Posts**
```
For Instagram:
  Call mcp__Composio (Instagram GET) to verify post exists and is visible
For Facebook:
  Call mcp__Composio (Facebook GET) to verify post exists
For YouTube:
  Call YouTube API to verify video is indexed
Only proceed to logging if all verifications pass
```

**Tools:** Platform verification APIs

---

### 7. **Log Results**
```
Append to data/orchestrator-log.json:
{
  "date": "YYYY-MM-DD (Day ET)",
  "slot": "morning|afternoon|evening|night",
  "revitalize": {
    "product": "product name",
    "price": "$XX",
    "theme": "theme name",
    "angle": "education|supportive_solution|aspirational_offer|urgency_social_proof",
    "image_job_id": "higgsfield job ID",
    "ig_post_id": "Instagram post ID",
    "fb_post_id": "Facebook post ID",
    "ig_url": "https://instagram.com/...",
    "status": "posted|failed"
  },
  "reclaim": {
    "product": "product name",
    "price": "$XX",
    "theme": "theme name",
    "image_job_id": "higgsfield job ID",
    "ig_post_id": "Instagram post ID",
    "yt_video_id": "YouTube video ID",
    "ig_url": "https://instagram.com/...",
    "yt_url": "https://youtube.com/...",
    "status": "posted|failed"
  },
  "timestamp": "ISO 8601",
  "executed_by": "orchestrator routine|manual trigger",
  "approval_given_at": "ISO 8601"
}

Keep last 90 entries only
Commit and push to branch: claude/laughing-darwin-cQTwH
```

**Tools:** Write JSON, Git commit/push

---

## Compliance Gates

**Before posting, verify:**

1. ✅ No "fix/cure/heal/reverse" health claims
2. ✅ No weight-loss promises or numbers
3. ✅ No "guarantee(d)" or "proven" claims
4. ✅ No medical outcome claims (off medication, diagnoses)
5. ✅ No fabricated testimonials or statistics
6. ✅ No before/after body transformation claims
7. ✅ Product name, price, and full URL present
8. ✅ Clear call to action included
9. ✅ Framing is educational/supportive/aspirational (not deceptive)

**If any gate fails:** Stop, flag caption for manual review, do not post.

---

## Error Handling

| Error | Action |
|-------|--------|
| Image generation timeout | Retry up to 2x; if fails, use fallback image library |
| Post to Instagram fails | Log error, try Facebook/YouTube, notify user |
| Platform unavailable (429, 503) | Wait 5min, retry once, then fail gracefully |
| Already posted today (guard) | Abort, report in output |
| Compliance gate fails | Stop, flag for manual review, do not post |
| JSON parse error on config | Abort, report specific file + line |

---

## Approval & Authorization

**Standing authorization (from CLAUDE.md):**
- Owner: lccrichards
- Authorized platforms: Instagram, Facebook, YouTube
- Authorized brands: Revitalize & Thrive Now, Reclaim & Rise
- Account aliases: `instagram_cardin-bulgar`, `instagram_medlar-slap`
- Approval process: Routine fires → Claude generates → Posts automatically (no per-run confirmation needed)

**When to ask for approval:**
- First run of the day (morning slot)
- Compliance gate fails
- Platform restriction active (e.g., link sharing disabled on IG)
- Manual invocation with `approval_required=true`

---

## Usage Examples

### Automatic (Scheduled)
```
Triggered at 7:00 AM ET daily
$ orchestrator-post --slot=morning --brand=both
```

### Manual (Morning Review)
```
$ orchestrator-post --slot=morning --brand=revitalize --dry_run=true
→ Shows caption preview + image before posting
```

### Manual (Post Later)
```
$ orchestrator-post --slot=afternoon --brand=reclaim --date=2026-08-14
→ Posts content for specific date
```

### Override (Emergency Retract)
```
If post violates policy:
1. Call Instagram/Facebook/YouTube API to delete
2. Update orchestrator-log.json status to "retracted"
3. Notify user with reason
```

---

## Output

On success:
```
✅ ORCHESTRATOR POST COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand          Slot       Product                    Status
Revitalize     morning    30-Day Wellness Transform  ✓ Posted
Reclaim        morning    Reclaim Masterclass        ✓ Posted

Posts:
- Revitalize Instagram: https://instagram.com/p/...
- Revitalize Facebook: https://facebook.com/...
- Reclaim Instagram: https://instagram.com/p/...
- Reclaim YouTube: https://youtube.com/watch?v=...

Time: 4m 32s | Logged to orchestrator-log.json
```

On failure:
```
⚠️ POST GUARD: Already posted morning slot on 2026-08-13
Skipping to prevent duplicates.
Next eligible slot: afternoon (3 PM)
```

On compliance gate fail:
```
❌ COMPLIANCE GATE FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand: Revitalize
Issue: Medical claim detected in caption
Problematic text: "...fix your hormones..."
Recommendation: Change to "supports hormone balance"
Status: BLOCKED — manual review required
```

---

## Configuration Files

**Required inputs:**
- `/data/brand-config.json` — Brand voice, products, URLs, prices
- `/data/orchestrator-config.json` — Schedule, rotations, Higgsfield prompts, Composio accounts
- `/data/orchestrator-log.json` — POST history (created if missing)

**Generated output:**
- `/data/orchestrator-log.json` (appended)
- Git commit on branch `claude/laughing-darwin-cQTwH`

---

## Scheduled Triggers

Create Routines in Claude Code:

```
Morning:   0 11 * * * (7 AM ET)
Afternoon: 0 19 * * * (3 PM ET)
Evening:   0 23 * * * (7 PM ET)
Night:     0 2 * * *  (10 PM ET)
Video:     0 0 * * 2,4 (Mon/Wed, video generation)
```

Each trigger calls:
```
/orchestrator-post --slot=[morning|afternoon|evening|night] --brand=both --dry_run=false
```

---

## Maintenance

**Weekly:**
- Review orchestrator-log.json for failures
- Check brand-config.json for updated products/prices
- Verify Higgsfield + Composio account status

**Monthly:**
- Audit Instagram compliance (check for restriction notices)
- Refresh YouTube descriptions + category settings
- Archive old log entries (keep last 90)

**Before changes:**
- Test with `--dry_run=true`
- Verify compliance gates pass
- Confirm account aliases are current
