import argparse
import json
import logging
import time

import pdfplumber
import requests
from lxml import etree


def download_pdf(url, max_retries=3, delay=2):
    nombre_archivo = "doc_temp.pdf"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/pdf",
    }
    time.sleep(2)  # Espera inicial antes de la primera descarga
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            content_type = response.headers.get("Content-Type", "")

            if response.status_code == 200 and "application/pdf" in content_type:
                with open(nombre_archivo, "wb") as f:
                    f.write(response.content)
                return True
            else:
                logging.warning(f"Intento {attempt}: No es un PDF válido (Content-Type: {content_type}), {response.content}")
        except Exception as e:
            logging.exception(f"Intento {attempt}: Error al descargar el PDF -> {e}")

        time.sleep(delay)  # Espera antes de reintentar

    logging.error("No se pudo descargar un PDF válido tras varios intentos.")
    return False


def extract_columns(pdf_path, fecha, encabezado_alto=50, pie_alto=50):
    with pdfplumber.open(pdf_path) as pdf:
        text_col1, text_col2 = [], []
        primera_pagina = True
        for page in pdf.pages:
            # Divide la página en dos mitades y elimina el encabezado y pie
            width = page.width
            height = page.height

            if primera_pagina:
                primera_pagina = False
                text = page.extract_text()
                if "Bilkuraren hitzez hitzeko transkripzioaren behin-behineko argitalpena" in text or "sustituida en su momento por la publicación definitiva" in text:
                    logging.warning("No es el behin-betiko: ", fecha)
                    return None

            # Ajusta las coordenadas para excluir el encabezado y el pie de página
            left_bbox = (0, encabezado_alto, width / 2, height - pie_alto)
            right_bbox = (width / 2, encabezado_alto, width, height - pie_alto)

            # Extrae el texto de las columnas
            text1 = page.within_bbox(left_bbox).extract_text()
            text2 = page.within_bbox(right_bbox).extract_text()

            text_col1.append(text1.replace("-\n", "").replace("\n", " "))
            text_col2.append(text2.replace("-\n", "").replace("\n", " "))

        text_1 = " ".join(text_col1)
        text_2 = " ".join(text_col2)

        if text_1 == "" or text_2 == "":
            logging.warning("No se ha podido extraer texto de ninguna columna: ", fecha)
        return text_1, text_2


def main(fname_texts: str, num_legislature: str):
    parser = etree.XMLParser(remove_blank_text=True)  # discard whitespace nodes
    tree_texts = etree.parse(fname_texts, parser)

    logging.warning("ANALIZANDO FICHEROS...")

    json_outputs = []
    for i, art_elem in enumerate(tree_texts.xpath("//sesiones_pleno")):

        legislatura = art_elem.xpath("./sesiones_pleno_legislatura")[0].text
        id = art_elem.xpath("./sesiones_pleno_num_sesion")[0].text
        fecha = art_elem.xpath("./sesiones_pleno_fecha_inicio")[0].text
        pdf_path = art_elem.xpath("./sesiones_pleno_diario_link")[0].text

        url = pdf_path.replace("<![CDATA[", "").replace("]]>", "").strip()

        download_pdf(url)

        texts = extract_columns("doc_temp.pdf", fecha)
        if texts is None:
            continue

        text1 = texts[0]
        text2 = texts[1]

        json_output = {
            "legislatura": legislatura,
            "num_sesion": id,
            "fecha": fecha,
            "original": text1,
            "traduccion": text2,
            "url": url,
        }
        json_outputs.append(json_output)

    with open(f"json_output_{num_legislature}.json", "w") as f:
        json.dump(json_outputs, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse PDF and extract text columns")
    parser.add_argument("--input_xml", type=str, help="Path to input XML file")
    parser.add_argument("--num_legislature", type=str, help="Legislature number")
    args = parser.parse_args()
    main(args.input_xml, args.num_legislature)
