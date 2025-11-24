from collections import defaultdict
import os
import json
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from tqdm import tqdm


def convert_pdf_to_text(filepath: str) -> str:
    """Convierte un PDF en texto usando Marker."""
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )
    rendered = converter(filepath)
    text, _, _ = text_from_rendered(rendered)
    return text


def collect_pdfs(folder_path: str):
    """Recorre recursivamente la carpeta y devuelve todos los PDFs encontrados."""
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    return pdf_files


def main(folder_path: str, corpus: str, domain: str, output_file: str):
    pdf_files = collect_pdfs(folder_path)

    # contador de ids repetidos

    print(f"Found {len(pdf_files)} PDF files in {folder_path}.")

    edition2year = {
        'i': 2015,
        'ii': 2017,
        'iii': 2019,
        'iv': 2021,
        'v': 2023,
        'vi': 2025
    }

    with open(output_file, "w", encoding="utf-8") as out:
        for filepath in tqdm(pdf_files, desc="Converting PDFs"):

            try:
                text = convert_pdf_to_text(filepath)
            except Exception as e:
                print(f"Error converting {filepath}: {e}")
                continue

            # extraer datos del path
            parts = filepath.split(os.sep)
            title = os.path.basename(filepath).replace(".pdf", "")
            #year = parts[-2].split("_")[-2] if len(parts[-2].split("_")[-2]) == 4 else "unknown"
            parent_folder = parts[-2] if len(parts) >= 2 else ""
            ikergazte_parts = parent_folder.split("-")
            edition = ikergazte_parts[0]
            pdf_id = title.split("-")[0]
            title = "".join(title.split("-")[1:])
            domain = "-".join(ikergazte_parts[8:]) if len(ikergazte_parts) > 8 else domain

            _id = f"{corpus}_{edition}_{domain}_{pdf_id}"

            domain = " ".join(ikergazte_parts[8:]) if len(ikergazte_parts) > 8 else domain

            
            # crear json
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
    folder_path = "aldizkariak/ikergazte"
    corpus = "ikergazte"
    domain = "ikergazte"
    output_file = f"{corpus}.jsonl"

    main(folder_path, corpus, domain, output_file)
    print(f"JSONL creado en {output_file}")
