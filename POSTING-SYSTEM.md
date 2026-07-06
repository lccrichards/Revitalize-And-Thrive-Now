# Daily Multi-Platform Posting System

## Overview
Automated daily posting system for **Revitalize & Thrive Now** and **Reclaim & Rise Now** across 6 platforms with intelligent scheduling, product rotation, and conversion tracking.

## Posting Schedule

### Revitalize & Thrive Now (Women 45-65)
| Day | Time | Type | Platforms | Frequency |
|-----|------|------|-----------|-----------|
| **Monday** | 7 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Tuesday** | 7 PM ET | **VIDEO** | Instagram Reels, TikTok, YouTube Shorts | 1 of 2/week |
| **Wednesday** | 6 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Thursday** | 6 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Friday** | 7 PM ET | **VIDEO** | Instagram Reels, TikTok, YouTube Shorts | 2 of 2/week |
| **Saturday** | 5 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Sunday** | 6 PM ET | General Post | Instagram Feed, Facebook | Weekly |

### Reclaim & Rise Now (Men 45-55)
| Day | Time | Type | Platforms | Frequency |
|-----|------|------|-----------|-----------|
| **Monday** | 7 PM ET | **VIDEO** | Instagram Reels, TikTok, YouTube Shorts | 1 of 2/week |
| **Tuesday** | 7 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Wednesday** | 6 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Thursday** | 6 PM ET | **VIDEO** | Instagram Reels, TikTok, YouTube Shorts | 2 of 2/week |
| **Friday** | 7 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Saturday** | 5 PM ET | General Post | Instagram Feed, Facebook | Weekly |
| **Sunday** | 6 PM ET | General Post | Instagram Feed, Facebook | Weekly |

---

## Weekly Content Breakdown

```
Per Brand Per Week:
├── 2 Video Posts (15-second, 9:16 vertical)
│   ├── Video 1: Problem/ROI or Science focus
│   └── Video 2: Transformation/Solution focus
│
└── 5 General Posts (Images, Carousels, Educational)
    ├── Educational Carousel (3-5 slides with product info)
    ├── Testimonial/Before-After
    ├── Tips/Actionable Content
    ├── Offer/Limited-Time Promotion
    └── Brand-Building/Inspirational

Total: 14 posts per week (7 per brand)
Monthly: 56+ assets (16 videos + 40 images)
```

---

## Platform Distribution

### Video Posts (2x per week per brand)
**Platforms:** Instagram Reels → TikTok → YouTube Shorts

- **Format:** 15-second, 9:16 vertical aspect ratio
- **Codec:** H.264 video, AAC audio
- **Content:** Problem/ROI hooks, transformation stories, testimonials
- **CTA:** Soft — "Tap link in bio" / "Link in bio for full breakdown"
- **Reach Strategy:** Algorithm-optimized short-form content

### General Posts (5x per week per brand)
**Platforms:** Instagram Feed → Facebook

- **Format:** Image carousel (3-5 slides) or single image
- **Content:** Educational content, product showcases, testimonials, offers
- **CTA:** Hard — Direct Gumroad URL with pricing
- **Reach Strategy:** Feed + community engagement

### Multi-Platform Posting Flow
```
New Video Generated
    ↓
Optimized for 9:16 (15s max)
    ↓
Posted simultaneously to:
├── Instagram Reels (with hashtags + soft CTA)
├── TikTok (with trending sound + on-brand text)
└── YouTube Shorts (with card + pinned comment)

General Post Generated
    ↓
Optimized for platform specs
    ↓
Posted to:
├── Instagram Feed (carousel with product link)
└── Facebook (carousel with CTA button)
```

---

## Automation Architecture

### Daily Triggers (14 Total)
Each trigger fires at scheduled time and creates a new session for:
1. **Content Generation** — New video or general post
2. **Multi-Platform Posting** — Simultaneous distribution
3. **Logging & Tracking** — Record all posts with IDs and metrics

**Trigger File:** `data/daily-triggers.json` (14 cron expressions)

### Orchestrator Scripts
- **daily-orchestrator.js** — Determines daily posting requirements
- **multi-platform-posting.js** — Executes posting to all platforms
- **asset-generator.js** — (Future) Auto-generates videos/images via Higgsfield

---

## Product Rotation (4-Week Cycle)

### Week 1: Problem/ROI Focus
- **Revitalize:** Perimenopause Guide ($39) + Hormone Meal Plan ($47)
- **Reclaim:** Hormone Meal Plan ($47) + Testosterone Boost ($49)

### Week 2: Science/Education
- **Revitalize:** Midlife Sleep Fix ($37) + Gut Health Reset ($39)
- **Reclaim:** Midlife Sleep Fix ($37) + Testosterone Boost ($49)

### Week 3: Transformation/Social Proof
- **Revitalize:** Burnout Recovery ($49) + Strength & Longevity ($59)
- **Reclaim:** Confidence Rebuild ($39) + Strength Training ($59)

### Week 4: Solution/Deep Dive
- **Revitalize:** 30-Day Workbook ($79) + Wellness Planner ($29)
- **Reclaim:** 30-Day Workbook ($79) + Mindset Reset ($37)

**Rotation Repeats:** Every 4 weeks to expose full product catalog

---

## Content Generation Pipeline

### Weekly Asset Generation Requirements

```
Revitalize:
├── 2 videos (15s, 9:16, seedance_2_0)
├── 5 general post images (carousel slides)
└── Total: 7 new assets per week

Reclaim:
├── 2 videos (15s, 9:16, seedance_2_0)
├── 5 general post images (carousel slides)
└── Total: 7 new assets per week

Combined: 4 videos + 10 images = 14 assets/week
Monthly: 16 videos + 40 images = 56 assets
```

### Video Generation (Higgsfield)
- **Model:** seedance_2_0 (optimal for 15s social content)
- **Duration:** 15 seconds (platform maximum)
- **Aspect Ratio:** 9:16 vertical
- **Diversity:** Rotate through ethnic backgrounds (African American, Asian, Indian, Latino, etc.)
- **Age Range:** 40-65 years old

### Image Generation (Higgsfield or Templates)
- **Carousel Posts:** 3-5 slide sequences with consistent branding
- **Template Types:** Educational, testimonial, offer, tips, product showcase

---

## CTA Framework

### Video Posts (Soft CTA)
```
"Tap the link in bio to learn more"
"Save this for later"
"Comments below - which resonates?"
"Your transformation is waiting"
```
*Placement:* Last 2-3 seconds of video + caption

### General Posts (Hard CTA)
```
"Get it now: [DIRECT_GUMROAD_URL]"
"Limited availability - $47 today"
"Your clarity starts at $39"
"Reclaim your edge: [URL]"
```
*Placement:* Caption text + carousel final slide

---

## Performance Metrics & Tracking

### Key Metrics by Platform
- **Instagram Reels:** Views, engagement rate, saves, click-through to bio
- **TikTok:** Views, watch time %, engagement, shares
- **YouTube Shorts:** Views, watch duration %, click-through
- **Facebook:** Engagement, shares, click-through rate
- **Conversions:** Link clicks → Gumroad purchases

### Weekly Review
- Which CTAs drive conversions?
- Which video hooks get highest retention?
- Which products convert best?
- Optimal posting times by platform?

### Monthly Analysis
- Revenue per product
- Most engaging content pillars
- Follower growth by platform
- Brand awareness metrics (mentions, searches)

### Quarterly Strategy
- Scale top 20% performing content
- Test new content pillars
- Adjust product rotation based on revenue
- Expand to new platforms based on performance

---

## Platform Setup Checklist

### ✅ Connected & Ready
- [x] Instagram Revitalize account (Composio API)
- [x] Higgsfield workspace (video generation)

### ⚠️ Pending Connection
- [ ] Instagram Reclaim account (manual setup in Composio)
- [ ] TikTok account (Composio TikTok connector)
- [ ] YouTube channel (YouTube Data API v3 + OAuth)
- [ ] Facebook page (Meta Graph API + app approval)

### Setup Instructions by Platform

#### Instagram Revitalize (Connected)
- Business Account: `@revitalize_thrive_now`
- User ID: `27164026169935796`
- Status: ✅ Ready for posting

#### Instagram Reclaim (Pending)
- Business Account: `@reclaim_and_rise_now`
- User ID: `27634679816148097`
- Status: ⚠️ Needs manual Composio connection
- Action: Connect in Composio → COMPOSIO_MANAGE_CONNECTIONS

#### TikTok Setup
1. Create Business Accounts: `@revitalize_thrive_now` + `@reclaim_and_rise_now`
2. Enable TikTok Creator Fund eligibility
3. Connect via Composio TikTok connector (requires OAuth)

#### YouTube Setup
1. Create brand channels for both brands
2. Enable YouTube Partner monetization (optional)
3. Set up playlists by content pillar
4. Connect via YouTube Data API v3

#### Facebook Setup
1. Create business pages for both brands
2. Link to brand business accounts
3. Enable commerce features (optional)
4. Connect via Meta Graph API with appropriate permissions

---

## File Structure

```
data/
├── brand-config.json          # Brand identity + product catalog
├── orchestrator-config.json   # Daily rotation + Higgsfield settings
├── daily-posting-schedule.json # 7-day schedule + platform strategy
├── daily-triggers.json        # 14 cron triggers for automation
├── orchestrator-log.json      # Posting history + metrics
└── posting-logs/              # Daily posting batch logs

scripts/
├── daily-orchestrator.js      # Main posting orchestrator
├── multi-platform-posting.js  # Platform-specific posting logic
└── asset-generator.js         # Higgsfield integration (future)
```

---

## Next Steps

1. **Generate Initial Assets** — Create first batch of 4 videos + 10 general post images
2. **Test Posting** — Manually post to 1 platform for each brand to verify workflow
3. **Enable Triggers** — Activate 14 daily automated triggers
4. **Monitor Performance** — Track metrics daily, optimize CTAs weekly
5. **Scale Content** — Add YouTube/Facebook once setup complete

---

## Support & Troubleshooting

### Video Generation Issues
- **Problem:** "Out of credits"
  - **Solution:** Add credits to Higgsfield workspace
  
- **Problem:** Video duration exceeds 15s
  - **Solution:** seedance_2_0 has 4-15s limit; use multiple shorts or kling3_0

### Posting Failures
- **Problem:** "Account not connected"
  - **Solution:** Verify Composio connection in COMPOSIO_MANAGE_CONNECTIONS
  
- **Problem:** "Invalid image format"
  - **Solution:** Ensure 9:16 aspect ratio, 1080x1920px minimum, MP4 codec

### Schedule Misalignment
- **Problem:** Posts not firing at scheduled time
  - **Solution:** Verify cron expression in data/daily-triggers.json matches timezone (ET)

---

## Contact & Updates
All posting logic controlled via configuration files — no code changes needed for adjustments.
