"""Validate the app's retained source records and publication data."""
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
COUNTS = {"VIC": 483, "WA": 364, "QLD": 277, "SA": 432, "NSW": 461}


def read(path):
    return json.loads((ROOT / path).read_text())


def source_url(value):
    url = urlsplit(value or "")
    return url.scheme == "https" and bool(url.netloc)


def validate():
    guides = read("data/pronunciations.json")
    audit = read("scripts/validation/source-audit.json")
    assert set(guides) == set(audit) == set(COUNTS)
    ids = set()
    for state, expected in COUNTS.items():
        records = read(f"data/{state.lower()}.json")
        source = audit[state]
        assert source["sourceCount"] == expected, state
        assert len(records) == source["importedCount"], state
        assert len(records) + len(source["duplicates"]) + len(source["unresolved"]) == expected, state
        assert not source["unresolved"], state
        keys = set()
        counts = Counter()
        classes = Counter()
        for row in records:
            assert row["id"] not in ids and row["id"].startswith(f"{state}-{row['postcode']}-"), row
            ids.add(row["id"])
            assert row["state"] == state and row["zone"] == ("B1" if state == "QLD" else "A"), row
            assert re.fullmatch(r"[0-9]{4}", row["postcode"]) and row["suburb"].strip(), row
            classification = row["consolidationClass"]
            key = row["postcode"], row["suburb"], classification
            assert key not in keys, row
            keys.add(key)
            if state == "NSW":
                assert classification[0] in "CMR" and row["ratingCombination"] == f"A-{classification[0]}", row
                classes[row["ratingCombination"]] += 1
            else:
                assert classification is None, row
            guide = guides[state][row["suburb"]]
            status = guide.get("verificationStatus", "needs_review")
            assert status in {"verified", "provisional", "needs_review"}, guide
            assert guide["phonetic"].strip(), guide
            if status in {"verified", "provisional"}:
                assert guide["phonetic"].strip() and source_url(guide["verificationSource"]), guide
                assert guide["sourceName"].strip() and guide["verificationNotes"].strip(), guide
            if guide.get("lastReviewed"):
                assert date.fromisoformat(guide["lastReviewed"]), guide
            for variant in guide.get("variants", []):
                assert variant["phonetic"].strip() and source_url(variant["source"]), guide
            if guide.get("audioUrl"):
                audio = guide["audioUrl"]
                audio_status = guide["audioStatus"]
                assert audio_status in {"approved", "source_recording", "pending"}, guide
                if audio_status in {"approved", "source_recording"}:
                    target = (ROOT / audio).resolve()
                    assert target.is_relative_to(ROOT / "audio/verified") and target.is_file(), guide
                    assert guide["audioReviewNotes"].strip(), guide
                if audio_status == "approved":
                    assert status == "verified" and guide["lastReviewed"], guide
            counts[status] += 1
        assert guides[state].keys() == {key[1] for key in keys}, state
        if state == "NSW":
            assert classes == source["classes"] == {"A-C": 425, "A-M": 14, "A-R": 22}
        print(state, len(records), dict(counts))
    print(f"Validated {len(ids)} unique records.")

    names = read("data/names.json")
    for row in names:
        assert row["id"].startswith("name-") and row["id"] not in ids, row
        ids.add(row["id"])
        assert all(row[key].strip() for key in ("name", "nativeSpelling", "locale", "phonetic")), row
        assert row["australianUsage"]["label"].strip() and source_url(row["australianUsage"]["url"]), row
    print(f"Validated Australian usage citations for {len(names)} given names.")

    pilot = read("scripts/review/pilot.json")
    pilot_keys = {(row["state"], row["locality"]) for row in pilot}
    assert len(pilot_keys) == len(pilot) and len({name for _, name in pilot_keys}) == 100
    assert {state for state, _ in pilot_keys} == set(COUNTS)
    for row in pilot:
        guide = guides[row["state"]][row["locality"]]
        assert row["verificationStatus"] in {"verified", "provisional", "needs_review"}, row
        assert row["currentPhonetic"] and row["evidenceNotes"] and row["audioReviewStatus"], row
        if row["proposedCorrection"]:
            assert source_url(row["sourceUrl"]), row
        assert guide.get("lastReviewed"), row
    print(f"Validated the pilot for 100 spellings across {len(pilot)} state–locality records.")


if __name__ == "__main__":
    validate()
