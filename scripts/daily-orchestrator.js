#!/usr/bin/env node

/**
 * Daily Posting Orchestrator
 * Manages automated daily posts across Instagram, TikTok, YouTube, Facebook
 * 2 videos per week per brand + 5 general posts per week per brand
 */

const fs = require('fs');
const path = require('path');

const BRANDS = {
  revitalize: {
    name: 'Revitalize & Thrive Now',
    audience: 'Women 45-65',
    ig_handle: 'revitalize_thrive_now',
    ig_user_id: '27164026169935796',
    video_days: ['tuesday', 'friday'],
    video_times: ['23:00', '22:00'],
  },
  reclaim: {
    name: 'Reclaim & Rise Now',
    audience: 'Men 45-55',
    ig_handle: 'reclaim_and_rise_now',
    ig_user_id: '27634679816148097',
    video_days: ['monday', 'thursday'],
    video_times: ['23:00', '22:00'],
  },
};

const PLATFORMS = {
  instagram_reels: { name: 'Instagram Reels', supports_videos: true, supports_images: false },
  instagram_feed: { name: 'Instagram Feed', supports_videos: false, supports_images: true },
  tiktok: { name: 'TikTok', supports_videos: true, supports_images: false },
  youtube_shorts: { name: 'YouTube Shorts', supports_videos: true, supports_images: false },
  youtube_channel: { name: 'YouTube Channel', supports_videos: true, supports_images: false },
  facebook: { name: 'Facebook', supports_videos: true, supports_images: true },
};

const DAILY_SCHEDULE = {
  revitalize: {
    monday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '23:00' },
    tuesday: { type: 'video', platforms: ['instagram_reels', 'tiktok', 'youtube_shorts'], time: '23:00' },
    wednesday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '22:00' },
    thursday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '22:00' },
    friday: { type: 'video', platforms: ['instagram_reels', 'tiktok', 'youtube_shorts'], time: '23:00' },
    saturday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '21:00' },
    sunday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '22:00' },
  },
  reclaim: {
    monday: { type: 'video', platforms: ['instagram_reels', 'tiktok', 'youtube_shorts'], time: '23:00' },
    tuesday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '23:00' },
    wednesday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '22:00' },
    thursday: { type: 'video', platforms: ['instagram_reels', 'tiktok', 'youtube_shorts'], time: '22:00' },
    friday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '23:00' },
    saturday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '21:00' },
    sunday: { type: 'general', platforms: ['instagram_feed', 'facebook'], time: '22:00' },
  },
};

const PRODUCT_ROTATION = {
  week_1: {
    revitalize: ['perimenopause-guide', 'hormone-meal-plan'],
    reclaim: ['hormone-meal-plan', 'testosterone-boost'],
  },
  week_2: {
    revitalize: ['midlife-sleep-fix', 'gut-health-reset'],
    reclaim: ['midlife-sleep-fix', 'testosterone-boost'],
  },
  week_3: {
    revitalize: ['burnout-recovery', 'strength-longevity'],
    reclaim: ['confidence-rebuild', 'strength-training'],
  },
  week_4: {
    revitalize: ['30day-workbook', 'wellness-planner'],
    reclaim: ['30day-workbook', 'mindset-reset'],
  },
};

/**
 * Get current posting schedule for a given day and brand
 */
function getTodaySchedule(brand, dayOfWeek) {
  return DAILY_SCHEDULE[brand][dayOfWeek];
}

/**
 * Get current week number (1-4)
 */
function getCurrentWeek() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 1);
  const diff = now - start;
  const oneDay = 1000 * 60 * 60 * 24;
  const dayOfYear = Math.floor(diff / oneDay);
  const weekNumber = Math.ceil((dayOfYear + 1) / 7);
  return ((weekNumber - 1) % 4) + 1;
}

/**
 * Get featured products for current week
 */
function getFeaturedProducts(brand) {
  const week = `week_${getCurrentWeek()}`;
  return PRODUCT_ROTATION[week][brand];
}

/**
 * Generate posting instructions for the day
 */
function generateDailyPostingInstructions(brand, dayOfWeek) {
  const schedule = getTodaySchedule(brand, dayOfWeek);
  const products = getFeaturedProducts(brand);
  const brandConfig = BRANDS[brand];

  if (!schedule) {
    console.log(`No schedule found for ${brand} on ${dayOfWeek}`);
    return null;
  }

  const instruction = {
    brand,
    brand_name: brandConfig.name,
    day: dayOfWeek,
    type: schedule.type,
    time: schedule.time,
    platforms: schedule.platforms,
    products: products,
    timestamp: new Date().toISOString(),
  };

  if (schedule.type === 'video') {
    instruction.task = `Generate and post ${brand} VIDEO for ${dayOfWeek}`;
    instruction.details = {
      format: '15-second video (seedance_2_0)',
      aspect_ratio: '9:16',
      content: 'Problem/ROI or Transformation focus',
      cta: 'Soft CTA on videos - Link in bio',
      platforms: schedule.platforms,
    };
  } else {
    instruction.task = `Generate and post ${brand} GENERAL POST for ${dayOfWeek}`;
    instruction.details = {
      format: 'Image carousel or educational post',
      slides: '3-5 slides',
      content: 'Educational, testimonial, or offer-based',
      cta: 'Hard CTA with direct Gumroad URL',
      platforms: schedule.platforms,
    };
  }

  return instruction;
}

/**
 * Log posting activity
 */
function logPostingActivity(brand, dayOfWeek, instruction, result) {
  const logPath = path.join(__dirname, '../data/orchestrator-log.json');
  let logs = [];

  if (fs.existsSync(logPath)) {
    logs = JSON.parse(fs.readFileSync(logPath, 'utf8'));
  }

  const entry = {
    date: new Date().toISOString().split('T')[0],
    day_of_week: dayOfWeek,
    brand,
    instruction,
    result,
    status: result ? 'posted' : 'pending',
    timestamp: new Date().toISOString(),
  };

  logs.push(entry);
  fs.writeFileSync(logPath, JSON.stringify(logs, null, 2));
}

/**
 * Main execution
 */
function execute() {
  const now = new Date();
  const dayOfWeek = now.toLocaleDateString('en-US', { weekday: 'lowercase' });
  const hour = String(now.getHours()).padStart(2, '0');
  const minute = String(now.getMinutes()).padStart(2, '0');
  const currentTime = `${hour}:${minute}`;

  console.log(`\n=== Daily Posting Orchestrator ===`);
  console.log(`Time: ${now.toISOString()}`);
  console.log(`Day: ${dayOfWeek}`);
  console.log(`Current Time: ${currentTime}`);

  Object.keys(BRANDS).forEach((brand) => {
    const schedule = getTodaySchedule(brand, dayOfWeek);

    if (schedule) {
      const instruction = generateDailyPostingInstructions(brand, dayOfWeek);

      console.log(`\n[${brand.toUpperCase()}]`);
      console.log(`  Task: ${instruction.task}`);
      console.log(`  Scheduled Time: ${schedule.time}`);
      console.log(`  Platforms: ${schedule.platforms.join(', ')}`);
      console.log(`  Products: ${instruction.products.join(', ')}`);
      console.log(`  Status: Pending`);

      logPostingActivity(brand, dayOfWeek, instruction, false);
    }
  });
}

// Execute
execute();

module.exports = { getTodaySchedule, getFeaturedProducts, generateDailyPostingInstructions };
