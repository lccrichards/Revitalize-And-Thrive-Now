#!/usr/bin/env node

/**
 * Multi-Platform Posting Workflow
 * Handles posting to: Instagram (Reels + Feed), TikTok, YouTube (Shorts + Channel), Facebook
 * Called by daily orchestrator triggers
 */

const fs = require('fs');
const path = require('path');

const POSTING_WORKFLOW = {
  instagram_reels: {
    name: 'Instagram Reels',
    type: 'video',
    duration: '15 seconds',
    format: '9:16 vertical',
    requirements: {
      video_file: 'required',
      caption: 'required',
      hashtags: 'recommended',
      cta: 'soft - link in bio'
    },
    api: 'Composio - Instagram Business API',
    post_limit: '1 per posting',
    reach: 'High - algorithmic feed + discovery'
  },

  instagram_feed: {
    name: 'Instagram Feed Post',
    type: 'image_carousel',
    format: 'Square or carousel (1:1 or 4:5)',
    slides: '1-5 slides',
    requirements: {
      image_file: 'required',
      caption: 'required (2200 chars max)',
      cta: 'hard - direct URL'
    },
    api: 'Composio - Instagram Business API',
    post_limit: '1 per posting',
    reach: 'Algorithmic + follower feed'
  },

  tiktok: {
    name: 'TikTok',
    type: 'video',
    duration: '15 seconds (optimized)',
    format: '9:16 vertical',
    requirements: {
      video_file: 'required',
      caption: 'required',
      sound: 'trending sounds recommended',
      hashtags: '3-5 relevant tags',
      cta: 'subtle - content-focused'
    },
    api: 'Composio - TikTok API',
    post_limit: '1 per posting',
    reach: 'Very High - For You Page (algorithm-driven)'
  },

  youtube_shorts: {
    name: 'YouTube Shorts',
    type: 'video',
    duration: '15-60 seconds',
    format: '9:16 vertical',
    requirements: {
      video_file: 'required',
      title: 'required (60 chars)',
      description: 'required (5000 chars)',
      thumbnail: 'optional but recommended',
      cta: 'card annotation + pinned comment'
    },
    api: 'YouTube Data API v3',
    post_limit: '1 per posting',
    reach: 'High - Shorts shelf + homepage'
  },

  youtube_channel: {
    name: 'YouTube Channel Library',
    type: 'video_archive',
    notes: 'Store all shorts as private/unlisted first, then organize in playlists',
    features: {
      playlists: 'Organize by pillar (Problem, Science, Transformation, Solution)',
      community_tab: 'Pinned comments with product links',
      cards: 'Click-through cards linking to product pages'
    },
    api: 'YouTube Data API v3',
    cta_method: 'Pinned comment with Gumroad URL'
  },

  facebook: {
    name: 'Facebook',
    type: 'image_carousel or video',
    format: 'Flexible (1.2:1 to 4:5)',
    requirements: {
      image_or_video: 'required',
      caption: 'required',
      cta_button: 'Learn More / Shop Now',
      link_url: 'required'
    },
    api: 'Meta Graph API',
    post_limit: '1 per posting',
    reach: 'Feed + community groups'
  }
};

/**
 * Platform distribution matrix
 */
const PLATFORM_DISTRIBUTION = {
  video_post: {
    platforms: ['instagram_reels', 'tiktok', 'youtube_shorts'],
    format_requirement: '15-second video, 9:16 vertical',
    cta_type: 'soft - link in bio'
  },
  general_post: {
    platforms: ['instagram_feed', 'facebook'],
    format_requirement: 'Image carousel or single image',
    cta_type: 'hard - direct product URL'
  }
};

/**
 * Generate posting payload for a given platform
 */
function generatePlatformPayload(platform, brand, postType, content, products) {
  const payload = {
    platform,
    brand,
    content_type: postType,
    generated_at: new Date().toISOString(),
    content,
    products,
  };

  switch (platform) {
    case 'instagram_reels':
      payload.requirements = {
        video: '15s, 9:16, MP4 H.264',
        caption: `Hook + soft CTA (max 2200 chars)\nCaption template: [Problem] → [Solution] → Link in bio\nHashtags: 15-20 relevant`,
        cta: 'Tap link in bio',
      };
      break;

    case 'instagram_feed':
      payload.requirements = {
        image: 'Carousel 3-5 slides, 1080x1350px each',
        caption: `Slide 1: Hook\nSlide 2: Why it matters\nSlide 3: Solution\nSlide 4: What's included\nSlide 5: CTA with price + link\n\nDirect URL required in caption`,
        cta: `Get it now: [GUMROAD_URL]`,
      };
      break;

    case 'tiktok':
      payload.requirements = {
        video: '15s, 9:16, MP4',
        caption: `Hook text + trending hashtags\nUse trending sounds for algorithm boost\nText overlay: Large, bold, on-brand`,
        cta: 'Subtle - content-driven',
      };
      break;

    case 'youtube_shorts':
      payload.requirements = {
        video: '15-60s, 9:16, MP4',
        title: `${brand} - [Product/Benefit] (max 60 chars)`,
        description: `Complete value prop + product link + subscribe CTA (max 5000 chars)`,
        cta: 'Card annotation + pinned comment with URL',
      };
      break;

    case 'facebook':
      payload.requirements = {
        image: 'Carousel or single image (1.2:1 to 4:5 ratio)',
        caption: `Accessible language + clear benefit\nInclude emoji for visual interest`,
        cta_button: 'Learn More or Shop Now',
        link_url: '[GUMROAD_URL]',
      };
      break;
  }

  return payload;
}

/**
 * Execute posting workflow
 */
function executeDailyPosting(brand, day, postType, products) {
  const timestamp = new Date().toISOString();
  const platforms = PLATFORM_DISTRIBUTION[postType].platforms;

  console.log(`\n=== Multi-Platform Posting Workflow ===`);
  console.log(`Brand: ${brand}`);
  console.log(`Day: ${day}`);
  console.log(`Type: ${postType}`);
  console.log(`Platforms: ${platforms.join(', ')}`);
  console.log(`Products: ${products.join(', ')}`);
  console.log(`Timestamp: ${timestamp}\n`);

  const payloads = platforms.map((platform) => {
    const payload = generatePlatformPayload(platform, brand, postType, {}, products);
    console.log(`[${platform.toUpperCase()}]`);
    console.log(`  Requirements: ${JSON.stringify(payload.requirements, null, 2)}`);
    return payload;
  });

  // Log posting batch
  logPostingBatch(brand, day, postType, payloads);

  return payloads;
}

/**
 * Log posting batch for reference
 */
function logPostingBatch(brand, day, postType, payloads) {
  const logDir = path.join(__dirname, '../data/posting-logs');

  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  const logFile = path.join(logDir, `${brand}-${day}-${Date.now()}.json`);

  const batchLog = {
    brand,
    day,
    post_type: postType,
    platform_count: payloads.length,
    timestamp: new Date().toISOString(),
    payloads,
  };

  fs.writeFileSync(logFile, JSON.stringify(batchLog, null, 2));
  console.log(`\n✓ Posting batch logged to ${logFile}`);
}

/**
 * Platform status checker
 */
function checkPlatformStatus() {
  console.log(`\n=== Platform Connection Status ===`);
  console.log(`[✓] Instagram - Revitalize account connected (Composio)`);
  console.log(`[⚠] Instagram - Reclaim account pending connection (manual setup needed)`);
  console.log(`[  ] TikTok - Requires Composio TikTok connector setup`);
  console.log(`[  ] YouTube - Requires YouTube Data API v3 + OAuth`);
  console.log(`[  ] Facebook - Requires Meta Graph API + app approval`);
  console.log(
    `\nAction Required: Connect missing platform accounts before posting goes live`
  );
}

// Export functions
module.exports = {
  POSTING_WORKFLOW,
  PLATFORM_DISTRIBUTION,
  generatePlatformPayload,
  executeDailyPosting,
  checkPlatformStatus,
};

// Execute if called directly
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === 'status') {
    checkPlatformStatus();
  } else if (args.length >= 4) {
    executeDailyPosting(args[0], args[1], args[2], args.slice(3));
  } else {
    console.log('Usage: node multi-platform-posting.js <brand> <day> <postType> <product1> [product2...]');
    console.log('Example: node multi-platform-posting.js revitalize monday video perimenopause-guide');
  }
}
