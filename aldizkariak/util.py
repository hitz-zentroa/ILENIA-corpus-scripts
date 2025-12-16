import os

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
import requests


def download_pdf(headers, pdf_link, pdf_path):
    with requests.get(pdf_link, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def collect_pdfs(folder_path: str):
    """Recorre recursivamente la carpeta y devuelve todos los PDFs encontrados."""
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    return pdf_files


def convert_pdf_to_text(filepath: str) -> str:
    """Convierte un PDF en texto usando Marker."""
    converter = PdfConverter(artifact_dict=create_model_dict())
    rendered = converter(filepath)
    text, _, _ = text_from_rendered(rendered)
    return text
