import argparse
import json
import logging
import os
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup, NavigableString


def daterange(start_date, end_date):
    """Genera fechas entre start_date y end_date (inclusive)."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def extraer_enlaces(html):
    """
    Dado el HTML de una página, extrae los anuncios con su enlace HTML (archivo .htm) y título.
    
    Se contemplan dos estructuras:
    
    1. Estructura "anuncios":
       <ul class="anuncios">
         <li>
           <div class="titulo_anuncio"> ... título ... </div>
           ... otros elementos ...
           <div class="enlace_html">
             <a ... href="...cXXXXXXX.htm" ...>HTML</a>
           </div>
         </li>
         ...
       </ul>
       
    2. Estructura "areas":
       <ul class="areas">
         <li class="area">
           <!-- Título del área (no se usa para el anuncio) -->
           <a name="..."><p> ... </p></a>
           <ul class="areas_temas">
             <li>
               Texto propio del anuncio (título) seguido de enlaces:
               ... texto del anuncio ...
               <a href="...#cXXXXXXX"><span ...>PDF</span></a>
               &nbsp;
               <a href="eXXXXXXX.htm"><span ...>HTM</span></a>
             </li>
             ...
           </ul>
         </li>
         ...
       </ul>
    
    Para cada anuncio se devuelve una tupla (nombre_archivo, título).
    """

    soup = BeautifulSoup(html, 'html.parser')
    resultados = []

    # Estructura 1: Procesar <ul class="anuncios">
    ul_anuncios = soup.find_all('ul', class_="anuncios")
    for ul in ul_anuncios:
        # Se procesan los <li> directos de cada <ul class="anuncios">
        for li in ul.find_all('li', recursive=False):
            # Intentamos obtener el título del anuncio
            titulo_div = li.find('div', class_="titulo_anuncio")
            if titulo_div:
                titulo = titulo_div.get_text(strip=True)
            else:
                # Si no hay div específico, tomamos el texto inmediato que no pertenezca a un <a>
                textos = [t.strip() for t in li.find_all(string=True, recursive=False) if t.strip()]
                titulo = " ".join(textos)

            # Buscar el enlace que termina en ".htm"
            enlace = None
            for a in li.find_all('a', href=True):
                if re.search(r'\.htm$', a['href'], re.IGNORECASE):
                    enlace = os.path.basename(a['href'])
                    break
            if enlace and titulo:
                resultados.append((enlace, titulo))

    # Estructura 2: Procesar <ul class="areas"> y sus <ul class="areas_temas">
    ul_areas = soup.find_all('ul', class_="areas")
    for ul in ul_areas:
        # Cada <li class="area"> agrupa anuncios
        for li_area in ul.find_all('li', class_="area", recursive=False):
            # Dentro de cada área, se buscan los anuncios en <ul class="areas_temas">
            temas_ul = li_area.find('ul', class_="areas_temas")
            if temas_ul:
                for li in temas_ul.find_all('li', recursive=False):
                    # Extraer el título del anuncio: tomar el contenido de texto inmediato fuera de los <a>
                    titulo_partes = []
                    for child in li.contents:
                        # Si es un tag <a>, lo saltamos
                        if getattr(child, "name", None) == "a":
                            continue
                        if isinstance(child, NavigableString):
                            texto = child.strip()
                            if texto:
                                titulo_partes.append(texto)
                        else:
                            # Si es otro tag, extraemos su texto
                            texto = child.get_text(strip=True)
                            if texto:
                                titulo_partes.append(texto)
                    titulo = " ".join(titulo_partes).strip()

                    # Buscar el enlace cuyo href termine en ".htm"
                    enlace = None
                    for a in li.find_all('a', href=True):
                        if re.search(r'\.htm$', a['href'], re.IGNORECASE):
                            enlace = os.path.basename(a['href'])
                            break
                    if enlace and titulo:
                        resultados.append((enlace, titulo))
    return resultados


def scrape_y_guardar(url, directorio, fecha, idioma, titulo):
    """
    Recibe:
      - url: la url de la página a scrapear.
      - directorio: ruta donde se guardará el archivo jsonl.
      - fecha: fecha proporcionada (se convertirá al formato AAAA-MM-DD).
      - idioma: cadena que se usará en el nombre del archivo.
      - titulo: título que se incluirá en el registro.

    La función obtiene el HTML de la URL, extrae:
      - organismo: se busca en distintos patrones (por ejemplo, en <span class="norma_000"> o <p class="00norma">)
      - departamento: se busca en <p class="norma01"> o, en algunos casos, en un bloque <b> que contiene varios <p>.
      - contenido_texto: se concatenan los textos encontrados en:
          1. varios <span class="textocomun">,
          2. varios <p> con clases que emparejen el patrón r'\d+norma',
          3. o <p align="JUSTIFY">.
    Finalmente, escribe o añade una línea en un archivo llamado "bog_{idioma}_{año}.jsonl".
    """

    # Aseguramos que la fecha esté en formato AAAA-MM-DD.
    try:
        # Se asume que la fecha de entrada puede venir en otro formato, por ejemplo, "DD/MM/YYYY".
        fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
    except ValueError:
        # Si ya está en el formato correcto o no se puede parsear, se usa tal cual
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("El formato de fecha debe ser DD/MM/YYYY o YYYY-MM-DD") from e
    fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
    anio = fecha_obj.strftime("%Y")

    # Obtención del HTML
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        logging.exception(f"Error al obtener la url: {e}")
        return

    soup = BeautifulSoup(html, 'html.parser')

    # Inicializamos los campos
    organismo = ""
    departamento = ""
    contenido_texto = ""

    # 1. Intentamos extraer organismo y departamento cuando están juntos en un bloque <b>
    bloque_b = soup.find('b')
    if bloque_b:
        # Buscamos todos los <p> con alineación CENTER dentro del bloque <b>
        parrafos_center = bloque_b.find_all('p', attrs={'align': 'CENTER'})
        if parrafos_center:
            # El primer párrafo se asume que es el organismo
            organismo = parrafos_center[0].get_text(strip=True)
            # Si existe un segundo párrafo, se asume que es el departamento
            if len(parrafos_center) > 1:
                departamento = parrafos_center[1].get_text(" ", strip=True)

    # 2. Si no se encontraron en bloque <b>, se buscan patrones individuales
    if not organismo:
        # Buscamos organismo en <span class="norma_000">
        span_norma = soup.find('span', class_='norma_000')
        if span_norma:
            organismo = span_norma.get_text(" ", strip=True)
        else:
            # Buscamos en <p class="00norma">
            p_norma = soup.find('p', class_='00norma')
            if p_norma:
                organismo = p_norma.get_text(" ", strip=True)

    if not departamento:
        # Buscamos departamento en <p class="norma01">
        p_departamento = soup.find('p', class_='norma01')
        if p_departamento:
            departamento = p_departamento.get_text(" ", strip=True)

    # 3. Extraemos el contenido textual.
    contenidos = []

    # a) Contenido en <span class="textocomun">
    spans_textocomun = soup.find_all('span', class_='textocomun')
    for span in spans_textocomun:
        textos = span.stripped_strings
        contenidos.append(" ".join(textos))

    # b) Contenido en <p> con clases que coincidan con el patrón \d+norma
    parrafos_norma = soup.find_all('p', class_=re.compile(r'\d+norma'))
    for p in parrafos_norma:
        contenidos.append(p.get_text(" ", strip=True))

    # c) Contenido en <p align="JUSTIFY">
    parrafos_justify = soup.find_all('p', align="JUSTIFY")
    for p in parrafos_justify:
        contenidos.append(p.get_text(" ", strip=True))

    # Unimos todo el contenido extraído en un solo string.
    contenido_texto = "\n".join(contenidos)

    # Preparamos el diccionario con los campos requeridos.
    registro = {
        "titulo": titulo,
        "fechaPublicacion": fecha_formateada,
        "organismo": organismo,
        "departamento": departamento,
        "contenido_texto": contenido_texto,
        "url": url
    }

    # Preparamos el nombre del archivo, asegurándonos de que el directorio exista.
    nombre_archivo = f"bog_{idioma}_{anio}.jsonl"
    ruta_archivo = os.path.join(directorio, nombre_archivo)
    os.makedirs(directorio, exist_ok=True)

    # Abrimos el archivo en modo 'append' y escribimos el registro como JSON en una nueva línea.
    try:
        with open(ruta_archivo, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        # logging.warning(f"Registro añadido en {ruta_archivo}")
    except Exception as e:
        logging.exception(f"Error al escribir en el archivo: {e}")


def procesar_fecha(fecha, idioma, directorio, bolname):
    """
    Construye la URL a partir de la fecha, realiza la solicitud y, en caso de que la
    página exista y no tenga el mensaje de boletín no disponible, extrae los enlaces.
    """
    year = fecha.year
    month = fecha.month
    day = fecha.day

    # Construir el segmento bc{AAMMDD} -> usando el año en dos dígitos
    aammdd = f"{year % 100:02d}{month:02d}{day:02d}"
    url = f"https://egoitza.gipuzkoa.eus/gao-bog/{idioma}/{bolname}/{year}/{month:02d}/{day:02d}/b{idioma[0]}{aammdd}.htm"

    logging.warning(f"\nProcesando {fecha.strftime('%Y-%m-%d')} -> {url}")
    try:
        response = requests.get(url)
    except Exception as e:
        logging.exception(f"Error al solicitar la URL: {e}")
        return None

    # Si la respuesta es 404, la página no existe
    if response.status_code == 404:
        logging.error("Página no encontrada (404).")
        return None

    # Comprobar si la página contiene el mensaje de boletín no disponible
    if "Por motivos técnicos" in response.text:
        logging.warning("Boletín no disponible (mensaje técnico).")
        return None

    # Extraer enlaces del HTML
    enlaces = extraer_enlaces(response.text)

    # por cada elemennto de enlaces, llamar a la url y guardar en el fichero
    for enlace, titulo in enlaces:
        url = f"https://egoitza.gipuzkoa.eus/gao-bog/{idioma}/{bolname}/{year}/{month:02d}/{day:02d}/{enlace}"
        scrape_y_guardar(url, directorio, fecha.strftime("%Y-%m-%d"), idioma, titulo)


def main(añoinicio, añofin, idioma, directorio, bolname):
    """ Procesa las fechas entre añoinicio y añofin (inclusive) y guarda los datos en el directorio especificado."""

    start_date = datetime(añoinicio, 1, 1)
    end_date = datetime(añofin, 12, 31)

    for fecha in daterange(start_date, end_date):
        procesar_fecha(fecha, idioma, directorio, bolname)


if __name__ == '__main__':

    # argument parser
    parser = argparse.ArgumentParser(description="Obtener actos administrativos del BOPV")
    parser.add_argument("directory", type=str, help="Directorio donde se guardarán los datos")
    parser.add_argument("añoinicio", type=int, help="Año de inicio")
    parser.add_argument("añofin", type=int, help="Año de fin")
    # idioma = eu o es , solo esas dos opciones
    parser.add_argument("idioma", choices=["eu", "es"], help="Idioma de los datos")
    args = parser.parse_args()

    idioma = "castell"
    bolname = "bog"

    if args.idioma == "eu":
        idioma = "euskera"
        bolname = "gao"
    else:
        idioma = "castell"
        bolname = "bog"

    añoinicio = args.añoinicio
    añofin = args.añofin
    main(añoinicio, añofin, idioma, args.directory, bolname)
