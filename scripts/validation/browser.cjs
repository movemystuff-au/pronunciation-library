/* Run against scripts/preview.py with Playwright and Chrome available. */
const assert = require('node:assert/strict');
const { chromium } = require(process.env.MMS_PLAYWRIGHT || 'playwright');

async function check() {
  const browser = await chromium.launch({ channel: 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      const NativeAudio = window.Audio;
      window.audioEvents = [];
      window.speechEvents = [];
      window.Audio = class extends NativeAudio {
        constructor(source) {
          super(source);
          this.addEventListener('playing', () => window.audioEvents.push(['play', source, this.playbackRate]));
        }
        pause() {
          window.audioEvents.push(['pause', this.getAttribute('src')]);
          return super.pause();
        }
      };
      window.testVoices = [
        { name: 'US default test voice', lang: 'en-US', default: true },
        { name: 'British test voice', lang: 'en-GB', default: false }
      ];
      Object.defineProperty(window, 'speechSynthesis', { value: {
        getVoices: () => window.testVoices,
        addEventListener: () => {},
        cancel: () => {},
        speak: utterance => window.speechEvents.push([utterance.text, utterance.lang, utterance.rate])
      } });
      window.SpeechSynthesisUtterance = class {
        constructor(text) { this.text = text; }
      };
    });
    await page.goto(process.env.MMS_PREVIEW_URL || 'http://127.0.0.1:8765/');
    const search = page.locator('#query');
    await page.locator('#results .row').first().waitFor();
    const stateCounts = {
      'VIC · Victoria': 483, 'WA · Western Australia': 330, 'QLD · Queensland': 277,
      'SA · South Australia': 426, 'NSW · New South Wales': 460
    };
    for (const [label, count] of Object.entries(stateCounts)) {
      await page.getByRole('button', { name: label }).click();
      assert.match(await page.locator('#results-status').textContent(), new RegExp(`of ${count} results`));
    }
    await page.getByRole('button', { name: 'All States', exact: true }).click();
    assert.match(await page.locator('#results-status').textContent(), /of 1,976 results/);
    await search.fill('5839');
    assert.equal(await page.getByRole('heading', { name: 'Adelaide', exact: true }).count(), 1);
    assert.match(await page.locator('#results').textContent(), /5000, 5001, 5800, 5810, 5839/);
    await search.fill('coogee');
    assert.match(await page.locator('#results').textContent(), /KUU-jee/);
    assert.match(await page.locator('#results').textContent(), /KOO-jee/);
    await page.getByRole('button', { name: 'NSW · New South Wales' }).click();
    assert.match(await page.locator('#results').textContent(), /KUU-jee/);
    assert.doesNotMatch(await page.locator('#results').textContent(), /Western Australia/);
    await search.fill('2026');
    assert.equal(await page.getByRole('heading', { name: 'Bondi', exact: true }).count(), 1);
    const bondi = page.getByRole('button', { name: 'Listen to Bondi', exact: true });
    await bondi.click();
    await page.waitForFunction(() => window.audioEvents.some(item => item[0] === 'play'));
    await page.getByRole('button', { name: 'Listen slowly to Bondi', exact: true }).click();
    await page.waitForFunction(() => window.audioEvents.filter(item => item[0] === 'play').length === 2);
    const events = await page.evaluate(() => window.audioEvents);
    assert.deepEqual(events.map(item => item[0]), ['play', 'pause', 'play']);
    assert.equal(events[0][1], events[2][1]);
    assert.deepEqual([events[0][2], events[2][2]], [1, .7]);

    await page.route('**/audio/verified/bondi.wav', route => route.fulfill({ status: 404 }));
    await page.reload();
    await page.locator('#results .row').first().waitFor();
    await search.fill('bondi');
    await bondi.click();
    await page.waitForFunction(() => window.speechEvents.length === 1);
    assert.deepEqual(await page.evaluate(() => window.speechEvents[0]), ['Bondi', 'en-GB', 1]);
    assert.match(await page.locator('#playback-notice').textContent(), /Recording unavailable.*Synthesised playback/);

    await page.evaluate(() => { window.testVoices.pop(); });
    await bondi.click();
    await page.waitForFunction(() => document.querySelector('#playback-notice').textContent.includes('British English voice is unavailable'));
    assert.equal(await page.evaluate(() => window.speechEvents.length), 1);

    await page.unroute('**/audio/verified/bondi.wav');
    await page.route('**/data/pronunciations.json', async route => {
      const response = await route.fetch();
      const database = await response.json();
      database.NSW.Bondi.audioStatus = 'pending';
      await route.fulfill({ response, json: database });
    });
    await page.reload();
    await page.locator('#results .row').first().waitFor();
    await search.fill('bondi');
    await bondi.click();
    await page.waitForFunction(() => window.audioEvents.some(item => item[0] === 'play'));
    assert.match(await page.evaluate(() => window.audioEvents[0][1]), /__local_audio/);

    await page.getByRole('link', { name: 'Practice', exact: true }).click();
    await page.getByRole('button', { name: 'Reveal Pronunciation' }).click();
    assert.match(await page.locator('#answer').textContent(), /Verified/);

    await page.setViewportSize({ width: 375, height: 812 });
    await page.getByRole('link', { name: 'General names', exact: true }).click();
    await page.locator('#names-results .row').first().waitFor();
    assert.match(await page.locator('#names-status').textContent(), /87 names/);
    await page.locator('#name-query').fill('Dusan');
    assert.equal(await page.locator('#names-results h3').textContent(), 'Dušan');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 375);
    await page.getByRole('link', { name: 'Suburbs', exact: true }).click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 375);
    assert.deepEqual(errors, []);
    console.log('Desktop and mobile search, postcode, state filtering, guide variants, playback rates, cancellation, missing audio fallback, Practice and General names passed.');
  } finally {
    await browser.close();
  }
}

check().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
