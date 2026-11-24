"""Prepare a single Australian clip for local listening review."""
import argparse
from html import escape
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", help="Locality state code, or NAME for a sourced Australian English given name")
    parser.add_argument("name")
    parser.add_argument("--voice", default="en-AU-Neural2-A")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--execute", action="store_true", help="Allow one billable Google Cloud request")
    args = parser.parse_args()
    if not args.voice.startswith("en-AU-"):
        parser.error("Choose an en-AU voice.")
    scope = args.state.upper()
    if scope == "NAME":
        names = json.loads((ROOT / "data/names.json").read_text())
        row = next((entry for entry in names if entry["name"] == args.name), None)
        if not row or row["locale"] != "en-AU" or not row.get("verificationSource"):
            parser.error("Select a sourced Australian English given name by exact spelling.")
    else:
        database = json.loads((ROOT / "data/pronunciations.json").read_text())
        row = database.get(scope, {}).get(args.name)
        if not row or row["verificationStatus"] != "verified":
            parser.error("Select a verified locality by exact spelling.")
    text = row.get("speechOverride") or args.name
    ssml = None
    if row.get("ipa") and len(args.name.split()) == 1:
        if "chirp" in args.voice.lower():
            parser.error("Choose Neural2, WaveNet or another SSML-compatible voice for IPA input.")
        ipa = escape(row["ipa"].strip("/[]"), quote=True)
        ssml = f'<speak><phoneme alphabet="ipa" ph="{ipa}">{escape(args.name)}</phoneme></speak>'
    plan = {"voice": args.voice, "languageCode": "en-AU", "audioEncoding": "LINEAR16",
            "input": {"ssml": ssml} if ssml else {"text": text}}
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    output = args.output or Path(tempfile.mkdtemp(prefix="mms-pronunciation-")) / "review.wav"
    output = output.resolve()
    if output.is_relative_to(ROOT) or output.suffix.lower() != ".wav" or output.exists():
        parser.error("Choose a new .wav file outside the repository.")
    if not output.parent.is_dir():
        parser.error("The output directory must already exist.")
    try:
        from google.cloud import texttospeech as tts
    except ImportError:
        parser.error("Install google-cloud-texttospeech and configure Application Default Credentials locally.")
    response = tts.TextToSpeechClient().synthesize_speech(
        input=tts.SynthesisInput(**plan["input"]),
        voice=tts.VoiceSelectionParams(language_code="en-AU", name=args.voice),
        audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16),
        retry=None, timeout=30,
    )
    with output.open("xb") as handle:
        handle.write(response.audio_content)
    print(f"Unreviewed candidate: {output}")


if __name__ == "__main__":
    main()
