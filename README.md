# Australian Suburb Pronunciation Library

A Move My Stuff employee training directory for VIC, WA, QLD, SA and NSW. Search by suburb or postcode, filter by state, and use Pronunciation Practice to work through a shuffled set of names. Practice starts with verified written guides.

## Run locally

From the repository root, run:

```sh
python3 scripts/preview.py
```

Open [the local library](http://127.0.0.1:8765/). Serve the files over HTTP so the browser can load the JSON datasets. The app runs without a build step. On a Mac with the Australian Karen voice installed, the optional preview server produces speech on demand at a normal conversational rate. Both buttons play the same audio clip. The preview binds to this machine only. GitHub Pages serves the static files and uses browser speech for names without a recording.

## Publish on GitHub Pages

Push this repository to a new GitHub repository. In that repository’s **Settings → Pages**, select **Deploy from a branch**, then **main** and **/ (root)**. The site uses relative URLs and includes `.nojekyll`. See [GitHub Pages publishing settings](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Update the directory

The five state files in `data/` contain the imported source names, postcodes, classifications and source locations. The app normalises names in memory for search. The NSW workbook is read using saved cell values from the **NSW Postcode Coverage** sheet.

To regenerate source records, install `pypdf` and `openpyxl` in a Python environment, then run:

```sh
python3 scripts/validation/import_sources.py "/path/to/pdf-directory" "/path/to/NSW workbook.xlsx"
python3 scripts/validation/validate.py
```

The importer regenerates the five state files and the source audit while retaining the pronunciation master. If coverage changes, review the new source totals and zone boundaries before updating the validator. See [the validation report](VALIDATION.md).

## Add or review pronunciations

Add guides to `data/pronunciations.json` under the state code and exact source locality name. Records with the same state and name share a guide. An omitted sourced guide uses the separate draft guide and stays marked Draft · Needs Review. Generate candidate drafts outside the repository with `python3 scripts/build_draft_guides.py /tmp/locality-drafts.json` in an environment with `piper-tts`. The master includes the existing draft spellings. The older draft file is retained as the pre-review baseline. The generator uses eSpeak NG’s British English phonemiser as a non-rhotic spelling approximation. Drafts may be wrong for local names and are never used as speech input.

- **Verified** requires a written guide and a source that supports the local pronunciation.
- **Provisional** is for an evidence-based guide still awaiting confirmation.
- **Needs Review** is for unavailable or unresolved pronunciations. Keep uncertain spellings blank until there is evidence.

Use hyphens to separate syllables and capitals to mark the stressed syllable. Prefer ABC pronunciation resources, Australian dictionary entries and local recordings. Where appropriate, consult the relevant local language organisation or naming authority. Record sourced variants when more than one pronunciation is in use.

Use `speechOverride` only after listening to the result and confirming it against the source. For a recording cleared for playback, add its HTTPS URL or a relative path under `./audio/verified/` as `audioUrl`. A verified recording takes precedence over device speech. Recordings play at the original pace or at 70% speed. If a recording is unavailable, the library uses device speech and prefers an Australian English voice. Device speech can differ from local usage. See [recording credits](audio/README.md).

## General names

The General names tab lists given names with documented use in Australia. Search supports original scripts, alternative spellings and diacritics. Each record in `data/names.json` stores the pronunciation language, a provisional English reading aid, and a separate Australian usage citation. A registration can confirm a spelling or transliteration in use, while the pronunciation language describes the variant shown. The library does not estimate nationwide frequency.

Registration sources include the [NSW Registry top 100 series](https://www.data.nsw.gov.au/data/en/dataset/popular-baby-names-from-1952/resource/2adcb228-9101-4c95-a786-b3216539b4a2) and [South Australian registration records from 1944 to 2013](https://zenodo.org/records/11580348), republished by Pete Jones from South Australian Government data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Other entries cite Australian sport, university, arts and community profiles.

The macOS preview uses installed voices for each language. The preview reads Serbian and Bosnian Latin spellings with a Croatian voice and labels the result as approximate. Irish names use an explicitly marked Australian English approximation in this preview. In the static version, the browser tries the name’s language first and uses a configured approximation where available. A person’s own pronunciation takes precedence over the guide.

The [local review workflow](scripts/review/README.md) covers evidence, corrections, audio review and the pilot. See also the [baseline audit](PRONUNCIATION-AUDIT.md).
