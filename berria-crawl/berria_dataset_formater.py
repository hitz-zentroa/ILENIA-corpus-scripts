import json
from pathlib import Path

def transform_record(rec: dict) -> dict:
    """
    Transform one record:
    - Put 'url' first
    - Build 'text' from titularra, azpititularra, egilea, fetxa, testua
    - Append the rest of the fields afterwards
    """
    # Build text
    parts = []

    # titularra (title)
    if rec.get("titularra"):
        parts.append(rec["titularra"])

    # azpititularra (subtitle)
    if rec.get("azpititularra"):
        parts.append(rec["azpititularra"])

    # egilea + fetxa (author + date) or just date
    if rec.get("egilea") and rec.get("fetxa"):
        parts.append(f"Egilea: {rec['egilea']} / Data: {rec['fetxa']}")
    elif rec.get("fetxa"):
        parts.append("Data: " + rec["fetxa"])

    # testua (main text)
    if rec.get("testua"):
        parts.append(rec["testua"])

    text = "\n\n".join(parts)

    # Build ordered record
    out = {"url": rec.get("url", ""), "text": text}

    # Add the rest of the fields, preserving original order but skipping url
    for k, v in rec.items():
        if k in ("url",):
            continue
        out[k] = v

    return out


def process_jsonl(in_path: Path, out_path: Path):
    with in_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            rec = json.loads(line)
            new_rec = transform_record(rec)
            fout.write(json.dumps(new_rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reformat Berria JSONL file")
    parser.add_argument("input", type=Path, help="Input JSONL file")
    parser.add_argument("output", type=Path, help="Output JSONL file")
    args = parser.parse_args()

    process_jsonl(args.input, args.output)