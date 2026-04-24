#!/usr/bin/env node
// Fetches today's class schedule from Crunch Allen's public location page,
// parses the "Today's Classes" section, tags each class by workout goal,
// and writes crunch-today.json at the repo root.
//
// Designed to run on GitHub Actions daily. No third-party deps — uses plain
// node:https + regex. The Crunch page is server-rendered, so no browser needed.

const https = require('https');
const fs = require('fs');
const path = require('path');

const URL = 'https://www.crunch.com/locations/allen';
const OUT = path.resolve(__dirname, '..', 'crunch-today.json');

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

function fetchHtml(url, maxRedirects = 5) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'locale=en'
      }
    }, (res) => {
      if ([301, 302, 307, 308].includes(res.statusCode) && res.headers.location && maxRedirects > 0) {
        const next = new URL(res.headers.location, url).toString();
        res.resume();
        return resolve(fetchHtml(next, maxRedirects - 1));
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`HTTP ${res.statusCode} on ${url}`));
      }
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (c) => { data += c; });
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.setTimeout(20000, () => req.destroy(new Error('timeout')));
  });
}

function decodeEntities(s) {
  return s
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ')
    .trim();
}

function parseClasses(html) {
  // The schedule items are rendered as:
  //   <li class="list-block__item__link">
  //     <p class="list-block__item__link__title type--e3 type--white">NAME</p>
  //     <p class="type--c5 type--gray-light"> TIME | DURATION | INSTRUCTOR</p>
  //   </li>
  const re = /<li class="list-block__item__link">[\s\S]*?<p class="list-block__item__link__title type--e3 type--white">([^<]+?)<\/p>\s*<p class="type--c5 type--gray-light">\s*([^<]+?)<\/p>/g;
  const out = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    const name = decodeEntities(m[1]);
    const meta = decodeEntities(m[2]);
    const parts = meta.split('|').map((p) => p.trim());
    const time = parts[0] || null;
    const durStr = parts[1] || '';
    const instructor = parts[2] || null;
    const durMatch = durStr.match(/(\d+)/);
    const duration = durMatch ? parseInt(durMatch[1], 10) : null;
    out.push({ name, time, duration, instructor, tags: classifyClass(name) });
  }
  return out;
}

// Map class name → goal tags.
// Returns array of: 'intervals' (HIIT-style), 'steady' (zone 2 cardio),
// 'not_cardio' (yoga, pilates, strength). A class can have both intervals+steady
// if it's a hybrid.
function classifyClass(name) {
  const n = name.toLowerCase();
  const tags = [];

  // Check cardio keywords FIRST — a class like "Strong-er HIIT" is a HIIT class
  // even though "Strong" is in the name. Cardio signals dominate.
  const intervals = [
    'hiit', 'tabata', 'ride45', 'ride 45', 'bootcamp', 'boot camp', 'insanity',
    'metcon', 'conditioning', 'interval', 'sprint'
  ];
  for (const k of intervals) if (n.includes(k)) { tags.push('intervals'); break; }

  const steady = [
    'zumba', 'dance', 'step', 'cycle', 'spin', 'the ride', 'ride',
    'cardio', 'fat burn', 'kickbox', 'kick box', 'aerobic',
    'box fit', 'groove', 'jazz'
  ];
  for (const k of steady) if (n.includes(k)) { tags.push('steady'); break; }

  if (tags.length > 0) return tags;

  // No cardio signal — check if it's clearly non-cardio.
  const nonCardio = [
    'yoga', 'pilates', 'barre', 'stretch', 'meditation', 'recovery',
    'mobility', 'foam roll', 'restorative',
    'body sculpt', 'sculpt', 'trx', 'bodyweb',
    'lift', 'strength', 'muscle', 'weights', 'camp crunch'
  ];
  for (const k of nonCardio) if (n.includes(k)) { tags.push('not_cardio'); return tags; }

  // Unknown — will be shown as a generic option, user can decide.
  tags.push('unknown');
  return tags;
}

function todayIsoDate() {
  // Crunch Allen is Central Time. Use America/Chicago via Intl.
  const fmt = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Chicago',
    year: 'numeric', month: '2-digit', day: '2-digit'
  });
  return fmt.format(new Date()); // YYYY-MM-DD
}

(async () => {
  try {
    const html = await fetchHtml(URL);
    const classes = parseClasses(html);
    const payload = {
      location: 'Crunch Allen',
      address: '510 N Watters Rd, Allen, TX 75013',
      phone: '469.824.3022',
      locationUrl: URL,
      scrapedAt: new Date().toISOString(),
      date: todayIsoDate(),
      classCount: classes.length,
      classes
    };
    fs.writeFileSync(OUT, JSON.stringify(payload, null, 2) + '\n');
    console.log(`Wrote ${OUT} with ${classes.length} classes for ${payload.date}`);
    if (classes.length === 0) {
      console.error('WARNING: no classes parsed — Crunch page structure may have changed.');
      process.exit(2); // non-fatal but flags the workflow as failed
    }
  } catch (err) {
    console.error('Scrape failed:', err.message);
    process.exit(1);
  }
})();
