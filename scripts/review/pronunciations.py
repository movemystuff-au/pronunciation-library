"""Read and maintain the locality pronunciation database from a local shell."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "data/pronunciations.json"
STATUSES = ("needs_review", "provisional", "verified")


def save(database):
    """Keep each locality on one line so changes stay readable in Git."""
    states = []
    for state, records in database.items():
        rows = [f"    {json.dumps(name, ensure_ascii=False)}: {json.dumps(row, ensure_ascii=False)}"
                for name, row in records.items()]
        states.append(f'  "{state}": {{\n' + ",\n".join(rows) + "\n  }")
    payload = "{\n" + ",\n".join(states) + "\n}\n"
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=DATABASE.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
    try:
        temporary.chmod(DATABASE.stat().st_mode & 0o777)
        os.replace(temporary, DATABASE)
    finally:
        temporary.unlink(missing_ok=True)


def https_url(value):
    url = urlsplit(value or "")
    return url.scheme == "https" and bool(url.hostname)


def validate_change(row):
    if row["verificationStatus"] in {"verified", "provisional"}:
        if not row.get("phonetic", "").strip() or not https_url(row.get("verificationSource")):
            raise ValueError("A sourced guide requires phonetic text and an HTTPS evidence URL.")
        if not row.get("sourceName") or not row.get("verificationNotes"):
            raise ValueError("Provide a source name and a note explaining what the evidence supports.")
    path = row.get("audioUrl")
    if path:
        target = (ROOT / path).resolve()
        if not path.startswith("./audio/verified/") or not target.is_relative_to(ROOT / "audio/verified"):
            raise ValueError("Use a relative asset path under ./audio/verified/.")
    if row.get("audioStatus") == "approved":
        if not path or not target.is_file():
            raise ValueError("Approved audio must exist under audio/verified.")
        if row["verificationStatus"] != "verified" or not row.get("audioReviewNotes"):
            raise ValueError("Approval requires a verified guide and notes from a listening review.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search", help="Find a locality and its status")
    search.add_argument("query")
    for command in ("show", "preview", "edit"):
        action = commands.add_parser(command)
        action.add_argument("state")
        action.add_argument("name")
        if command == "preview":
            action.add_argument("--slow", action="store_true")
            action.add_argument("--override", help="Preview proposed speech input before saving")
        if command == "edit":
            action.add_argument("--reviewer", required=True)
            action.add_argument("--status", choices=STATUSES)
            action.add_argument("--phonetic")
            action.add_argument("--ipa")
            action.add_argument("--source")
            action.add_argument("--source-name")
            action.add_argument("--notes")
            action.add_argument("--override")
            action.add_argument("--audio")
            action.add_argument("--audio-status", choices=("pending", "approved"))
            action.add_argument("--audio-notes")
    args = parser.parse_args()
    database = json.loads(DATABASE.read_text(encoding="utf-8"))
    if args.command == "search":
        for state, entries in database.items():
            for name, row in entries.items():
                if args.query.casefold() in name.casefold():
                    print(f"{state}\t{name}\t{row['phonetic']}\t{row['verificationStatus']}")
        return
    state = args.state.upper()
    name = args.name
    try:
        row = database[state][name]
    except KeyError:
        parser.error("Locality not found. Use search to get its exact state and spelling.")
    if args.command == "show":
        print(json.dumps({"state": state, "locality": name, **row}, indent=2, ensure_ascii=False))
        return
    if args.command == "preview":
        if sys.platform != "darwin":
            parser.error("The command-line preview requires macOS. The local website also supports browser speech.")
        clip = row.get("audioUrl")
        if args.override is None and clip and (ROOT / clip).is_file():
            if args.slow:
                parser.error("Use Slow in the local website to hear the recorded clip at 70%.")
            subprocess.run(["/usr/bin/afplay", str(ROOT / clip)], check=True)
        else:
            text = args.override or row.get("speechOverride") or name
            subprocess.run(["/usr/bin/say", "-v", "Karen", "-r", "127" if args.slow else "182", "--", text], check=True)
        return

    fields = {"status": "verificationStatus", "phonetic": "phonetic", "ipa": "ipa",
              "source": "verificationSource", "source_name": "sourceName", "notes": "verificationNotes",
              "override": "speechOverride", "audio": "audioUrl", "audio_status": "audioStatus",
              "audio_notes": "audioReviewNotes"}
    patch = {key: getattr(args, arg) or None for arg, key in fields.items()
             if getattr(args, arg) is not None and (getattr(args, arg) or None) != row.get(key)}
    if not patch:
        parser.error("Supply at least one changed field.")
    if not args.reviewer.strip():
        parser.error("Enter a reviewer name or initials.")
    if "audioUrl" in patch:
        patch["audioStatus"] = args.audio_status or "pending"
        patch["audioReviewNotes"] = args.audio_notes
    if args.audio_status == "approved" and not args.audio_notes:
        parser.error("Supply notes from this listening review before approving audio.")
    updated = {**row, **patch}
    try:
        validate_change(updated)
    except ValueError as error:
        parser.error(str(error))
    now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")
    updated["lastReviewed"] = now[:10]
    updated["reviewHistory"] = [*row.get("reviewHistory", []), {
        "at": now, "reviewer": args.reviewer.strip(),
        "changes": {key: {"before": row.get(key), "after": value} for key, value in patch.items()},
    }]
    database[state][name] = updated
    save(database)
    print(f"Saved {name}, {state} ({updated['verificationStatus']}).")


if __name__ == "__main__":
    main()
