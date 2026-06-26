import random
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
import time
from tqdm import tqdm
import sys
disable_tqdm = not sys.stdout.isatty()

def extraer_categoria(url):
    """
    Extrae categoría y subcategoría desde la URL:
    https://orain.eus/es/cultura/cine/2022/11/18/... 
    → categoria=cultura, subcategoria=cine

    Si la categoría o subcategoría son numéricas, devuelve None.
    """
    path_parts = urlparse(url).path.strip("/").split("/")

    def procesar(valor):
        if not valor:
            return None
        valor = valor.strip()
        if valor.isdigit():
            return None
        return valor

    categoria = procesar(path_parts[1] if len(path_parts) > 1 else None)
    subcategoria = procesar(path_parts[2] if len(path_parts) > 2 else None)

    return categoria, subcategoria

def scrap_noticia(url, reintento=False, error_not_found=[]):
    """
    Devuelve un diccionario con la info de la noticia
    """
    HEADERS = {
        "User-Agent": "OrainNewsScraper/1.0"
    }
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        # Título
        h1 = soup.find("h1", class_="cmp-title__text")
        titulo = h1.get_text(strip=True) if h1 else None
        

        # Subtítulo (puede estar en un div con clase cmp-text)
        subtitulo_div = soup.find("div", class_="text")
        subtitulo = None
        if subtitulo_div:
            cmp_text = subtitulo_div.find("div", class_="cmp-text")
            if cmp_text:
                # Si quieres solo el texto dentro del <b>
                b_tag = cmp_text.find("b")
                if b_tag:
                    subtitulo = b_tag.get_text(strip=True)
                else:
                    # Si quieres todo el texto del div como fallback
                    subtitulo = cmp_text.get_text(strip=True)

        # Texto principal
        texto_div = soup.find("div", class_="text aem-GridColumn aem-GridColumn--default--12")
        if texto_div:
            parrafos = texto_div.find_all("p")
            if parrafos:
                # Tomar cada párrafo, unir con saltos de línea
                texto = "\n".join([p.get_text(" ", strip=True) for p in parrafos])
            else:
                # Si no hay <p>, tomar todo el contenido de texto_div
                texto = texto_div.get_text(" ", strip=True)
        else:
            texto = None

        # Autor y fechas
        autor = None
        fecha_publicacion = None
        fecha_actualizacion = None

        autor_div = soup.find("div", class_="cmp-cf-author-date_text")
        if autor_div:
            autor_p = autor_div.find("div", class_="cmp-cf-author-date_author")
            if autor_p:
                autor = autor_p.get_text(strip=True)
                autor = autor.replace("|", "")
                autor = autor.replace("EITB MEDIA", "")
                autor = autor.replace("EITB Media", "")
                autor = autor.replace("EITB", "")
                autor = autor.strip()
            
            date_div = autor_div.find("div", class_="cmp-cf-author-date_date")
            if date_div:
                times = date_div.find_all("time")
                if times:
                    fecha_publicacion = times[0]["datestime"] if len(times) > 0 else None
                    fecha_actualizacion = times[1]["datestime"] if len(times) > 1 else None

        # Categoría y subcategoría
        categoria, subcategoria = extraer_categoria(url)

        # Tags
        tags_div = soup.find("div", class_="all-tags")
        tags_list = []

        if tags_div:
            # Extraer el texto de cada <a> dentro de <span class="tag">
            tags_list = [a.get_text(strip=True) for a in tags_div.find_all("a")]

        return {
            "url": url,
            "titulo": titulo,
            "subtitulo": subtitulo,
            "texto": texto,
            "autor": autor,
            "fecha_publicacion": fecha_publicacion,
            "fecha_actualizacion": fecha_actualizacion,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "tags": tags_list
        }

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code

        if status == 404:
            print(f"404 - No encontrada: {url}")
            error_not_found.append(url)
            return None  # no tiene sentido reintentar

        elif status >= 500:
            print(f"{status} - Error servidor, reintentando: {url}")
            if not reintento:
                time.sleep(3)
                return scrap_noticia(url, reintento=True)  # reintento simple
            else:
                print(f"Reintento fallido para {url}")
                error_not_found.append(url)
                return None

        else:
            print(f"HTTP error {status} en {url}")
            return None
        
    except requests.RequestException as e:
        print(f"Error accediendo a {url}: {e}")
        return None
    
def scrap_file(input_path: str):

    error_not_found = []
    print(f"Procesando {input_path}...")

    with open(input_path, "r", encoding="utf-8") as f:
        urls = json.load(f)

    articulos = []

    for item in tqdm(urls, desc="Procesando noticias", disable=disable_tqdm):

        new_instance = {
            "id": item["id"],
            "fecha": item["fecha"]
        }

        # -------- Euskera --------
        url_eu = item.get("url_eu")
        if url_eu:
            info_eu = scrap_noticia(url_eu, error_not_found=error_not_found)
            new_instance["eu"] = info_eu
            time.sleep(random.uniform(1.5, 3))
        else:
            new_instance["eu"] = None

        # -------- Español --------
        url_es = item.get("url_es")
        if url_es:
            info_es = scrap_noticia(url_es, error_not_found=error_not_found)
            new_instance["es"] = info_es
            time.sleep(random.uniform(1.5, 3))
        else:
            new_instance["es"] = None

        articulos.append(new_instance)

    output_name = input_path.replace(".json", "_scrapeado.json")

    with open(output_name, "w", encoding="utf-8") as f:
        json.dump(articulos, f, ensure_ascii=False, indent=2)

    print(f"Guardado {output_name} con {len(articulos)} artículos.")

    # Guardar URLs no encontradas
    if error_not_found:
        with open("urls_no_encontradas.txt", "w", encoding="utf-8") as f:
            for url in error_not_found:
                f.write(url + "\n")
        print(f"Guardado urls_no_encontradas con {len(error_not_found)} URLs.")

    return output_name
