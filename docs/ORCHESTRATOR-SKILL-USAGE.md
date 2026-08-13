# Orchestrator Skill Usage Guide

## Quick Start

The Orchestrator Skill automates content generation and posting for both brands across Instagram, Facebook, and YouTube.

### Basic Usage

**Post morning content (both brands):**
```bash
python scripts/orchestrator-skill.py --slot=morning
```

**Post afternoon content (Revitalize only):**
```bash
python scripts/orchestrator-skill.py --slot=afternoon --brand=revitalize
```

**Preview evening content without posting:**
```bash
python scripts/orchestrator-skill.py --slot=evening --dry_run
```

**Post specific date:**
```bash
python scripts/orchestrator-skill.py --slot=morning --date=2026-08-14
```

---

## Workflow Overview

When you run the skill:

1. **Pre-flight Check** → Verifies configs, checks POST GUARD (no duplicate posts)
2. **Determine Content** → Looks up product/theme for brand/day/slot
3. **Generate Caption** → Claude creates on-brand caption with product + CTA
4. **Validate Compliance** → Checks for forbidden claims (weight loss, medical claims, etc.)
5. **Generate Images** → Higgsfield creates images (women for Revitalize, men for Reclaim)
6. **Post to Platforms** → Instagram, Facebook (Revitalize), YouTube (Reclaim)
7. **Verify & Log** → Confirms posts exist, logs to orchestrator-log.json

---

## Parameters

| Parameter | Values | Default | Required |
|-----------|--------|---------|----------|
| `--slot` | morning, afternoon, evening, night | — | ✅ Yes |
| `--brand` | revitalize, reclaim, both | both | No |
| `--date` | YYYY-MM-DD | Today (ET) | No |
| `--dry_run` | flag (true if present) | false | No |

---

## Scheduled Execution

The skill is triggered automatically by scheduled Routines in Claude Code:

```
Morning:   7:00 AM ET  → python orchestrator-skill.py --slot=morning
Afternoon: 3:00 PM ET  → python orchestrator-skill.py --slot=afternoon
Evening:   7:00 PM ET  → python orchestrator-skill.py --slot=evening
Night:     10:00 PM ET → python orchestrator-skill.py --slot=night
```

Each scheduled trigger runs `--brand=both` automatically.

---

## Compliance Gates (Built-in)

The skill **blocks posting** if it detects:

❌ **Forbidden words:** "fix," "cure," "heal," "reverse," "guarantee," "proven"  
❌ **Weight-loss claims:** "lost 5 lbs," "weight loss," "lose weight"  
❌ **Medical claims:** "off medication," "blood pressure," "medical condition"  
❌ **Fabricated testimonials:** Unnamed statistics ("1,200 women," "100s of customers")  
❌ **Before/after claims:** Body transformation language  

If a caption fails validation:
```
❌ COMPLIANCE GATE FAILED
Issue: Medical claim detected
Problematic text: "fix your hormones"
Recommendation: Change to "supports hormone balance"
Status: BLOCKED — manual review required
```

---

## Output Examples

### Success
```
============================================================
ORCHESTRATOR POST SKILL
============================================================
Slot: morning | Date: 2026-08-13 | Brands: revitalize, reclaim

[REVITALIZE]
  Product: 30-Day Wellness Transformation
  Price: $79
  Theme: hormone balance
  ✓ Ready for compliance check
  Platforms: instagram, facebook

[RECLAIM]
  Product: Reclaim Masterclass
  Price: $59
  Theme: testosterone optimization
  ✓ Ready for compliance check
  Platforms: instagram, youtube

============================================================
✅ ORCHESTRATOR POST PREPARED
============================================================

Next steps:
1. Claude will generate captions
2. Claude will call Higgsfield for images
3. Claude will post via Composio
4. Results logged to orchestrator-log.json
```

### Dry Run
```
MODE: DRY RUN (preview only)
[Shows same output above, but no posts created]
```

### Post Guard (Duplicate Prevention)
```
⚠️ POST GUARD: Already posted morning on 2026-08-13
   Skipping to prevent duplicates.
```

### Compliance Failure
```
❌ COMPLIANCE GATE FAILED
Issue: Weight loss numbers detected
Status: BLOCKED — manual review required
```

---

## Configuration Files

The skill reads from:

- **`data/brand-config.json`** — Brand voice, products, prices, URLs
- **`data/orchestrator-config.json`** — Schedule, rotations, Higgsfield prompts, platform accounts
- **`data/orchestrator-log.json`** — Log of all posted content (created if missing)

### Example Config Structure

```json
{
  "revitalize": {
    "name": "Revitalize and Thrive Now",
    "voice": "Warm, empowering, woman-to-woman...",
    "products": [
      {
        "name": "30-Day Wellness Transformation",
        "price_short": "$79",
        "url": "rivitalize.gumroad.com/l/nlkuz"
      }
    ]
  },
  "schedule": {
    "morning": {
      "time_et": "7:00 AM",
      "angle": "education",
      "tone": "Authority and credibility..."
    }
  },
  "revitalize_rotation": {
    "monday": {
      "theme": "hormone balance",
      "slot_products": {
        "morning": "Hormone Reset Masterclass",
        "afternoon": "Hormone-Balancing Meal Plan"
      }
    }
  }
}
```

---

## Troubleshooting

### "POST GUARD: Already posted"
**Problem:** Post already exists for this slot/day  
**Solution:** Change the date (`--date=2026-08-14`) or wait until next day

### "Product not found"
**Problem:** Product listed in rotation doesn't exist in brand-config.json  
**Solution:** Check `orchestrator-config.json` rotation for typos, or add product to `brand-config.json`

### "Invalid slot"
**Problem:** Slot doesn't exist in schedule  
**Solution:** Use one of: `morning`, `afternoon`, `evening`, `night`

### Compliance gate fails
**Problem:** Caption contains forbidden words  
**Solution:** Claude will flag the text; you can:
1. Edit the generated caption manually
2. Update brand guidelines to avoid the phrase
3. Rerun with revised version

### Image generation times out
**Problem:** Higgsfield takes >5 minutes  
**Solution:** Retry with `--dry_run` to test, check Higgsfield status separately

### Platform posting fails (429 / 503)
**Problem:** Instagram/Facebook rate limit or temporarily down  
**Solution:** Wait 5 minutes, then rerun the script (it will retry)

---

## Best Practices

✅ **DO:**
- Run `--dry_run` first to preview captions
- Check orchestrator-log.json after posting
- Review compliance gates if something seems off
- Schedule routines during off-peak hours (not 7 AM ET exactly, stagger by a few minutes)

❌ **DON'T:**
- Bypass compliance gates manually (they exist for legal/platform safety)
- Post the same content to two brands on the same day (stagger by 30 mins)
- Override POST GUARD without checking why it flagged
- Use fabricated testimonials or statistics

---

## Integration with Claude Code Triggers

To set up automatic scheduling:

1. Go to your Claude Code session
2. Use `/schedule` or create a Routine:
   ```
   Name: Morning Orchestrator Post
   Cron: 0 11 * * * (7 AM ET)
   Command: python scripts/orchestrator-skill.py --slot=morning
   ```

3. Repeat for afternoon (0 19), evening (0 23), night (0 2)

---

## Monitoring

Check posting history:

```bash
# View last 10 posts
tail -50 data/orchestrator-log.json

# Check specific date
grep "2026-08-13" data/orchestrator-log.json

# Verify post IDs from platforms
jq '.[] | select(.date | contains("2026-08-13")) | {product: .revitalize.product, ig_post_id: .revitalize.ig_post_id}' data/orchestrator-log.json
```

---

## Manual Post Deletion

If a post violates policy and needs to be removed:

1. Find post ID in orchestrator-log.json
2. Delete from Instagram/Facebook/YouTube manually
3. Update log entry status:
   ```bash
   # Edit data/orchestrator-log.json and change status to "retracted"
   ```
4. Commit: `git add data/orchestrator-log.json && git commit -m "Retracted violating post"`

---

## Support

Questions? Check:
- `.claude/skills/orchestrator-post.md` — Full skill specification
- `data/orchestrator-config.json` — Schedule + rotation details
- `data/orchestrator-log.json` — Execution history + post IDs
- `CLAUDE.md` — Brand guidelines + authorization
