import argparse
import logging
import os
import json

from tqdm import tqdm

from util import convert_pdf_to_text, collect_pdfs

edition2year = {
    'i': 2015,
    'ii': 2017,
    'iii': 2019,
    'iv': 2021,
    'v': 2023,
    'vi': 2025
}


def main(input_folder: str, output_file: str, corpus: str, domain: str):

    pdf_files = collect_pdfs(input_folder)

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
            parent_folder = parts[-2] if len(parts) >= 2 else ""
            parts = parent_folder.split("-")
            edition = parts[0]
            pdf_id = title.split("-")[0]
            title = "".join(title.split("-")[1:])

            _id = f"{corpus}_{edition}_{domain}_{pdf_id}"

            domain = " ".join(parts[8:]) if len(parts) > 8 else domain

            record = {
                "id": _id,
                "title": title,
                "edition": edition,
                "year": edition2year.get(edition.lower(), ""),
                "domain": domain,
                "text": text,
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Path to the folder containing PDF files")
    parser.add_argument("-o", "--output", type=str, required=False, help="Output JSONL file (default: <corpus>.jsonl)")
    parser.add_argument("--corpus", type=str, default="ikergazte", help="Corpus name (used for IDs and default output filename)")
    parser.add_argument("--domain", type=str, required=True, help="Domain label for the documents")

    args = parser.parse_args()

    main(args.input, args.output or f"{args.corpus}.jsonl", args.corpus, args.domain)
