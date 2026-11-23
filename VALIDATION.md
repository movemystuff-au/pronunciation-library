# Source extraction and validation

| State | Approved section | Source rows | Imported | Exact duplicates | Extraction issues | Flagged names | Verified guides on records | Provisional | Needs Review |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VIC | Zone A, PDF pages 2–4 | 483 | 483 | 0 | 0 | 18 | 11 | 1 | 471 |
| WA | Zone A, Perth Core, PDF pages 2–4 | 364 | 364 | 0 | 0 | 22 | 2 | 0 | 362 |
| QLD | Brisbane Metro B1, PDF pages 2–3 | 277 | 277 | 0 | 0 | 4 | 2 | 15 | 260 |
| SA | Zone A, PDF pages 2–4 | 432 | 432 | 0 | 0 | 21 | 5 | 1 | 426 |
| NSW | Zone A, NSW Postcode Coverage worksheet | 461 | 461 | 0 | 0 | 0 | 10 | 0 | 451 |
| **Total** | | **2,017** | **2,017** | **0** | **0** | **65** | **30** | **17** | **1,970** |

NSW contains 425 A-C, 14 A-M and 22 A-R rows. The attached workbook and the public project's `source.xlsx` have the same SHA-256 hash. The workbook describes these assignments as draft. [Public NSW workbook](https://github.com/priyanshbuilds/nsw-postcode-coverage/blob/main/source.xlsx)

The four PDFs use three pairs of postcode and suburb columns. Some sections continue across pages without repeating the heading. Others share a page with the next zone. Extraction used the printed section boundaries and reconciled each count with its PDF summary. All imported rows have a four-digit postcode and a locality name. Postcodes shared by different localities and localities listed against multiple postcodes are retained.

The [row-level audit](scripts/validation/source-audit.json) includes file hashes, exact duplicates, questionable records and unresolved extraction entries. Flagged records include facility abbreviations and possible aliases, such as Heidelberg Rgh, Joondalup Dc, Adelaide Bc and Saint Helena / St Helena. This pattern-based review does not establish whether a name is obsolete. All flagged records remain in the directory.

## Pronunciation and browser QA

Every record without a sourced guide has a generated written draft and is marked Draft · Needs Review. Verified and provisional written guides cover 47 source rows. Adelaide, Bondi and Bardon use Australian speaker recordings. The remaining entries use device speech. The local macOS preview renders this speech as a clip and applies the selected rate in the audio player. The full directory still requires pronunciation research and review before it can serve as the complete training reference.

The static data validator checks counts, coverage zones, NSW classifications, postcode and locality fields, unique identifiers, duplicate keys and required verification metadata. Chrome checks exercised exact and partial search, postcode search, all state filters, pagination, empty results, keyboard reveal, practice navigation, and the desktop and mobile layouts. Automated speech checks simulated voice availability, cancellation, normal and slow rates, and unsupported-browser fallback.
