"""Extract the approved tables from the original PDFs and NSW workbook."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from openpyxl import load_workbook
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PDFS = {"VIC": (483, (2, 3, 4)), "WA": (364, (2, 3, 4)), "QLD": (277, (2, 3)), "SA": (432, (2, 3, 4))}
FACILITY = re.compile(
    r"\b(?:po|gpo|dc|bc|cbd|rgh|hospital|university|campus|delivery cent(?:re|er)|"
    r"business cent(?:re|er)|shopping cent(?:re|er)|post office|terminal)\b", re.I
)


def pdf_rows(path, pages):
    pdf = PdfReader(path)
    for number in pages:
        page = pdf.pages[number - 1].extract_text(extraction_mode="layout")
        for line, text in enumerate(page.splitlines(), 1):
            if re.match(r"\s*(?:ZONE B|B2)\s+(?:\||•)", text):
                break
            if not re.match(r"\s*\d{4}(?=\s|$)", text):
                continue
            cells = re.split(r"(?:^\s*|\s{2,})(\d{4})(?=\s|$)", text)
            for postcode, suburb in zip(cells[1::2], cells[2::2]):
                yield postcode, suburb.strip(), None, f"page {number}, text line {line}"


def nsw_rows(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book["NSW Postcode Coverage"]
        for line, row in enumerate(sheet.values, 1):
            if row and row[0] == "A":
                _, original_class, _, _, postcode, suburb, rating, *_ = row
                if rating not in {"A-C", "A-M", "A-R"} or not original_class.startswith(rating[-1]):
                    raise ValueError(f"Unexpected assignment on NSW row {line}")
                yield str(postcode), suburb or "", original_class, f"NSW Postcode Coverage row {line}"
    finally:
        book.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()
    audit = {}
    for state in (*PDFS, "NSW"):
        zone = "B1" if state == "QLD" else "A"
        if state == "NSW":
            path = args.workbook
            rows = list(nsw_rows(path))
            expected = len(rows)
        else:
            expected, pages = PDFS[state]
            path = args.pdf_directory / f"{state} POSTCODE COVERAGE.pdf"
            rows = list(pdf_rows(path, pages))
        if not expected or len(rows) != expected:
            raise ValueError(f"{state}: expected {expected}, extracted {len(rows)}")
        records = {}
        stats = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "sourceCount": expected, "duplicates": [], "unresolved": [], "questionable": []}
        for postcode, suburb, classification, locator in rows:
            if not re.fullmatch(r"\d{4}", postcode) or not suburb.strip():
                stats["unresolved"].append([postcode, suburb, locator])
                continue
            key = (state, zone, postcode, suburb, classification)
            if key in records:
                stats["duplicates"].append([postcode, suburb, classification, locator])
                continue
            digest = hashlib.sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()[:16]
            record = dict(id=f"{state}-{postcode}-{digest}", state=state, zone=zone,
                          postcode=postcode, suburb=suburb, consolidationClass=classification,
                          sourceLocation=locator)
            if state == "NSW":
                record["ratingCombination"] = f"A-{classification[0]}"
            if FACILITY.search(suburb) or suburb in {"Saint Helena", "St Helena", "Saint Lucia", "St Lucia"}:
                stats["questionable"].append([postcode, suburb, locator])
            records[key] = record
        stats["importedCount"] = len(records)
        stats["classes"] = dict(Counter(r["ratingCombination"] for r in records.values() if state == "NSW"))
        audit[state] = stats
        (ROOT / "data" / f"{state.lower()}.json").write_text(
            json.dumps(list(records.values()), ensure_ascii=False, indent=2) + "\n"
        )
    (ROOT / "scripts/validation/source-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
