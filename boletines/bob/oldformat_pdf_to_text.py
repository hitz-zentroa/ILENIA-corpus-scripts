import pdfplumber
import json
import re
from difflib import SequenceMatcher
import argparse
import os 
import tqdm

def clean_text(text):
    """Limpia saltos de línea y espacios extra para normalizar la comparación."""
    if not text: return ""
    # Unir guiones de salto de línea (ej: "admi-\nnistracion" -> "administracion")
    text = re.sub(r'-\s*\n', '', text) 
    # Normalizar espacios (elimina saltos de línea y espacios dobles)
    return " ".join(text.split())

def get_best_match_index(pdf_block_text, articles_list, start_idx=0):
    """
    Busca el mejor match PERO solo busca a partir de start_idx.
    Esto soluciona el problema de artículos repetidos/consecutivos.
    """
    best_score = 0
    best_idx = -1
    
    pdf_clean = clean_text(pdf_block_text).lower()
    
    for i, art in enumerate(articles_list):
        if i < start_idx:
            continue
        full_json = f"{art.get('organismo_emisor', '')} {art.get('titulo', '')}"
        json_clean_full = clean_text(full_json).lower()
        
        json_clean_title = clean_text(art.get('titulo', '')).lower()
        
        score_full = SequenceMatcher(None, pdf_clean, json_clean_full).ratio()
        score_title = SequenceMatcher(None, pdf_clean, json_clean_title).ratio()
        
        current_max = max(score_full, score_title)
        
        if json_clean_title in pdf_clean and len(json_clean_title) > 20:
             current_max = max(current_max, 0.95)

        if current_max > 0.85 and current_max > best_score:
            best_score = current_max
            best_idx = i
            
    return best_idx

def extract_content_final(pdf_path, jsonl_path, output_path, lang='es'):
    # 1. Configuración de Márgenes (Puntos PDF: A4 es aprox 595x842)
    MARGIN_TOP = 46
    MARGIN_BOTTOM = 36
    MARGIN_LEFT = 36
    MARGIN_RIGHT = 36

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        articles = [json.loads(line) for line in f]

    # obtener el nombre del pdf y filtrar con el campo 'nombre_original_pdf' los artículos
    pdf_name = pdf_path.split('_')[-1]
    if pdf_name == "eus.pdf": # ocurre con los de despues del 3 de abril de 2017, son los que no hay que procesar
        return
    articles = [art for art in articles if art['nombre_original_pdf'] == pdf_name]
    
    raw_blocks = [] 
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            width = page.width
            height = page.height
            midpoint = width / 2
            
            # --- RECORTE DE MÁRGENES (v3) ---
            crop_box = (MARGIN_LEFT, MARGIN_TOP, width - MARGIN_RIGHT, height - MARGIN_BOTTOM)
            cropped_page = page.crop(crop_box)
            
            words = cropped_page.extract_words(keep_blank_chars=True, extra_attrs=["fontname"])
            words.sort(key=lambda w: (w['top'], w['x0']))
            
            current_type = None
            current_words = []
            
            for w in words:
                x_mid = (w['x0'] + w['x1']) / 2
                
                # --- FILTRO DE COLUMNA (v3) ---
                in_col = False
                if lang == 'es':
                    if w['x0'] > (midpoint - 10): in_col = True
                else: # euskera
                    if w['x1'] < (midpoint + 10): in_col = True
                
                if not in_col:
                    continue

                # Detección Negrita
                font = w.get("fontname", "").lower()
                is_bold = "bold" in font or "b" in font.split("-")[-1] or "negrita" in font
                b_type = 'BOLD' if is_bold else 'REGULAR'
                
                if b_type != current_type:
                    if current_words:
                        raw_blocks.append({
                            'type': current_type, 
                            'text': " ".join([word['text'] for word in current_words]),
                            'page': page_num
                        })
                    current_type = b_type
                    current_words = [w]
                else:
                    current_words.append(w)
            
            if current_words:
                raw_blocks.append({
                    'type': current_type, 
                    'text': " ".join([word['text'] for word in current_words]),
                    'page': page_num
                })

    # =========================================================================
    # PASO 1: TROCEADO DE ANUNCIOS/EDICTOS
    # =========================================================================
    processed_blocks = []

    split_pattern = re.compile(
        r'(?:(?:^|\n|•|\))\s*)'
        r'(IRAGARKIA|ANUNCIO|EDICTO|EDIKTUA|EDIKTOA)\b',
        re.IGNORECASE
    )

    for block in raw_blocks:
        if block['type'] == 'BOLD':
            processed_blocks.append(block)
            continue

        parts = split_pattern.split(block['text'])

        if len(parts) == 1:
            processed_blocks.append(block)
            continue

        i = 0
        while i < len(parts):
            part = parts[i].strip()

            if not part:
                i += 1
                continue

            # Si es IRAGARKIA, lo juntamos con el texto que le sigue
            if split_pattern.fullmatch(part):
                if i + 1 < len(parts):
                    text = part + " " + parts[i + 1]
                    processed_blocks.append({
                        'type': 'REGULAR',
                        'text': text.strip(),
                        'page': block['page']
                    })
                    i += 2
                else:
                    processed_blocks.append({
                        'type': 'REGULAR',
                        'text': part,
                        'page': block['page']
                    })
                    i += 1
            else:
                processed_blocks.append({
                    'type': 'REGULAR',
                    'text': part,
                    'page': block['page']
                })
                i += 1

    raw_blocks = processed_blocks

    # =========================================================================
    # PASO 2: MATCHING (CON TU LÓGICA ORIGINAL + FIX ANUNCIOS)
    # =========================================================================
    block_to_article = {}
    last_matched_article_idx = -1
    start_anuncio_pattern = re.compile(
        r'^(IRAGARKIA|ANUNCIO|EDICTO|EDIKTOA|EDIKTUA)\b\s*(.*)',
        re.IGNORECASE | re.DOTALL
    )

    for i, block in enumerate(raw_blocks):
        text_clean = clean_text(block['text'])
        
        # CASO 1: NEGRITA - Usar tu función original
        if block['type'] == 'BOLD':
            best_idx = get_best_match_index(
                block['text'],
                articles,
                start_idx=last_matched_article_idx + 1
            )

            if best_idx != -1:
                block_to_article[i] = best_idx
                last_matched_article_idx = best_idx

        # CASO 2: ANUNCIO/EDICTO
        else:
            match_anuncio = start_anuncio_pattern.match(text_clean)
            if match_anuncio:
                content_start = match_anuncio.group(2)
                
                best_idx = -1
                best_score = 0
                
                for j, art in enumerate(articles):
                    if j <= last_matched_article_idx:
                        continue

                    title = clean_text(art.get('titulo', '')).lower()
                    pdf_start = clean_text(content_start).lower()

                    score = SequenceMatcher(None, pdf_start[:300], title[:300]).ratio()

                    if pdf_start and pdf_start in title:
                        score = max(score, 0.92)

                    if score > 0.75 and score > best_score:
                        best_score = score
                        best_idx = j

                
                if best_idx != -1:
                    block_to_article[i] = best_idx
                    last_matched_article_idx = best_idx


    # =========================================================================
    # PASO 3: ASIGNACIÓN (TU LÓGICA ORIGINAL)
    # =========================================================================

    section_pattern = re.compile(
        r'^(?:[IVXLCDM]+\.\s*(?:Atala|Sección|Sekzioa))',
        re.IGNORECASE
    )

    current_article_idx = -1
    pending_article_idx = -1

    
    for i, block in enumerate(raw_blocks):

        text_clean = clean_text(block['text'])

        # Si el bloque es un match explícito (negrita o anuncio)
        if i in block_to_article:
            current_article_idx = block_to_article[i]
            pending_article_idx = current_article_idx
            articles[current_article_idx]['contenido_texto'] = ""

            # Si es anuncio, guardar el contenido completo
            if block['type'] != 'BOLD':
                articles[current_article_idx]['contenido_texto'] = block['text'].strip()
                continue

            # Si es negrita (título), no lo añadimos
            continue

        # CORTE POR CAMBIO DE SECCIÓN
        if section_pattern.match(text_clean):
            current_article_idx = -1
            continue

        # CORTE FUERTE: inicio de anuncio (sin match explícito)
        if start_anuncio_pattern.match(text_clean):
            current_article_idx = -1
            if pending_article_idx + 1 < len(articles):
                pending_article_idx += 1
                current_article_idx = pending_article_idx
                articles[current_article_idx]['contenido_texto'] = ""
                articles[current_article_idx]['contenido_texto'] = block['text'].strip()
            continue

        # Acumular contenido
        if current_article_idx != -1:
            new_text = block['text']
            new_text = new_text.replace("- ", "")

            if block['type'] == 'BOLD':
                new_text = f"\n**{new_text}**\n"

            prev = articles[current_article_idx].get('contenido_texto', "")
            articles[current_article_idx]['contenido_texto'] = (prev + "\n" + new_text).strip()


    # GUARDAR RESULTADO
    count = 0
    with open(output_path, 'a', encoding='utf-8') as f:
        for art in articles:
            if art.get('contenido_texto'): count += 1
            f.write(json.dumps(art, ensure_ascii=False) + "\n")
            
    print(f"Recuperados {count}/{len(articles)} artículos.")

# EJEMPLO DE USO:
# extract_content_final('20170102a001.pdf', 'articulos.jsonl', 'resultado_final.jsonl', lang='es')

# extract_content_final('/gaueko1/users/asagasti036/BOB_scrapping/files/2017/20170102_completo_20170102a001.pdf', '/gaueko1/users/asagasti036/BOB_scrapping/files/datos_2017_eu.jsonl', 'final.jsonl', "eu")

def main(input_dir, jsonfile, output_jsonl, lang='eu'):
    # iterar sobre cada pdf del input_dir y extraer texto
    for pdf_file in tqdm.tqdm(os.listdir(input_dir)):

        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, pdf_file)
            
            output_path = os.path.join(output_jsonl)
            
            extract_content_final(pdf_path, jsonfile, output_path, lang=lang)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Obtener contenido en texto de PDFs del BOB")
    parser.add_argument('input_dir', type=str, help='Directorio con PDFs de entrada')
    parser.add_argument('jsonfile', type=str, help='Fichero JSON de entrada con metadatos')
    parser.add_argument('output_jsonl', type=str, help='Fichero JSONL de salida con textos extraídos')
    parser.add_argument('--lang', type=str, default='eu', help='Idioma: "es" para español, "eu" para euskera')

    args = parser.parse_args()

    main(input_dir=args.input_dir, jsonfile=args.jsonfile, output_jsonl=args.output_jsonl, lang=args.lang)
