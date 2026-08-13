# Orchestrator Agent

**Type:** Claude Code Remote Agent  
**Purpose:** Autonomous content generation and posting for Revitalize & Thrive Now and Reclaim & Rise  
**Trigger:** Scheduled routines (7 AM, 3 PM, 7 PM, 10 PM ET)  
**Output:** Posts to Instagram, Facebook, YouTube + logs to orchestrator-log.json

---

## Agent Capabilities

The Orchestrator Agent runs as a standalone Claude Code Remote session and:

1. **Determines today's content** — Looks up day/slot in orchestrator-config.json
2. **Generates captions** — Creates on-brand captions using brand voice guidelines
3. **Generates images** — Calls Higgsfield to create brand-specific imagery
4. **Posts to platforms** — Posts to Instagram, Facebook (Revitalize), YouTube (Reclaim)
5. **Verifies posts** — Confirms posts exist and are visible
6. **Logs results** — Records post IDs, URLs, and metadata
7. **Reports status** — Returns success/failure with links and metrics

---

## Scheduled Triggers

Create 4 Claude Code Routines to spawn this agent daily:

### Morning Agent (7:00 AM ET)
```yaml
Name: Orchestrator Agent — Morning
Schedule: 0 11 * * * (7:00 AM ET)
Environment: [your environment]
Model: claude-opus-5
Command: /orchestrator-agent morning both
Create New Session: true
Notifications: push + email on failure
```

### Afternoon Agent (3:00 PM ET)
```yaml
Name: Orchestrator Agent — Afternoon
Schedule: 0 19 * * * (3:00 PM ET)
Environment: [your environment]
Model: claude-opus-5
Command: /orchestrator-agent afternoon both
Create New Session: true
Notifications: push + email on failure
```

### Evening Agent (7:00 PM ET)
```yaml
Name: Orchestrator Agent — Evening
Schedule: 0 23 * * * (7:00 PM ET)
Environment: [your environment]
Model: claude-opus-5
Command: /orchestrator-agent evening both
Create New Session: true
Notifications: push + email on failure
```

### Night Agent (10:00 PM ET)
```yaml
Name: Orchestrator Agent — Night
Schedule: 0 2 * * * (10:00 PM ET)
Environment: [your environment]
Model: claude-opus-5
Command: /orchestrator-agent night both
Create New Session: true
Notifications: push + email on failure
```

---

## Agent Workflow

When triggered, the agent:

```
1. INITIALIZE
   ├─ Load brand-config.json
   ├─ Load orchestrator-config.json
   ├─ Check POST GUARD (no duplicates)
   └─ Determine day/slot/product

2. GENERATE CONTENT
   ├─ Build caption prompt
   ├─ Generate caption (on-brand)
   ├─ Validate caption (compliance gates)
   └─ Build Higgsfield prompt

3. CREATE IMAGES
   ├─ Call mcp__higgsfield__generate_image (Revitalize)
   ├─ Call mcp__higgsfield__generate_image (Reclaim)
   ├─ Poll mcp__higgsfield__job_display until done
   └─ Retrieve image URLs

4. POST TO PLATFORMS
   ├─ Instagram: Create + Publish (both brands)
   ├─ Facebook: Post (Revitalize only)
   ├─ YouTube: Generate video + Upload (Reclaim only)
   └─ Capture post IDs from each platform

5. VERIFY POSTS
   ├─ Call INSTAGRAM_GET_IG_MEDIA
   ├─ Call FACEBOOK_GET_PAGE_POST
   ├─ Call YouTube API to confirm video indexed
   └─ Confirm all posts are public

6. LOG & REPORT
   ├─ Append entry to orchestrator-log.json
   ├─ Commit to claude/laughing-darwin-cQTwH
   ├─ Push to remote
   └─ Report success with post URLs
```

---

## Agent Instructions

The agent receives a prompt like:

```
/orchestrator-agent morning both
```

Which translates to:

```
Execute the morning orchestrator posting routine:
- Slot: morning
- Brands: both (Revitalize & Reclaim)
- Date: today (ET timezone)

Steps:
1. Load configs and check POST GUARD
2. Generate captions for both brands using brand voice + product details
3. Call Higgsfield to generate images (women for Revitalize, men for Reclaim)
4. Post to Instagram, Facebook (Revitalize), YouTube (Reclaim)
5. Verify all posts exist and are visible
6. Log results to orchestrator-log.json with post IDs and URLs
7. Commit and push to claude/laughing-darwin-cQTwH
8. Report success with post links and metrics

Compliance: Block posting if any caption contains:
- Medical claims (fix/cure/heal/reverse)
- Weight-loss promises
- Fabricated testimonials or statistics
- Before/after body claims
- Medical outcomes

Use existing brand voice from brand-config.json, not placeholder language.
```

---

## Agent Permissions

The agent needs these MCP tool permissions:

- ✅ `mcp__higgsfield__generate_image` — Image generation
- ✅ `mcp__higgsfield__job_display` — Poll image status
- ✅ `mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL` — Instagram/Facebook posting
- ✅ `mcp__Composio__YouTube API` — YouTube upload (if available)
- ✅ `Read` / `Write` — File I/O for configs and logs
- ✅ `Bash` — Git commit/push

---

## Agent Output Example

**Success:**
```
✅ ORCHESTRATOR AGENT COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Slot: morning | Date: 2026-08-13 | Status: POSTED

[REVITALIZE & THRIVE NOW]
  Product: Energy Restoration Guide ($29)
  Theme: energy restoration
  
  Instagram: https://instagram.com/p/C_abc123def/
  Facebook: https://facebook.com/groups/.../posts/123456
  Status: ✓ Posted & Verified

[RECLAIM & RISE NOW]
  Product: Reclaim Masterclass ($149)
  Theme: energy and cognitive performance
  
  Instagram: https://instagram.com/p/C_xyz789ghi/
  YouTube: https://youtube.com/watch?v=abc123xyz
  Status: ✓ Posted & Verified

Logged to orchestrator-log.json
Committed to claude/laughing-darwin-cQTwH
Pushed to remote

Total time: 4m 23s
```

**Failure (Compliance):**
```
❌ COMPLIANCE GATE FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Brand: Revitalize
Slot: morning
Issue: Medical claim in caption
Problematic text: "...fix your hormones..."
Status: BLOCKED — manual review required

Recommendation: Change to "supports hormone balance"
```

**Failure (Duplicate):**
```
⚠️  POST GUARD BLOCKED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Slot: morning
Date: 2026-08-13
Status: Already posted today

Skipping to prevent duplicates.
Next eligible slot: afternoon (3 PM)
```

---

## Monitoring & Management

### View Agent Runs
```bash
# List all orchestrator agent sessions
mcp__Claude_Code_Remote__list_sessions --tags "orchestrator-agent"

# Get specific agent status
mcp__Claude_Code_Remote__get_session session_xyz123
```

### Manage Routines
```bash
# List all orchestrator triggers
mcp__Claude_Code_Remote__list_triggers

# Disable a routine temporarily
mcp__Claude_Code_Remote__update_trigger --trigger_id trig_abc --enabled false

# Manually fire a routine
mcp__Claude_Code_Remote__fire_trigger --trigger_id trig_morning
```

### Monitor Logs
```bash
# View today's posting results
tail -20 data/orchestrator-log.json | jq '.[] | select(.date | contains("2026-08-13"))'

# Check for failures
grep '"status": "failed"' data/orchestrator-log.json
```

---

## Agent Lifecycle

### Spawn
Triggered by schedule → Creates new session → Inherits environment + permissions

### Execute
- Initialize (load configs)
- Generate (captions + images)
- Post (to platforms)
- Verify (posts exist)
- Log (save results)
- Report (return status)
- Cleanup (archive session)

### Archive
Session automatically archived after:
- Successful completion (all posts verified)
- Compliance gate failure (manual review needed)
- Platform error after retries (logged for investigation)

---

## Fallback & Recovery

If agent encounters errors:

1. **Image generation timeout** → Retry 2x, then use default image
2. **Instagram rate limit (429)** → Wait 5 min, retry once
3. **Facebook API error** → Log error, skip Facebook, continue with IG/YouTube
4. **Compliance gate failure** → Stop, flag caption, notify user
5. **Log write error** → Retry, escalate if persistent

All errors logged to orchestrator-log.json with timestamp and context.

---

## Authorization

The agent operates under **standing authorization** from the repository owner (lccrichards):

- ✅ Can post to Revitalize & Thrive Now (IG: 27164026169935796, FB: 130419383084779)
- ✅ Can post to Reclaim & Rise Now (IG: 27634679816148097)
- ✅ Can generate images via Higgsfield
- ✅ Can log results and commit to repository
- ✅ Can post without per-run confirmation (pre-approved by owner)

**Constraint:** Cannot post if compliance gates fail (safety override).

---

## Cost & Performance

| Metric | Estimate | Details |
|--------|----------|---------|
| Time per post | 4-5 minutes | Image generation (2-3 min) + posting (1-2 min) |
| API calls | ~20-25 | Higgsfield (2) + Composio (8-10) + YouTube (1-2) + Verification (5-8) |
| Storage | ~5KB per log entry | 90-day retention = ~450KB |
| Monthly cost | $0-5 | Within free tier for most services |

---

## Next Steps to Deploy

1. **Create routines** in Claude Code:
   - /mcp or go to Claude Code settings
   - Create 4 Routines with exact cron times
   - Set to create new session on fire
   - Add email/push notifications

2. **Test first run**:
   - Manually trigger morning routine
   - Verify posts appear on platforms
   - Check orchestrator-log.json for entries
   - Review post links in your Instagram feed

3. **Monitor first week**:
   - Check for failures or compliance gates
   - Verify POST GUARD works (no duplicates)
   - Monitor Instagram for restriction notices
   - If clean, agent is ready for production

4. **Request Instagram review** (after 1-2 weeks):
   - Open Instagram settings
   - Request review of August 12 restriction
   - Link to your compliant posts as evidence
   - Should lift by September 11 deadline
