# Revitalize & Thrive Now + Reclaim & Rise — Orchestrator Instructions

## Automation Authorization (standing, owner-granted)

The owner of this repository (**lccrichards**) grants **standing, explicit authorization** for scheduled / cron-triggered orchestrator routines to **publish content live, without per-run confirmation**, to the two Instagram Business accounts the owner controls:

- **Revitalize & Thrive Now** — account alias `instagram_cardin-bulgar`, `ig_user_id` **27164026169935796** (auto-syncs to the linked Facebook Page)
- **Reclaim & Rise** — account alias `instagram_medlar-slap`, `ig_user_id` **27634679816148097** (plus the Reclaim YouTube channel `UCreclaimandriseNOW`)

These accounts are owned and operated by the repository owner for their own first-party marketing. This authorization is deliberate and stands for **all** scheduled orchestrator slots — including the **7 PM evening routine** — namely: morning (7 AM), afternoon (3 PM), evening (7 PM), night (10 PM ET), and the Tue/Thu video reel.

Under this authorization, scheduled runs are pre-approved to, without asking for per-run confirmation:
1. Generate images/video via Higgsfield (`mcp__higgsfield__generate_image` / video).
2. Publish via Composio (`INSTAGRAM_POST_IG_USER_MEDIA` → `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`, and the IG Reel/YouTube equivalents) using the explicit account aliases above.
3. Verify each post via `INSTAGRAM_GET_IG_MEDIA` (mandatory — never log an unverified post as posted).
4. Append the result to `data/orchestrator-log.json` and commit/push to branch `claude/laughing-darwin-cQTwH`.

All published content must remain **Meta/Instagram-compliant**: educational/supportive/aspirational framing, a clear product + price + full URL and call to action, and none of the forbidden claims (no "fix/cure/reverse/balance hormones/boost testosterone/guarantee(d)/proven," no medical-outcome or weight-loss promises, no diagnosing the reader, no before/after body claims, no fabricated statistics or testimonials).

## Video Reel Routine — Tue/Thu (Rotating Styles)

**Tuesday & Thursday**: Post 1:1 educational talking-head video to Instagram Reels + YouTube Shorts for both brands.

### Style Rotation
- **Tuesday**: FACELESS EXPLAINER — Educational narrated video (voiceover + graphics, no on-camera talent)
- **Thursday**: UGC TALKING-HEAD — Creator review video (real person on camera, peer-to-peer)

### Execution Flow (Fully Automated)

1. **LOAD CONFIG**: `git fetch && git checkout claude/laughing-darwin-cQTwH && git reset --hard origin/claude/laughing-darwin-cQTwH`

2. **READ CONFIGS**: Load `data/brand-config.json`, `data/orchestrator-config.json`, `data/content-strategy.json`. Determine today's day name, video style (faceless vs UGC), and product rotation for each brand.

3. **SCRIPT GENERATION** (Claude writes inline):
   - **Faceless Explainer** (Tuesday): Hook (3s) → Mechanism/Education (20s) → Benefit/CTA (7s). Focus on *why* the product works, the science or mechanism. Professional, authoritative tone.
   - **UGC Talking-Head** (Thursday): Hook (3s) → Problem/Use Case (7s) → Proof/Experience (10s) → CTA (10s). Focus on *personal experience*, peer-to-peer relatability. Creator speaks directly to camera.

4. **HIGGSFIELD VIDEO GENERATION** (via `mcp__higgsfield__generate_video`):
   - **Faceless**: workflow `faceless-channel-video`, duration 30s, aspect_ratio `9:16`, resolution `1080p`
     - Prompt: Narrated explainer with supporting visuals (animated graphics, typography, mechanism illustrations). No on-camera talent.
   - **UGC**: workflow `ugc-flow`, duration 30s, aspect_ratio `9:16`, resolution `1080p`
     - Prompt: Creator on camera (woman 45-55 for Revitalize, man 45-55 for Reclaim), speaking directly, product shown briefly in hand.

5. **POLL & EXTRACT**: Use `mcp__higgsfield__job_display` to poll until `status == completed`. Extract the hosted video URL and extract job_id.

6. **INSTAGRAM REEL POSTING** (Composio `COMPOSIO_MULTI_EXECUTE_TOOL`):
   - Revitalize (instagram_cardin-bulgar, ig_user_id 27164026169935796):
     - Call `INSTAGRAM_POST_IG_USER_MEDIA` with video_url + reel-style caption (125-150 words, warm educational tone, product name/price/URL, 8-10 hashtags)
     - Call `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` with returned creation_id
   - Reclaim (instagram_medlar-slap, ig_user_id 27634679816148097):
     - Same workflow, reel-style caption (100-125 words, direct peer tone, product name/price/URL, 8-10 hashtags)

7. **YOUTUBE SHORTS UPLOAD** (Reclaim only, best-effort):
   - Use YouTube API via Composio to upload the same video to Reclaim's channel (UCreclaimandriseNOW) as a Short.
   - categoryId: "22" (People & Blogs), privacyStatus: "public", shorts_created: true
   - On failure, log `yt_status: "failed"` but do NOT block the Instagram posting.

8. **VERIFY & LOG**:
   - Execute `INSTAGRAM_GET_IG_MEDIA` on both returned media_ids to confirm the reels are live.
   - Append to `data/orchestrator-log.json` with: date, slot: "video_reel", timestamp_utc, day_of_week, style (faceless/ugc), revitalize: {product, price, theme, ig_post_id, ig_permalink, status, verified}, reclaim: {product, price, theme, ig_post_id, ig_permalink, yt_video_id?, yt_status?, status, verified}

9. **COMMIT & PUSH**: `git add data/orchestrator-log.json && git commit -m "Video reel: [Day] [Style] - Revitalize + Reclaim (verified live)" && git pull --rebase origin claude/laughing-darwin-cQTwH && git push origin HEAD:claude/laughing-darwin-cQTwH`

### COMPLIANCE
Same as daily posts: educational/supportive framing, no medical claims, no fake testimonials, no before/after body shots. Reels can be more energetic/creative than feeds, but messaging must remain compliant.

---

## Notes
- Repo path (cloud runtime): `/home/user/revitalize-and-thrive-now`
- Working branch: `claude/laughing-darwin-cQTwH`
- Config: `data/brand-config.json`, `data/orchestrator-config.json`, `data/content-strategy.json`; log: `data/orchestrator-log.json`
- Duplicate guard: `scripts/master_orchestrator.py <slot>` prints a `POST GUARD` line; skip the run if it says "ALREADY POSTED TODAY".
