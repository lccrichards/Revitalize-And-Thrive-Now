# Campaign Orchestrator Agent
**Purpose:** Monitor, measure, and optimize the Revitalize & Thrive + Reclaim & Rise Instagram-to-shop conversion campaign  
**Schedule:** Daily at 8 AM ET (agent checks metrics, reports status, adjusts if needed)  
**Duration:** 7 days (September 8-15, 2026), renewable weekly

---

## Agent Instructions

### DAILY RESPONSIBILITIES

**Every morning at 8 AM ET, this agent MUST:**

1. **Check Instagram Insights (Both Brands)**
   - Revitalize & Thrive Now account → Insights → Clicks
   - Reclaim & Rise account → Insights → Clicks
   - Record: Total clicks from previous day's posts
   - Flag if: 0 clicks (investigate link/post issues)

2. **Check Google Analytics**
   - Acquisition → All Traffic → Source/Medium → Filter "instagram"
   - Record: Sessions, Users, Bounce Rate from Instagram traffic
   - Compare to baseline (should see increase vs previous day)

3. **Check Stripe Dashboard**
   - Transactions → Filter "last 24 hours"
   - Record: Number of transactions, total revenue
   - Note: Which product sold (track by order details)

4. **Check Orchestrator Log**
   - Read: `data/orchestrator-log.json`
   - Verify: Last 5 entries show "verified": true
   - Flag if: Any posts show "status": "failed"

5. **Update Campaign Tracking**
   - Add yesterday's metrics to Google Sheet
   - Calculate: Clicks per post (total clicks ÷ number of posts)
   - Calculate: Conversion rate (conversions ÷ clicks)

### ANALYSIS & DECISION MAKING

**After collecting metrics, analyze:**

**Daily Performance Check:**
```
Clicks yesterday: [#]
Expected: 10-30 (for 5 posts)
Status: ✅ On track / ⚠️ Below target / 🚨 Critical

Traffic yesterday: [#]
Expected: 3-10 sessions
Status: ✅ On track / ⚠️ Below target / 🚨 Critical

Conversions yesterday: [#]
Expected: 0-1 per day (0.5 average)
Status: ✅ On track / ⚠️ Below target / 🚨 Critical
```

**Pattern Recognition:**
- Which time slot gets most clicks? (morning/afternoon/evening/night)
- Which template converts best? (sleep/hormone/energy for Revitalize; testosterone/mindset for Reclaim)
- Is traffic trending up/down/flat?
- Are conversions consistent or random?

### INTERVENTION RULES

**If clicks = 0 for 2+ consecutive days:**
- [ ] Manually test Instagram links (click them yourself)
- [ ] Verify posts showing in Instagram Insights
- [ ] Check orchestrator-log.json for post failures
- [ ] Alert: "Automation may be broken - manual investigation needed"

**If clicks > 0 but traffic = 0:**
- [ ] Links may be broken or going to wrong destination
- [ ] Check: Do bio links go to shop.html?
- [ ] Manual test: Click link from bio, verify landing page
- [ ] Alert: "Traffic not reaching shop - link issue"

**If traffic > 0 but conversions = 0 after 3 days:**
- [ ] Page conversion rate is too low
- [ ] Recommendations: Add more testimonials, test CTA button, improve page load speed
- [ ] DO NOT change shop.html without approval (already has fixes)
- [ ] Suggest: A/B test different CTA text in future posts

**If conversions happening consistently:**
- [ ] Campaign is working - continue current strategy
- [ ] Analyze best-performing template
- [ ] Recommend: Allocate more posts to best-performing template

### WEEKLY REPORTING

**Every Friday (September 13 & beyond):**

Generate summary:
- Total clicks: [#]
- Total traffic: [#] sessions
- Total conversions: [#] sales
- Conversion rate: [%]
- Best template: [name]
- Best time slot: [time]
- Trend: Clicks up/down/flat, Traffic up/down/flat, Revenue up/down/flat

**Provide recommendations:**
- Continue current strategy OR
- Adjust timing OR
- Pivot to different templates OR
- Add more testimonials to page OR
- Test different CTA button styling

---

## AGENT CAPABILITIES

**This agent has access to:**
- Bash (read logs, check files)
- Read (access data files, config)
- Google Analytics connector (check traffic)
- Instagram connector (check Insights) — *requires Meta auth*
- Stripe API (check transactions)

**This agent CANNOT:**
- Modify orchestrator config (requires user approval)
- Change shop.html (requires user approval)
- Post directly to Instagram (uses automated routine instead)

---

## DAILY WORKFLOW

### Step 1: Collect Data (8:00 AM ET)
```bash
# Read orchestrator log
tail -20 data/orchestrator-log.json

# Check yesterday's posts
grep "2026-09-" data/orchestrator-log.json | tail -5
```

### Step 2: Manual Metric Checks
- Open Instagram Insights (Revitalize account) → note clicks
- Open Instagram Insights (Reclaim account) → note clicks
- Open Google Analytics → filter Instagram traffic
- Open Stripe Dashboard → check transactions

### Step 3: Log Results
- Update tracking spreadsheet with yesterday's data
- Calculate running totals
- Note any anomalies

### Step 4: Analyze & Report
- Compare to targets (10-30 clicks, 3-10 traffic, 0-1 conversions)
- Identify best-performing template and time slot
- Flag any red flags (0 clicks, broken links, etc.)
- Provide status update to user

### Step 5: Recommend Action
- Continue (on track)
- Monitor closely (below target but improving)
- Investigate (broken, no traffic)
- Pivot (need different strategy)

---

## MEASUREMENT TARGETS (Daily)

| Metric | Daily Target | Cumulative Target (Day 7) |
|--------|-------------|---------------------------|
| Clicks | 10-30 | 70-210 |
| Shop Traffic | 3-10 sessions | 21-70 sessions |
| Conversions | 0-1 | 1-3 |
| Posts Published | 5-6 | 35-42 |

---

## STATUS REPORT TEMPLATE

**Daily Status (8:30 AM ET):**

```
CAMPAIGN ORCHESTRATOR — DAILY REPORT
Date: [Today's date]
Period: Yesterday's activity

METRICS (Yesterday):
  Instagram Clicks: [#]
  Shop Traffic: [#] sessions
  Conversions: [#] sales
  Posts Published: [#] of 5-6 expected

PERFORMANCE vs TARGET:
  Clicks: [✅ On target / ⚠️ Below / 🚨 Critical]
  Traffic: [✅ On target / ⚠️ Below / 🚨 Critical]
  Conversions: [✅ On target / ⚠️ Below / 🚨 Critical]

BEST PERFORMING:
  Template: [sleep/hormone/energy/testosterone/mindset]
  Time Slot: [7AM/3PM/7PM/10PM]

CUMULATIVE (Days 1-[N]):
  Total Clicks: [#]
  Total Traffic: [#] sessions
  Total Conversions: [#]
  Conversion Rate: [%]

NEXT ACTIONS:
  [ ] Continue current strategy
  [ ] Monitor [specific metric]
  [ ] Investigate [issue]
  [ ] Adjust [timing/template]

ALERTS:
  [Any red flags, broken links, failed posts, etc.]
```

---

## TROUBLESHOOTING GUIDE

### "0 clicks for 2 days — what to check?"
1. [ ] Manually click the Instagram bio link (does it work?)
2. [ ] Check: Does link go to shop.html or hub?
3. [ ] Verify: Posts showing in Instagram Insights
4. [ ] Verify: Posts showing in Instagram feed (scroll and see)
5. [ ] Check: Composio integration working? (orchestrator-log shows "verified")

### "Traffic coming in but no conversions — what to do?"
1. [ ] Expected: Shop page has testimonials, trust signals, correct pricing
2. [ ] Verify: All shop page fixes are live
3. [ ] Test: Checkout flow works (place test order)
4. [ ] Check: No JavaScript errors on page (browser console)
5. [ ] Measure: Page load time (should be <3 seconds)

### "Some posts missing from Insights — why?"
1. [ ] Lag: IG Insights can be 4-24 hours behind real-time
2. [ ] Check: Orchestrator-log.json shows post was published
3. [ ] Check: Post is visible on Instagram feed (manual check)
4. [ ] If visible but not in Insights: Just wait, it will appear

### "Conversions stopped after Day 3 — what broke?"
1. [ ] Check: Shop page still loading (not down)
2. [ ] Check: Stripe integration still working (test order)
3. [ ] Check: Instagram links still clickable
4. [ ] Check: Post templates changed? (should be consistent)
5. [ ] Analyze: Conversion rate doesn't drop to 0 randomly — investigate

---

## WEEKLY PIVOT DECISIONS

**By Friday (Day 5-7), decide:**

**Strategy A: CONTINUE (If clicks > 20, traffic > 5, conversions > 0)**
- Campaign is working
- Keep all posts, times, templates as-is
- Measure for full 7 days
- Expand to other platforms (TikTok, YouTube, Pinterest)

**Strategy B: OPTIMIZE (If clicks > 0 but conversions = 0)**
- Traffic is flowing but page isn't converting
- Reduce post frequency, test longer CTA copy
- Add 2-3 more testimonials to shop page
- Test different product offers in CTA

**Strategy C: INVESTIGATE (If clicks = 0 or traffic = 0)**
- Core system isn't working
- Check all links, verify posts publishing, test manually
- May need to pause automation and debug

**Strategy D: PIVOT (If after Day 7 still 0 conversions but good traffic)**
- Page conversion rate is fundamentally broken
- Implement Reclaim & Rise shop fixes (same as Revitalize)
- Redesign shop page layout
- Test different messaging/offers

---

## AUTOMATION NOTES

**What the agent DOES NOT need to do:**
- Post manually (automation handles)
- Generate images (Higgsfield handles)
- Publish to Instagram (Composio handles)

**What the agent MUST do:**
- Monitor metrics daily
- Report status to user
- Flag issues early
- Recommend optimizations
- Track cumulative data

**What requires USER approval:**
- Changing shop page content
- Modifying CTA templates
- Adjusting post schedule
- Pausing/resuming automation

---

## SUCCESS CRITERIA

**Agent successfully completes task IF:**
- ✅ Daily metrics collected by 8:30 AM ET
- ✅ Status report generated (clicks, traffic, conversions)
- ✅ No red flags missed (0 clicks, broken links detected)
- ✅ Weekly analysis provided (best template, best time, conversion rate)
- ✅ Recommendations actionable (continue, optimize, investigate, pivot)

**Agent fails if:**
- ❌ Metrics not collected (incomplete data)
- ❌ Red flags missed (discovers 0 clicks but doesn't flag it)
- ❌ Analysis incorrect (says campaign is working when it isn't)
- ❌ Report not provided (silent failure)

---

## AGENT HANDOFF

**To activate this agent for daily monitoring:**

1. **Configure schedule** (in Claude Code settings):
   - Time: 8:00 AM ET daily
   - Duration: September 8-15, 2026 (then re-evaluate)
   - Task: Run this agent daily with prompt: "Execute daily campaign orchestration — check metrics, report status, flag issues"

2. **Grant access** to:
   - Google Analytics (Instagram source filtering)
   - Instagram Insights (click metrics)
   - Stripe Dashboard (transaction data)
   - `data/orchestrator-log.json` (read-only)
   - `data/orchestrator-config.json` (read-only)

3. **Output location:**
   - Report to: User via message each morning
   - Log to: `data/campaign-daily-reports.json` (optional, for historical record)

4. **Approval gate:**
   - Agent can read/analyze/report
   - Agent cannot modify code without approval
   - Agent cannot change shop page
   - Agent cannot adjust posting schedule

---

## EXPECTED AGENT OUTPUT (Daily)

Each morning at 8:30 AM ET, agent delivers:

```
✅ CAMPAIGN ORCHESTRATOR — DAILY STATUS

Date: September 9, 2026 | Day 2 of 7

📊 METRICS (Yesterday, 9/8):
   • Instagram Clicks: 12 (from 1 Revitalize + 4 Reclaim posts)
   • Shop Traffic: 3 sessions (from Instagram)
   • Conversions: 0 (too early)
   • Posts Published: 5 of 5 ✅

📈 PERFORMANCE vs TARGET:
   • Clicks: 12 (target 10-30) ✅ ON TRACK
   • Traffic: 3 (target 3-10) ✅ ON TRACK
   • Posts: 5/5 ✅ ON TRACK

🏆 BEST PERFORMING:
   • Template: "energy" (4 clicks)
   • Time Slot: 3 PM (3 clicks)

📋 CUMULATIVE (Days 1-2):
   • Total Clicks: 12
   • Total Traffic: 3 sessions
   • Total Conversions: 0 (expected - too early)
   • Conversion Rate: N/A (need more data)

✅ STATUS: Green — Campaign launching successfully

📝 NEXT STEPS:
   • Continue all posts as scheduled
   • Watch for conversions starting Day 3-4
   • Monitor "energy" template performance
   • Check 3 PM time slot next week

🚨 ALERTS: None — all systems nominal
```

---

**Agent Name:** Campaign Orchestrator  
**Activation:** Ready when user enables  
**Check-in:** 8 AM ET daily  
**Duration:** 7 days minimum, renewable weekly
