const $ = id => document.getElementById(id);
const states = { ALL: 'All States', VIC: 'Victoria', WA: 'Western Australia',
  QLD: 'Queensland', SA: 'South Australia', NSW: 'New South Wales' };
const statuses = { verified: 'Verified', provisional: 'Provisional', needs_review: 'Draft · Needs Review' };
const synthesis = window.speechSynthesis;
const pageSize = 30;
const slowRate = .70;
const localPreview = ['localhost', '127.0.0.1'].includes(location.hostname);

let records = [];
let state = 'ALL';
let page = 0;
let practiceQueue = [];
let current;
let revealed = false;
let lastRate = 1;
let audio;
let utterance;
let playbackVersion = 0;
let noticeTimer;
let voices = synthesis?.getVoices() ?? [];

synthesis?.addEventListener('voiceschanged', () => { voices = synthesis.getVoices(); });

function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

function button(label, callback, accessibleLabel) {
  const node = element('button', label);
  node.type = 'button';
  if (accessibleLabel) node.setAttribute('aria-label', accessibleLabel);
  node.addEventListener('click', callback);
  return node;
}

function notify(message) {
  clearTimeout(noticeTimer);
  $('playback-notice').textContent = message;
  if (message) noticeTimer = setTimeout(() => notify(''), 8500);
}

function stopPlayback() {
  playbackVersion += 1;
  audio?.pause();
  audio = undefined;
  synthesis?.cancel();
  utterance = undefined;
  notify('');
}

function speak(record, rate, version, recordingFailed) {
  if (!synthesis || !window.SpeechSynthesisUtterance) {
    notify(recordingFailed ? 'The recording could not be played.' : 'Speech playback is unavailable in this browser.');
    return;
  }
  const available = synthesis.getVoices();
  if (available.length) voices = available;
  const locale = record.locale ?? 'en-AU';
  const desired = findVoice(locale, Boolean(record.locale));
  const fallback = !desired && (record.fallbackLocale
    ? findVoice(record.fallbackLocale, true)
    : !record.locale && findVoice('en', true));
  if (record.locale && !desired && !fallback) {
    notify(`No ${record.language} voice is available on this device. Try the pronunciation source for ${record.name}.`);
    return;
  }
  const text = fallback && record.fallbackText ||
    record.speechOverride || record.nativeSpelling || record.suburb;
  utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = desired?.lang || fallback?.lang || locale;
  if (desired || fallback) utterance.voice = desired || fallback;
  utterance.rate = rate;
  utterance.onerror = () => {
    if (version === playbackVersion) notify('Device speech could not be played.');
  };
  const accent = desired ? `Using a ${record.language ?? 'Australian English'} device voice.`
    : fallback ? 'Using another device voice as an approximation.'
      : 'Requesting Australian English device speech.';
  const review = record.verificationStatus === 'verified' ? '' : ' This pronunciation still needs verification.';
  const speed = rate === 1 ? 'Normal speed.' : 'Slow speed requested (70%).';
  notify(`${recordingFailed ? 'Recording unavailable. ' : ''}${speed} ${accent}${review}`);
  synthesis.speak(utterance);
}

function findVoice(locale, matchLanguage) {
  const normal = code => code.toLowerCase().replaceAll('_', '-');
  const target = normal(locale);
  const exact = voices.filter(voice => normal(voice.lang) === target);
  const candidates = exact.length || !matchLanguage ? exact : voices.filter(voice =>
    normal(voice.lang).split('-')[0] === target.split('-')[0]);
  return candidates.find(voice => /premium|enhanced|natural/i.test(voice.name))
    ?? candidates.find(voice => voice.default) ?? candidates[0];
}

async function play(record, rate) {
  stopPlayback();
  lastRate = rate;
  const version = playbackVersion;
  if (!record.audioUrl && !localPreview) {
    speak(record, rate, version, false);
    return;
  }
  try {
    const source = record.audioUrl ?? `./__local_audio/${encodeURIComponent(record.id)}`;
    audio = new Audio(source);
    audio.playbackRate = rate;
    audio.preservesPitch = true;
    await audio.play();
    if (version !== playbackVersion) return;
    const speed = rate === 1 ? 'Normal speed' : 'Slow speed (70%)';
    const voiceLabel = record.audioUrl ? 'Speaker recording.'
      : record.fallbackLocale ? 'Approximate device pronunciation.'
        : `${record.language ?? 'Australian English'} device voice.`;
    notify(`${speed}. ${voiceLabel}`);
  } catch {
    if (version !== playbackVersion) return;
    audio?.pause();
    audio = undefined;
    speak(record, rate, version, Boolean(record.audioUrl));
  }
}

function audioControls(record, repeat = false) {
  const label = record.name ?? record.suburb;
  const actions = [
    button('Listen', () => play(record, 1), `Listen to ${label}`),
    button('Slow', () => play(record, slowRate), `Listen slowly to ${label}`)
  ];
  if (repeat) actions.push(button('Repeat Audio', () => play(record, lastRate)));
  return actions;
}

function pronunciation(record) {
  const group = element('div', '');
  const line = element('div', '', 'pron-line');
  line.append(element('span', record.phonetic ?? 'Guide pending', 'phonetic'));
  line.append(element('span', statuses[record.verificationStatus], `badge ${record.verificationStatus}`));
  group.append(line);
  for (const variant of record.variants ?? []) {
    const note = element('p', `Local variant: ${variant.phonetic} `, 'location');
    const link = element('a', 'Source');
    link.href = variant.source;
    note.append(link);
    group.append(note);
  }
  if (record.verificationSource) {
    const source = element('a', 'Pronunciation source', 'source');
    source.href = record.verificationSource;
    source.setAttribute('aria-label', `Pronunciation source for ${record.name ?? record.suburb}`);
    group.append(source);
  }
  if (record.recordingSource) {
    const link = element('a', 'Recording credit', 'source recording-credit');
    link.href = record.recordingSource;
    group.append(link);
  }
  return group;
}

function normalise(value) {
  return value.toLocaleLowerCase('en-AU').replaceAll('đ', 'dj').replaceAll('ł', 'l')
    .normalize('NFD').replace(/\p{M}/gu, '')
    .replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
}

function searchRank(record, query) {
  const name = record.searchName;
  const postcode = record.postcode;
  if (name === query || postcode === query) return 0;
  if (name.startsWith(query) || postcode.startsWith(query)) return 1;
  if (query.split(' ').every(term => name.includes(term) || postcode.includes(term))) return 2;
  return Infinity;
}

function renderDirectory() {
  const query = normalise($('query').value);
  const withGuides = $('with-guides').checked;
  const matches = records.filter(r => (state === 'ALL' || r.state === state) &&
      (!withGuides || Boolean(r.verificationSource)))
    .map(record => ({ record, rank: searchRank(record, query) }))
    .filter(result => Number.isFinite(result.rank))
    .sort((a, b) => a.rank - b.rank ||
      (!query ? Number(Boolean(b.record.verificationSource)) - Number(Boolean(a.record.verificationSource)) : 0));
  const totalPages = Math.ceil(matches.length / pageSize);
  const start = page * pageSize;
  $('results-status').textContent = matches.length
    ? `${start + 1}–${Math.min(start + pageSize, matches.length)} of ${matches.length.toLocaleString('en-AU')} results`
    : '0 results';
  const rows = document.createDocumentFragment();
  for (const { record } of matches.slice(start, start + pageSize)) {
    const row = $('row-template').content.cloneNode(true);
    row.querySelector('.locality').textContent = record.suburb;
    row.querySelector('.location').textContent = `${record.postcode} · ${states[record.state]}`;
    row.querySelector('.pronunciation').append(pronunciation(record));
    row.querySelector('.audio-controls').append(...audioControls(record));
    rows.append(row);
  }
  if (!matches.length) rows.append(element('p', withGuides
    ? 'No written guides match. Clear the written-guide filter to see all matching localities.'
    : 'No matching localities. Try another suburb or postcode, or select All States.', 'empty'));
  $('results').replaceChildren(rows);
  $('pages').hidden = totalPages < 2;
  $('page-number').textContent = `Page ${page + 1} of ${totalPages}`;
  $('previous').disabled = page === 0;
  $('next-page').disabled = page >= totalPages - 1;
}

function refillQueue() {
  const filter = $('practice-state').value;
  const verifiedOnly = $('verified-only').checked;
  const candidates = records.filter(record =>
    (filter === 'ALL' || record.state === filter) &&
    (!verifiedOnly || record.verificationStatus === 'verified'));
  practiceQueue = [...new Map(candidates.map(record => [
    JSON.stringify([record.state, record.suburb]), record
  ])).values()];
  for (let i = practiceQueue.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [practiceQueue[i], practiceQueue[j]] = [practiceQueue[j], practiceQueue[i]];
  }
  if (practiceQueue.length > 1 && practiceQueue.at(-1) === current) {
    [practiceQueue[0], practiceQueue[practiceQueue.length - 1]] =
      [practiceQueue.at(-1), practiceQueue[0]];
  }
}

function nextSuburb() {
  stopPlayback();
  if (!practiceQueue.length) refillQueue();
  current = practiceQueue.pop();
  revealed = false;
  lastRate = 1;
  $('answer').replaceChildren();
  $('reveal').hidden = !current;
  $('reveal').setAttribute('aria-expanded', 'false');
  $('practice-actions').hidden = !current;
  $('practice-name').replaceChildren();
  if (!current) {
    $('practice-name').append(element('p', 'No verified pronunciations for this selection. Choose another state or clear the verified-only filter.'));
    return;
  }
  $('practice-name').append(element('h2', current.suburb),
    element('p', `${current.postcode} · ${states[current.state]}`, 'location'));
}

function showView() {
  stopPlayback();
  const view = ['#names', '#practice'].includes(location.hash) ? location.hash : '#directory';
  for (const id of ['directory', 'names', 'practice']) $(id).hidden = view !== `#${id}`;
  for (const link of document.querySelectorAll('.top nav a')) {
    if (link.hash === view) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  if (view === '#practice' && !current && records.length) nextSuburb();
}

async function loadJson(file) {
  const response = await fetch(`./data/${file}.json`);
  if (!response.ok) throw new Error(`Could not load ${file} (${response.status})`);
  return response.json();
}

async function initialiseNames() {
  try {
    const names = (await loadJson('names')).map(record => ({
      ...record,
      searchTerms: [record.name, record.nativeSpelling, ...record.aliases]
        .map(normalise)
    })).sort((a, b) => a.name.localeCompare(b.name, 'en-AU'));
    const select = $('name-language');
    const languages = [...new Set(names.map(record => record.language))].sort();
    for (const language of languages) select.append(new Option(language, language));

    function renderNames() {
      const query = normalise($('name-query').value);
      const matches = names.filter(record =>
        (!select.value || record.language === select.value) &&
        record.searchTerms.some(term => term.includes(query)))
        .sort((a, b) => Number(b.searchTerms.includes(query)) - Number(a.searchTerms.includes(query)));
      $('names-status').textContent = `${matches.length} ${matches.length === 1 ? 'name' : 'names'}`;
      const rows = document.createDocumentFragment();
      for (const record of matches) {
        const row = $('row-template').content.cloneNode(true);
        row.querySelector('.locality').textContent = record.name;
        const location = row.querySelector('.location');
        if (record.nativeSpelling !== record.name) {
          const spelling = element('span', record.nativeSpelling);
          spelling.lang = record.locale;
          location.append(spelling, ' · ');
        }
        location.append(record.language);
        const evidence = element('a', 'Australian usage', 'source name-evidence');
        evidence.href = record.australianUsage.url;
        evidence.title = record.australianUsage.label;
        evidence.setAttribute('aria-label', `Australian usage for ${record.name}. ${record.australianUsage.label}`);
        location.append(evidence);
        row.querySelector('.pronunciation').append(pronunciation(record));
        row.querySelector('.audio-controls').append(...audioControls(record));
        rows.append(row);
      }
      if (!matches.length) rows.append(element('p', 'No matching names. Try a different spelling or language.', 'empty'));
      $('names-results').replaceChildren(rows);
    }

    $('name-query').addEventListener('input', renderNames);
    select.addEventListener('change', renderNames);
    renderNames();
  } catch (error) {
    console.error(error);
    $('names-status').textContent = 'Names could not be loaded. Reload to try again.';
  }
}

async function initialise() {
  showView();
  window.addEventListener('hashchange', showView);
  const groups = Object.keys(states).slice(1);
  try {
    const [guides, drafts, ...datasets] = await Promise.all([
      loadJson('pronunciations'), loadJson('draft-guides'), ...groups.map(code => loadJson(code.toLowerCase()))
    ]);
    records = datasets.flat().map(record => ({
      phonetic: drafts[record.state]?.[record.suburb] ?? null, speechOverride: null, audioUrl: null,
      verificationStatus: 'needs_review', verificationSource: null,
      ...record, ...guides[record.state]?.[record.suburb],
      searchName: normalise(record.suburb)
    })).sort((a, b) => a.suburb.localeCompare(b.suburb, 'en-AU') ||
      a.postcode.localeCompare(b.postcode) || a.state.localeCompare(b.state));

    for (const [code, label] of Object.entries(states)) {
      const tab = button(code === 'ALL' ? label : code, () => {
        state = code;
        page = 0;
        for (const filter of $('states').children) {
          filter.setAttribute('aria-pressed', String(filter === tab));
        }
        renderDirectory();
      }, code === 'ALL' ? label : `${code} · ${label}`);
      tab.setAttribute('aria-pressed', String(code === 'ALL'));
      $('states').append(tab);
      const option = element('option', label);
      option.value = code;
      $('practice-state').append(option);
    }

    $('query').addEventListener('input', () => { page = 0; renderDirectory(); });
    $('with-guides').addEventListener('change', () => { page = 0; renderDirectory(); });
    for (const [id, step] of [['previous', -1], ['next-page', 1]]) {
      $(id).addEventListener('click', () => {
        page += step;
        renderDirectory();
        if ($(id).disabled) $(step === 1 ? 'previous' : 'next-page').focus();
        $('results').scrollIntoView({ block: 'start' });
      });
    }
    for (const id of ['practice-state', 'verified-only']) {
      $(id).addEventListener('change', () => { refillQueue(); nextSuburb(); });
    }
    $('next-suburb').addEventListener('click', nextSuburb);
    $('skip').addEventListener('click', nextSuburb);
    $('shuffle').addEventListener('click', () => { refillQueue(); nextSuburb(); });
    $('reveal').addEventListener('click', () => {
      if (revealed || !current) return;
      revealed = true;
      const actions = element('div', '', 'actions');
      actions.append(...audioControls(current, true));
      $('answer').append(pronunciation(current), actions);
      $('reveal').setAttribute('aria-expanded', 'true');
    });
    $('reveal').setAttribute('aria-controls', 'answer');
    $('reveal').setAttribute('aria-expanded', 'false');
    renderDirectory();
    nextSuburb();
  } catch (error) {
    console.error(error);
    $('results-status').textContent = 'Directory unavailable';
    $('practice').querySelector('.practice-card').hidden = true;
    $('load-error').textContent = 'Locality data could not be loaded. Open the library through its web address and reload.';
    $('load-error').hidden = false;
  }
}

initialise();
initialiseNames();
