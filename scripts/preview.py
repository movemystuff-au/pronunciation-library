"""Serve the static library locally, with optional macOS Australian speech."""
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "/__local_audio/"
GUIDES = json.loads((ROOT / "data/pronunciations.json").read_text())
NAME_VOICES = {
    "ar": "Majed", "el-GR": "Melina", "en-AU": "Karen", "hi-IN": "Lekha",
    "hr-HR": "Lana", "ja-JP": "Kyoko", "ko-KR": "Yuna", "pl-PL": "Zosia",
    "ru-RU": "Milena", "tr-TR": "Yelda", "uk-UA": "Lesya", "vi-VN": "Linh",
    "zh-CN": "Tingting",
}
ENTRIES = {
    row["id"]: ("Karen", GUIDES[state].get(row["suburb"], {}).get("speechOverride") or row["suburb"])
    for state in GUIDES
    for row in json.loads((ROOT / f"data/{state.lower()}.json").read_text())
}
for name in json.loads((ROOT / "data/names.json").read_text()):
    locale = name.get("fallbackLocale", name["locale"])
    ENTRIES[name["id"]] = (NAME_VOICES[locale], name.get("fallbackText", name["nativeSpelling"]))


@lru_cache(maxsize=128)
def render(voice, text):
    with TemporaryDirectory() as folder:
        aiff = Path(folder) / "speech.aiff"
        wav = Path(folder) / "speech.wav"
        subprocess.run(["/usr/bin/say", "-v", voice, "-r", "182", "-o", str(aiff), "--", text],
                       check=True, timeout=10, capture_output=True)
        subprocess.run(["/usr/bin/afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff), str(wav)],
                       check=True, timeout=10, capture_output=True)
        clip = wav.read_bytes()
        if len(clip) <= 64:
            raise ValueError("The system voice returned an empty clip")
        return clip


class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if not path.startswith(ROUTE):
            return super().do_GET()
        entry = ENTRIES.get(unquote(path[len(ROUTE):]))
        if not entry or sys.platform != "darwin":
            return self.send_error(404)
        try:
            clip = render(*entry)
        except (OSError, ValueError, subprocess.SubprocessError):
            return self.send_error(503, "Local Australian voice unavailable")
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(clip)))
        self.send_header("Cache-Control", "private, max-age=600")
        self.end_headers()
        try:
            self.wfile.write(clip)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(PreviewHandler, directory=ROOT)) as server:
        print(f"Preview at http://127.0.0.1:{args.port}/", flush=True)
        server.serve_forever()
