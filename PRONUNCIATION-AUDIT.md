# Pronunciation audit before Phase 2

| Measure | Baseline |
| --- | ---: |
| Postcode–locality rows | 2,017 |
| Distinct locality spellings across the five states | 1,887 |
| Distinct state–locality pronunciation keys | 1,976 |
| Verified pronunciation keys | 26 |
| Provisional pronunciation keys | 17 |
| Needs Review pronunciation keys | 1,933 |

Counts use the exact source spelling. A locality repeated within a state already shares its guide across postcodes. Different states can have different pronunciations for the same spelling. For example, the WA and NSW entries for Coogee have separate guides and sources.

The baseline sourced file contained 43 guides. The other 1,933 came from eSpeak NG’s British English RP phonemiser and a rule-based conversion to English respelling. The generated entries are approximate spelling predictions. They were displayed with a review label. None were used as speech overrides.

The public browser code requests `en-AU`, preferring an available Australian English voice. Device voice inventory, accent and support for the requested speech rate vary. The local macOS preview synthesises suburb names with Karen and plays the resulting clip at 100% or 70%. Neither synthesis path confirms local pronunciation.

Adelaide, Bardon and Bondi link to existing attributed Australian speaker recordings. Adelaide is shared across five SA postcodes. Bondi is an extract from a longer recording. There were no manually defined locality speech overrides. The existing validator checked coverage totals, NSW classifications, identifiers and the presence of evidence URLs on verified entries.

## Phase 2 results

| Metric | Before | After |
| --- | ---: | ---: |
| Postcode–locality rows | 2,017 | 2,017 |
| Distinct locality spellings | 1,887 | 1,887 |
| Verified state–locality pronunciations | 26 | 62 |
| Provisional state–locality pronunciations | 17 | 13 |
| Needs Review state–locality pronunciations | 1,933 | 1,901 |

The first [pilot](scripts/review/pilot.json) covers 100 spellings across 101 state–locality keys. Coogee has separate WA and NSW entries. The pilot finished with 62 Verified, 13 Provisional and 26 Needs Review. It changed 45 written guides, while 36 keys gained Verified status. The whole library has 1,901 unresolved keys, plus 13 provisional keys awaiting stronger evidence.

The evidence pass used exact ABC headwords where their descriptions matched the relevant state and place. Local sources supplemented the ABC results. For example, the NSW Coogee guide uses the short vowel in *put*, the WA guide uses the long vowel in *food*, and the ABC Lalor entry names the federal electorate while the suburb uses a different form. The Cowandilla record links to Kaurna Warra Karrpanthi for language context and remains unresolved for the current suburb pronunciation.

Three existing audio assets passed file and signal checks, including peak levels below clipping. No new recording received listening approval. Existing recordings remain identified as speaker recordings, and the website skips pending audio. The Google Cloud generator was checked in dry-run mode. No cloud synthesis or billing was used.

The five coverage files, General Names data and UI layout files were compared with the baseline commit and match exactly. The validator checks directory counts, classifications, source fields, asset locations and pilot completeness. The local browser checks exercise desktop and mobile sizing, postcode and suburb search, each state tab, regional guides, playback, missing and pending audio handling, Practice and General Names.
