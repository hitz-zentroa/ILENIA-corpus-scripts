import argparse
import os 
import json
import pdfplumber
from difflib import SequenceMatcher
import re
from tqdm import tqdm


# def separar_con_regex_flexible(full_text, trigger):
#     trigger_chars = [c for c in trigger if c.isalnum()]
#     chars_escapados = [re.escape(c) for c in trigger_chars]
#     union = r'[\W_]*'
#     patron = union.join(chars_escapados)
    
#     match = re.search(patron, full_text, re.IGNORECASE | re.DOTALL)
    
#     if match:
#         return full_text[match.end():], match.group(0)
#     return None


def extract_text_from_pdf(pdf_path: str, metadata: dict) -> str:
    """
    Extrae el texto de un PDF dado su path.
    Se retorna el texto como str, quitando el titulo y demas campos que ya estan en metadata.
    """

    titulo = metadata.get('titulo', '')
    organismo_emisor = metadata.get('organismo_emisor', '')
    seccion = metadata.get('seccion', '')

    extracted_text = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        for i, page in enumerate(pdf.pages):
            # print(f"--- Página {i+1} ---")
            margen = 30  
            margen_top = 100
            # bbox = (izquierda, arriba, derecha, abajo)
            bbox = (
                margen,                  # Cortar X puntos a la izquierda
                margen_top,                       # 0 para empezar desde el techo
                page.width - margen,     # Ancho total menos el margen derecho
                page.height              # Alto total para llegar hasta el suelo
            )
            text = page.within_bbox(bbox).extract_text()
            
            # if i == 0:
            #     # primera pagina, quitar encabezado
            #     try:
            #         texto_sin_encabezado, parte_quitada = separar_con_regex_flexible(text, titulo)
            #         if texto_sin_encabezado is None:
            #             print("No se ha podido separar el encabezado con el título. Intentando con organismo emisor...")
            #     except Exception as e:
            #         print("Error en separar_con_regex_flexible con titulo:", e)
            #         print("Texto:", text)
            #         print("Titulo:", titulo)

            # else:
            #     texto_sin_encabezado = text

            footer_eus = "BIZKAIKO ALDIZKARI OFIZIALA"
            footer_es = "BOLETÍN OFICIAL DE BIZKAIA"
            patron = r'\s*(' + re.escape(footer_eus) + r'|' + re.escape(footer_es) + r')\s*$'
            texto_limpio = re.sub(patron, '', text, flags=re.IGNORECASE)
            extracted_text.append(texto_limpio)

    return "\n".join(extracted_text)


def main(input_dir: str, jsonfile: str, output_jsonl: str):
    """
    Procesa todos los PDFs en input_dir, extrae su texto y guarda en output_jsonl
    """

    # leer fichero jsonl de metadatos
    metadata = []
    with open(jsonfile, 'r') as f_json:
        for line in f_json:
            metadata.append(json.loads(line))

    ultimo_organismo_visto = ""

    for item in metadata:
        # Obtenemos el organismo actual y limpiamos espacios en blanco por seguridad
        organismo_actual = item.get("organismo_emisor", "").strip()
        
        if organismo_actual:
            # Si tiene valor, actualizamos nuestra "memoria"
            ultimo_organismo_visto = organismo_actual
        else:
            # Si está vacío, le asignamos el último visto
            item["organismo_emisor"] = ultimo_organismo_visto

    metadata_dict = {item['nombre_original_pdf']: item for item in metadata}

    cutoff_date = "20170403"
            
    # iterar sobre cada pdf del input_dir y extraer texto
    for pdf_file in tqdm(os.listdir(input_dir)):

        file_date_str = pdf_file[:8]

        if file_date_str < cutoff_date:
            continue

        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, pdf_file)

            # el nombre del archivo tiene forma "YYYYMMDD_XX_nombreoriginal_con_guiones.pdf", extraer el nombreoriginal_con_guiones
            nombre_original = pdf_file.split('_', 2)[-1]
            # buscar en metadata el diccionario que tenga ese nombre_original en la clave "nombre_original_pdf"
            metadata = metadata_dict.get(nombre_original, {})
            if not metadata:
                print(f"No se han encontrado metadatos para el fichero {pdf_file}")
                exit(1)

            fecha = metadata.get('fecha', 'desconocida') # formato  "fecha": "2020-01-02"
            # comprobar si la fecha es posterior al 2017-04-03 (FECHA DE CAMBIO DE FORMATO)
            if fecha < "2017-04-03":
                print(f"Error: El PDF {pdf_file} tiene una fecha anterior a la permitida.")
                exit(1)

            # Extraer texto del PDF
            text = extract_text_from_pdf(pdf_path, metadata)
            # Guardar texto en el fichero JSONL
            with open(output_jsonl, 'a') as f_output:
                new_dict = {
                    **metadata,
                    'contenido_texto': text
                }
                f_output.write(json.dumps(new_dict, ensure_ascii=False))
                f_output.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Obtener contenido en texto de PDFs del BOB")
    parser.add_argument('input_dir', type=str, help='Directorio con PDFs de entrada')
    parser.add_argument('jsonfile', type=str, help='Fichero JSON de entrada con metadatos')
    parser.add_argument('output_jsonl', type=str, help='Fichero JSONL de salida con textos extraídos')

    args = parser.parse_args()

    main(input_dir=args.input_dir, jsonfile=args.jsonfile, output_jsonl=args.output_jsonl)
