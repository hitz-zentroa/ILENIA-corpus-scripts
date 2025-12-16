import argparse
import logging
from collections import defaultdict
import os
import json

from tqdm import tqdm

from util import convert_pdf_to_text, collect_pdfs


def main(input_folder: str, output_file: str, corpus_name: str, domain: str):

    pdf_files = collect_pdfs(input_folder)
    id_counter = defaultdict(int)

    logging.warning(f"Found {len(pdf_files)} PDF files in {input_folder}.")

    with open(output_file, "w", encoding="utf-8") as out:
        for filepath in tqdm(pdf_files, desc="Converting PDFs"):

            try:
                text = convert_pdf_to_text(filepath)
            except Exception as e:
                logging.exception(f"Error converting {filepath}: {e}")
                continue

            parts = filepath.split(os.sep)
            title = os.path.basename(filepath).replace(".pdf", "")
            year = parts[-2].split("_")[-2] if len(parts[-2].split("_")[-2]) == 4 else "unknown"
            parent_folder = parts[-2] if len(parts) >= 2 else ""

            base_id = f"{corpus_name}_{parent_folder}"

            id_counter[base_id] += 1
            count = id_counter[base_id]
            _id = f"{base_id}{count}"

            record = {
                "id": _id,
                "title": title,
                "issue": parent_folder,
                "year": year,
                "domain": domain,
                "text": text,
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Path to the folder containing PDF files")
    parser.add_argument("-o", "--output", type=str, required=False, help="Output JSONL file (default: <corpus>.jsonl)")
    parser.add_argument("--corpus", type=str, required=True, help="Corpus name (used for IDs and default output filename)")
    parser.add_argument("--domain", type=str, required=True, help="Domain label for the documents")

    args = parser.parse_args()

    main(args.input, args.output or f"{args.corpus}.jsonl", args.corpus, args.domain)
