"""Build clearly labelled draft respellings from eSpeak NG, without audio."""
import argparse
import json
from pathlib import Path
import re

from piper.phonemize_espeak import EspeakPhonemizer

ROOT = Path(__file__).resolve().parents[1]
VOWELS = dict(zip(
    "iː uː ɑː ɔː ɜː ɛː ɪə eə ʊə eɪ aɪ ɔɪ aʊ əʊ oʊ ɐʊ æ ɐ ʌ ɒ ɛ e ɪ i ʊ u ə ɜ a o ɑ ɔ".split(),
    "ee oo ah aw ur air eer air oor ay eye oy ow oh oh ow a uh uh o eh eh i ee uu oo uh ur a o ah aw".split()
))
CONSONANTS = {"tʃ": "ch", "dʒ": "j", "ʃ": "sh", "ʒ": "zh", "θ": "th",
              "ð": "th", "ŋ": "ng", "ɹ": "r", "ɡ": "g", "ɾ": "t", "ʔ": ""}
SYMBOLS = sorted(VOWELS.keys() | CONSONANTS.keys(), key=len, reverse=True)
TOKENS = re.compile("|".join(map(re.escape, SYMBOLS)) + "|.", re.S)
ABBREVIATIONS = {"bc": "B C", "cbd": "C B D", "dc": "D C", "gpo": "G P O",
                 "po": "P O", "rgh": "R G H", "rd": "Road", "tce": "Terrace"}


def respell(ipa):
    phones = TOKENS.findall(ipa.replace("͡", "").replace("ːː", "ː"))
    nuclei = [idx for idx, phone in enumerate(phones) if phone in VOWELS]
    if not nuclei:
        return ""
    stress = phones.index("ˈ") if "ˈ" in phones else 0
    stressed = next((i for i, idx in enumerate(nuclei) if idx >= stress), 0)
    boundaries = [0]
    for left, right in zip(nuclei, nuclei[1:]):
        consonants = [idx for idx in range(left + 1, right) if phones[idx] not in "ˈˌ"]
        onset = consonants[-1] if consonants else right
        if len(consonants) > 1:
            pair = "".join(phones[i] for i in consonants[-2:])
            if pair in {"bl", "bɹ", "dɹ", "fl", "fɹ", "ɡl", "ɡɹ", "kl", "kɹ", "pl",
                        "pɹ", "sk", "sl", "sm", "sn", "sp", "st", "sw", "tɹ", "tw"}:
                onset = consonants[-2]
        boundaries.append(onset)
    boundaries.append(len(phones))
    syllables = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        sound = "".join(VOWELS.get(phone, CONSONANTS.get(phone, phone if phone.isascii() else ""))
                        for phone in phones[start:end])
        syllables.append(sound.upper() if i == stressed else sound.lower())
    return "-".join(filter(None, syllables))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Write draft candidates outside the repository")
    args = parser.parse_args()
    output_path = args.output.resolve()
    if output_path.is_relative_to(ROOT):
        parser.error("Write candidates outside the repository and review them before importing.")
    engine = EspeakPhonemizer()
    guides = json.loads((ROOT / "data/pronunciations.json").read_text())
    output = {}
    for state, sourced in guides.items():
        rows = json.loads((ROOT / f"data/{state.lower()}.json").read_text())
        drafts = output[state] = {}
        protected = {name for name, entry in sourced.items() if entry.get("verificationSource")}
        for name in sorted({row["suburb"] for row in rows} - protected):
            words = re.findall(r"[\w]+(?:['’][\w]+)*", name)
            expanded = ["Saint" if i == 0 and word == "St" else "Street" if word == "St"
                        else ABBREVIATIONS.get(word.lower(), word) for i, word in enumerate(words)]
            sounds = []
            for word in " ".join(expanded).split():
                clauses = engine.phonemize("en-gb-x-rp", word)
                sounds.append(respell("".join(clauses[0])) or word)
            drafts[name] = " ".join(sounds)
    with output_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
