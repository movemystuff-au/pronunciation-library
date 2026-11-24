# Local pronunciation review

The public site reads the master `data/pronunciations.json` file. It contains one guide per exact spelling and state. Postcode rows in the five coverage files reference that guide through their existing state and locality fields. A cross-state match remains separate unless the pronunciations have been independently established. Keep the exact locality name and state from the coverage source.

## Review a locality

Run these commands from the repository root:

```sh
python3 scripts/review/pronunciations.py search Coogee
python3 scripts/review/pronunciations.py show WA Coogee
python3 scripts/review/pronunciations.py preview WA Coogee
python3 scripts/review/pronunciations.py preview QLD Indooroopilly --override 'In droo pilly'
python3 scripts/validation/validate.py
```

The preview requires macOS. Start `python3 scripts/preview.py` to audition both media rates in a browser. Restart it after saving a speech override so its local synthesis route reloads the master file. The website only reads data. Review edits happen through the local command line.

To save a change, run `python3 scripts/review/pronunciations.py edit STATE "Exact locality" --reviewer "Initials"` with the relevant options from `edit --help`. Use `--phonetic` to change the reading aid, `--source` and `--source-name` to record its evidence, `--notes` to explain the match and `--status` to set the assessment. Use `--override` for independently tested speech input, and `--override ""` to clear it. Updates record the review date and old and new values in the locality’s history.

## Evidence and spelling

- Search Australian sources for the exact locality before interpreting a spelling. Check that a source is about the right state, locality and dialect. A namesake, electorate or historical etymology may require a different spoken form.
- Prefer direct Australian evidence, such as an ABC Pronounce entry naming the locality, an authorised local recording, or a Traditional Owner organisation’s guidance. Record where a traditional name or pronunciation applies before carrying it into an employee guide.
- Use short English syllables joined with hyphens and capitalise the primary stress. Use `uh` for a reduced vowel, `oo` as in *food*, `uu` as in *put*, and `eye` or `ye` for the sound in *my*. Avoid adding an audible R after a vowel in an Australian pronunciation unless the source supports it. Keep IPA in the optional `ipa` field.
- Use Verified after checking faithful transcription against reliable evidence. Provisional is for limited evidence. Needs Review is for uncertain or generated readings. Retain independently supported local variants with their context in the `variants` entries and cite each separately.
- The [pilot log](pilot.json) is a dated assessment of 100 exact spellings. It has 101 state–locality rows because Coogee is reviewed separately in WA and NSW. It records the previous reading, proposed correction, evidence and audio state. Later manual edits belong in the master history rather than overwriting the pilot snapshot.

## Generate and approve audio

Google Cloud supports Australian English voices and SSML phonemes. The offline authoring script builds a dry-run request locally by default. It can submit one synthesis request only when run with `--execute`, Application Default Credentials and a billing-enabled project. Some voice families, including Chirp 3 HD, have different SSML support. The default request uses Neural2. [Australian voices](https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types) · [Australian phoneme support](https://docs.cloud.google.com/text-to-speech/docs/phonemes) · [Google Cloud setup](https://docs.cloud.google.com/text-to-speech/docs/create-audio)

```sh
python3 scripts/review/generate_audio.py NSW Bondi
python3 scripts/review/generate_audio.py NAME Aisha --voice en-AU-Neural2-A
python3 scripts/review/generate_audio.py NAME Aisha --voice en-AU-Neural2-D
```

Generate a candidate outside the repository, listen at both speeds, and compare the vowels, consonants and stress against the cited source. Check clarity and clipping. When it passes, copy the file into `audio/verified/` and use `edit` with `--audio ./audio/verified/filename.wav --audio-status approved --audio-notes "Listening review details"`. Approved audio requires a verified written guide. Pending candidates are excluded from playback. Existing attributed recordings retain their speaker-recording label. Hosted playback falls back to device speech with a clear synthesis notice.

The `NAME` option only prepares review candidates for sourced Australian English given names. Aisha’s candidate uses the English IPA from Cambridge as its input. Compare a female and male Neural2 voice against the same IPA before adopting a model. One candidate can supply both playback speeds after review.

The pilot checked the public [ABC Pronounce database](https://www2b.c0.abc.net.au/abcpronunciation-external/) and supplemented it with local sources when available. The [Macquarie Australian Place Names dataset](https://www.macquariedictionary.com.au/australian-place-names/) was identified, but licensed dataset access was unavailable for this pilot.

To run the browser checks, start the local preview, then run `node scripts/validation/browser.cjs` with Playwright and Chrome available. If Playwright lives outside the repository, set `MMS_PLAYWRIGHT` to its installed module directory. Use `MMS_PREVIEW_URL` to override the loopback preview address.
