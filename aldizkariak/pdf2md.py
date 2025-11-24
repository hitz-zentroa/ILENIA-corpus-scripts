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
    id_counter = defaultdict(int)

    print(f"Found {len(pdf_files)} PDF files in {folder_path}.")

    with open(output_file, "w", encoding="utf-8") as out:
        for filepath in tqdm(pdf_files, desc="Converting PDFs"): # limitar a 5 para pruebas

            try:
                text = convert_pdf_to_text(filepath)
            except Exception as e:
                print(f"Error converting {filepath}: {e}")
                continue

            # extraer datos del path
            parts = filepath.split(os.sep)
            title = os.path.basename(filepath).replace(".pdf", "")
            year = parts[-2].split("_")[-2] if len(parts[-2].split("_")[-2]) == 4 else "unknown"
            parent_folder = parts[-2] if len(parts) >= 2 else ""
            #_id = f"{corpus}_{parent_folder}"

            # id base (sin número aún)
            base_id = f"{corpus}_{parent_folder}"

            # incrementar contador y usarlo como sufijo desde 1
            id_counter[base_id] += 1
            count = id_counter[base_id]
            _id = f"{base_id}{count}"

            # crear json
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
    folder_path = "aldizkariak/ekaia"
    corpus = "ekaia"
    domain = "zientzia eta teknologia"
    output_file = f"{corpus}.jsonl"

    main(folder_path, corpus, domain, output_file)
    print(f"JSONL creado en {output_file}")
