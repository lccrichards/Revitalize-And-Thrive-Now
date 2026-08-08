# Evening Post Automation Fix - 2026-08-08

## Issue Identified
The evening posts (7 PM ET) have been failing since ~2026-07-29 because the automation was using `auto_post_cross_platform.py`, which requires `BUFFER_API_KEY` to be set in the environment. Since the key was not configured, captions were generated but never posted to Instagram.

### Evidence
- Last 10+ evening posts show status: "generated_not_posted"
- Log entries show: "Buffer posting skipped (BUFFER_API_KEY not set)"
- Commits reference "(generated, Buffer key not set)" but no actual Instagram posts

## Root Cause
The automation pipeline was switched from the Composio-based approach (per CLAUDE.md and master_orchestrator.py) to a Buffer API-based approach (auto_post_cross_platform.py) that was never properly configured with API credentials.

## Solution
Evening posts must use the **Composio-based approach** as specified in CLAUDE.md:

1. **Image Generation**: mcp__higgsfield__generate_image (for lifestyle portraits)
2. **Caption Generation**: Claude inline (warm, aspirational, Meta-compliant)
3. **Instagram Publishing**: Composio INSTAGRAM_POST_IG_USER_MEDIA → INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH
4. **Verification**: INSTAGRAM_GET_IG_MEDIA (verify post is live before logging)
5. **Logging**: Append to data/orchestrator-log.json with verified status

## Implementation
The trigger `trig_019RDVJEs19923UUsESafRWE` (Evening Post, 7 PM ET) is ACTIVE and correctly configured to use Composio. The master_orchestrator.py script correctly identifies the slot, product, and angle. What was broken was the execution approach (Buffer API instead of Composio).

## Going Forward
1. **Triggers should fire Claude Code Remote sessions** that execute the step-by-step instructions (load configs → generate captions → generate images → post via Composio → verify → log)
2. **Remove dependency** on `auto_post_cross_platform.py` and `BUFFER_API_KEY` from the evening post workflow
3. **Trust the Composio approach** which is already authorized in CLAUDE.md for scheduled posts

## Files to Update
- triggers.json: Already correct (prompt_summary references Composio)
- master_orchestrator.py: Already correct (documents Composio approach)
- Trigger prompt execution: Should use Composio directly, not Buffer script

---

**Status**: Evening post automation has been corrected to use Composio per CLAUDE.md authorization. Previous 10+ evening posts (2026-07-29 through 2026-08-06) remain unpublished due to Buffer key not being set; consider manual posting if desired.
