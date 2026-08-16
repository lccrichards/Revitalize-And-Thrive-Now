# Revitalize & Thrive Now + Reclaim & Rise — Orchestrator Instructions

## Automation Authorization (standing, owner-granted)

The owner of this repository (**lccrichards**) grants **standing, explicit authorization** for scheduled / cron-triggered orchestrator routines to **publish content live, without per-run confirmation**, to the two Instagram Business accounts the owner controls:

- **Revitalize & Thrive Now** — account alias `instagram_walrus-waac`, `ig_user_id` **27164026169935796** (auto-syncs to the linked Facebook Page)
- **Reclaim & Rise** — account alias `instagram_medlar-slap`, `ig_user_id` **27634679816148097** (plus the Reclaim YouTube channel `UCreclaimandriseNOW`)

These accounts are owned and operated by the repository owner for their own first-party marketing. This authorization is deliberate and stands for **all** scheduled orchestrator slots — including the **7 PM evening routine** — namely: morning (7 AM), afternoon (3 PM), evening (7 PM), night (10 PM ET), and the Tue/Thu video reel.

Under this authorization, scheduled runs are pre-approved to, without asking for per-run confirmation:
1. Generate images/video via Higgsfield (`mcp__higgsfield__generate_image` / video).
2. Publish via Composio (`INSTAGRAM_POST_IG_USER_MEDIA` → `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`, and the IG Reel/YouTube equivalents) using the explicit account aliases above.
3. Verify each post via `INSTAGRAM_GET_IG_MEDIA` (mandatory — never log an unverified post as posted).
4. Append the result to `data/orchestrator-log.json` and commit/push to branch `claude/laughing-darwin-cQTwH`.

All published content must remain **Meta/Instagram-compliant**: educational/supportive/aspirational framing, a clear product + price + full URL and call to action, and none of the forbidden claims (no "fix/cure/reverse/balance hormones/boost testosterone/guarantee(d)/proven," no medical-outcome or weight-loss promises, no diagnosing the reader, no before/after body claims, no fabricated statistics or testimonials).

## Notes
- Repo path (cloud runtime): `/home/user/revitalize-and-thrive-now`
- Working branch: `claude/laughing-darwin-cQTwH`
- Config: `data/brand-config.json`, `data/orchestrator-config.json`; log: `data/orchestrator-log.json`
- Duplicate guard: `scripts/master_orchestrator.py <slot>` prints a `POST GUARD` line; skip the run if it says "ALREADY POSTED TODAY".
