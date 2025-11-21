import requests
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, timedelta
import os
import re
import argparse
import json
from urllib.parse import urljoin, urlparse, parse_qs
import html 
import unicodedata  
import difflib


def daterange(start_date, end_date):
    """Genera fechas entre start_date y end_date (inclusive)."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)



def extraer_enlaces(html, base_url):
    """
    Recibe el contenido HTML de un boletín del BOTHA
    y devuelve una lista de tuplas (enlace, título).
    """
    soup = BeautifulSoup(html, "html.parser")

    resultados = []
    vistos = set()

    # Seleccionamos únicamente enlaces a los textos HTML (xml) del BOTHA
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "Busquedas/Resultado.aspx" in href and ".xml" in href:
            enlace_abs = urljoin(base_url, href)

            if enlace_abs in vistos:
                continue

            # El título está en el mismo bloque del anuncio
            datos = a.find_parent("div", class_="datos_anuncio")
            titulo = ""
            if datos:
                # Suele venir en un <span id="...lblAnu...">
                span_titulo = datos.find("span", id=re.compile(r"lblAnu", re.I))
                if span_titulo:
                    titulo = span_titulo.get_text(" ", strip=True)
                else:
                    titulo = datos.get_text(" ", strip=True)

                # Limpieza: quitar el rastro de "Otros formatos: ..."
                titulo = re.sub(r"(Otros formatos|Bestelako formatuak)\s*:\s*.*", "", titulo, flags=re.I).strip(" :")

            resultados.append((enlace_abs, titulo))
            vistos.add(enlace_abs)
    return resultados


def normalize_text(text: str) -> str:
    # Pasar a minúsculas
    text = text.lower()
    # Normalizar acentos (por si hay diferencias de codificación)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    # Quitar guiones de final de línea (ej. "izenda-\ntzeko" -> "izendatzeko")
    text = re.sub(r'-\s+', '', text)
    # Asegurar espacio después de puntos, comas, puntos y comas, dos puntos
    text = re.sub(r'([.,;:])([^\s])', r'\1 \2', text)
    # Eliminar espacios innecesarios dentro de siglas (ej. "S. A." -> "S.A.")
    text = re.sub(r'\b([A-Z])\s+\.', r'\1.', text, flags=re.IGNORECASE)
    # Quitar saltos de línea y múltiples espacios
    text = re.sub(r'\s+', ' ', text)
    # cambiar comillas tipográficas por comillas simples
    text = text.replace("'", '"')
    # eliminar comillas
    text = text.replace('"', '')    
    # eliminar >> y <<
    text = text.replace(">>", "").replace("<<", "").replace("«", "").replace("»", "").replace("“", "").replace("”", "")
    # Convertir guiones entre letras en espacio (ej. "egoitza-zentro" -> "egoitza zentro")
    text = re.sub(r'(\w)-(\w)', r'\1 \2', text)

    # Quitar espacios al principio y final
    return text.strip()


def scrape_y_guardar(url, url_eu, directorio, fecha, titulo_es, titulo_eu, id):
    """
    Recibe:
      - url: la url de la página a scrapear. en el html esta tanto la version en euskera como en castellano.
      - directorio: ruta donde se guardará el archivo jsonl.
      - fecha: fecha proporcionada (se convertirá al formato AAAA-MM-DD).
      - idioma: cadena que se usará en el nombre del archivo.
      - titulo: título que se incluirá en el registro.

    La función obtiene el HTML de la URL, extrae:
      - organismo
      - departamento
      - contenido_texto
    Finalmente, escribe o añade una línea en un archivo .jsonl".
    """

    id_new = id + 1

    # Aseguramos que la fecha esté en formato AAAA-MM-DD.
    try:
        # Se asume que la fecha de entrada puede venir en otro formato, por ejemplo, "DD/MM/YYYY".
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
    except ValueError:
        # Si ya está en el formato correcto o no se puede parsear, se usa tal cual
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise ValueError("El formato de fecha debe ser DD/MM/YYYY o YYYY-MM-DD")
    fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
    anio = fecha_obj.strftime("%Y")
    
    # Obtención del HTML
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error al obtener la url: {e}")
        return
    
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text.replace("<br>", " ").replace("<BR>", " "), "html.parser")

    detalle_cast = soup.find("div", id="detalle_cast")
    if not detalle_cast:
        raise ValueError("No se encontró el div detalle_cast")
    if not detalle_cast.find("p", class_="txtprincipal"):
        print("⚠️ Página sin contenido válido, se omite:", url)
        return id_new
    detalle_eus = soup.find("div", id="detalle_eus")
    if not detalle_eus:
        raise ValueError("No se encontró el div detalle_eus")
    
    titulos = [titulo_es, titulo_eu]
    idtitulocast = None

    for idx, detalle in enumerate([detalle_cast, detalle_eus]):
        # Buscar bloques clave
        txttitulo1 = detalle.find("p", class_="txttitulo1")
        txtsubtitulo1 = detalle.find("p", class_="txtsubtitulo1")
        txttitulo2 = detalle.find("p", class_="txttitulo2")

        organismo, departamento = "", ""

        # Caso 1: existen cabeceras
        if txttitulo1 and txtsubtitulo1 and txttitulo2:
            if "Diputación Foral de Álava" in txtsubtitulo1.get_text(strip=True) or "Arabako Foru Aldundia" in txtsubtitulo1.get_text(strip=True):
                organismo = "Diputación Foral de Álava" if "Diputación Foral de Álava" in txtsubtitulo1.get_text(strip=True) else "Arabako Foru Aldundia"
                departamento = txttitulo2.get_text(strip=True)
            else:
                organismo = txttitulo2.get_text(strip=True)
                departamento = ""
            # Todo el contenido es el texto principal
            contenido = "\n".join(
                html.escape(p.get_text(strip=True))
                for p in detalle.find_all("p", class_="txtprincipal")
            )
        else:
            # Caso 2: buscar por título en txtprincipal
            parrafos = detalle.find_all("p", class_="txtprincipal")
            idx_titulo = None
            t_es_norm = normalize_text(titulo_es)
            t_eu_norm = normalize_text(titulo_eu)
            for i, p in enumerate(parrafos):
                p_norm = normalize_text(p.get_text())
                if t_es_norm in p_norm or p_norm in t_es_norm or t_eu_norm in p_norm or p_norm in t_eu_norm: 
                    idx_titulo = i
                    break
                else:
                    # Usar difflib para encontrar similitudes
                    ratio1 = difflib.SequenceMatcher(None, t_es_norm, p_norm).ratio()
                    ratio2 = difflib.SequenceMatcher(None, t_eu_norm, p_norm).ratio()
                    if ratio1 > 0.85 or ratio2 > 0.85:
                        idx_titulo = i
                        break
            if idx_titulo is None and idx == 0:
                # intentar buscar en el texto en euskera
                parrafos_eu = detalle_eus.find_all("p", class_="txtprincipal")
                for i, p in enumerate(parrafos_eu):
                    p_norm = normalize_text(p.get_text())
                    if t_es_norm in p_norm or p_norm in t_es_norm or t_eu_norm in p_norm or p_norm in t_eu_norm: 
                        idx_titulo = i
                        break
                    else:
                        # Usar difflib para encontrar similitudes
                        ratio1 = difflib.SequenceMatcher(None, t_es_norm, p_norm).ratio()
                        ratio2 = difflib.SequenceMatcher(None, t_eu_norm, p_norm).ratio()
                        if ratio1 > 0.85 or ratio2 > 0.85:
                            idx_titulo = i
                            break

            idtitulocast = idx_titulo if idx == 0 else idtitulocast
            if idx_titulo is None and idx == 1:   
                idx_titulo = idtitulocast

            if idx_titulo is None:
                print(f"No se encontró el párrafo que contiene el título : {titulo_es.strip()}")
                print(f"No se encontró el párrafo que contiene el título : {titulo_eu.strip()}")
                #raise ValueError("No se encontró el párrafo que contiene el título")

            prev = parrafos[:idx_titulo]
            if len(prev) >= 3 and ("Diputación Foral de Álava" in prev[1].get_text() or "Arabako Foru Aldundia" in prev[1].get_text()):
                organismo = prev[1].get_text(strip=True)
                departamento = prev[2].get_text(strip=True)
            elif len(prev) >= 3:
                organismo = prev[0].get_text(strip=True)
                departamento = prev[1].get_text(strip=True)
            elif len(prev) >= 2:
                organismo = prev[1].get_text(strip=True)
                departamento = ""
            elif len(prev) == 1:
                organismo = prev[0].get_text(strip=True)
                departamento = ""
            else:
                organismo = ""
                departamento = ""
            idx_titulo = 0
            contenido = "\n".join(
                html.escape(p.get_text(strip=True))
                for p in parrafos[idx_titulo + 1 :]
            )

        data = {
            "titulo": titulos[idx],
            "fechaPublicacion": fecha_formateada,
            "organismo": organismo,
            "departamento": departamento,
            "contenido_texto": contenido,
            "url": url if idx == 0 else url_eu,
            "id": f"botha_es_{id_new:05d}" if idx == 0 else f"botha_eu_{id_new:05d}",
        }

        # Preparamos el nombre del archivo, asegurándonos de que el directorio exista.
        nombre_archivo = f"botha_es_{anio}.jsonl" if idx == 0 else f"botha_eu_{anio}.jsonl"
        ruta_archivo = os.path.join(directorio, nombre_archivo)
        os.makedirs(directorio, exist_ok=True)

        # Abrimos el archivo en modo 'append' y escribimos el registro como JSON en una nueva línea.
        try:
            with open(ruta_archivo, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            # print(f"Registro añadido en {ruta_archivo}")
        except Exception as e:
            print(f"Error al escribir en el archivo: {e}")
    
    return id_new


def procesar_urls(lista_urls):
    """
    Procesa una lista de tuplas (URL, título) y agrupa por contenido común,
    manteniendo solo la URL con '_C' y ambos títulos.
    
    Args:
        lista_urls: Lista de tuplas en formato [(url1, título1), (url2, título2), ...]
    
    Returns:
        Lista de diccionarios con URL _C y ambos títulos
    """
    resultado_dict = {}
    
    for url, titulo in lista_urls:
        try:
            # Extraer el parámetro File de la URL
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            file_param = query_params.get('File', [''])[0]
            
            # Obtener la clave común (sin _C o _E)
            if '_C.xml' in file_param or '_E.xml' in file_param:
                clave_comun = file_param.replace('_C.xml', '').replace('_E.xml', '')
                
                # Inicializar entrada si no existe
                if clave_comun not in resultado_dict:
                    resultado_dict[clave_comun] = {
                        'url_C': None, 
                        'titulo_C': None, 
                        'titulo_E': None,
                        'clave_comun': clave_comun
                    }
                
                # Asignar según el tipo de URL
                if '_C.xml' in file_param:
                    resultado_dict[clave_comun]['url_C'] = url
                    resultado_dict[clave_comun]['titulo_C'] = titulo
                elif '_E.xml' in file_param:
                    resultado_dict[clave_comun]['titulo_E'] = titulo
                    
        except Exception as e:
            print(f"Error procesando URL: {url} - {e}")
            continue
    
    # Filtrar solo los que tienen URL _C y devolver como lista
    return [v for k, v in resultado_dict.items() if v['url_C']]


def procesar_fecha(fecha, directorio, id):
    """
    Construye la URL a partir de la fecha, realiza la solicitud y, en caso de que la
    página exista y no tenga el mensaje de boletín no disponible, extrae los enlaces.
    """
    year = fecha.year
    month = fecha.month
    day = fecha.day

    url = f"https://www.araba.eus/botha/Inicio/SGBO5001.aspx?FechaBotha={day:02d}/{month:02d}/{year}"

    print(f"\nProcesando {fecha.strftime('%Y-%m-%d')} -> {url}")
    try:
        response = requests.get(url)
    except Exception as e:
        print(f"Error al solicitar la URL: {e}")
        return id

    # Si la respuesta es 404, la página no existe
    if response.status_code == 404:
        print("Página no encontrada (404).")
        return id

    # Comprobar si la página contiene el mensaje de boletín no disponible
    if "Laburpena  zenbakiko aldizkaria, astelehena, 0001.eko urtarrilak 1 egunekoa" in response.text or \
       "Sumario del Boletin nº  del lunes, 1 de enero de 0001" in response.text:
        print("Boletín no disponible (mensaje técnico).")
        return id

    # Extraer enlaces del HTML
    enlaces = extraer_enlaces(response.text, url)
    # print(len(enlaces), "enlaces encontrados.")
    # for enlace, titulo in enlaces[0:10]:
    #     print(f"  - {enlace}: {titulo}")
    # input()

    pares = zip(enlaces[::2], enlaces[1::2])
    lista_triplas = [(url_c, url_e, titulo_c, titulo_e) for (url_e, titulo_e), (url_c, titulo_c) in pares]

    # por cada elemennto de enlaces, llamar a la url y guardar en el fichero
    for enlace, enlace_eu, titulo_es, titulo_eu in lista_triplas:
        if "_C.xml" in enlace:
            id = scrape_y_guardar(enlace, enlace_eu, directorio, fecha.strftime("%Y-%m-%d"), titulo_es, titulo_eu, id)
        else:
            print(f"Enlace no reconocido (ni _C ni _E): {enlace}")
            input()
    return id   


def main(añoinicio, añofin, directorio):
    """ Procesa las fechas entre añoinicio y añofin (inclusive) y guarda los datos en el directorio especificado."""

    id = 0

    #start_date = datetime(añoinicio, 1, 1)
    start_date = datetime(añoinicio, 1, 1)
    end_date = datetime(añofin, 12, 31)

    for fecha in daterange(start_date, end_date):
        id = procesar_fecha(fecha, directorio, id)


if __name__ == '__main__':

    # argument parser
    parser = argparse.ArgumentParser(description="Obtener actos administrativos del BOTHA")
    parser.add_argument("directory", type=str, help="Directorio donde se guardarán los datos")
    parser.add_argument("añoinicio", type=int, help="Año de inicio")
    parser.add_argument("añofin", type=int, help="Año de fin")
    # idioma = eu o es , solo esas dos opciones
    # parser.add_argument("idioma", choices=["eu", "es"], help="Idioma de los datos")
    args = parser.parse_args()

    añoinicio = args.añoinicio
    añofin = args.añofin
    datos = main(añoinicio, añofin, args.directory)


