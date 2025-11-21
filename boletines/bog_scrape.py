import requests
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, timedelta
import os
import re
import argparse
import json


def daterange(start_date, end_date):
    """Genera fechas entre start_date y end_date (inclusive)."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


"""
def extraer_enlaces(html):
    
    Dado el HTML de una página, extrae todos los nombres de archivo que coinciden
    con el patrón: c########.htm (por ejemplo, c1411581.htm o c0714114.htm), junto con su título correspondiente.
    
    Devuelve una lista de tuplas (nombre_archivo, titulo).
    
    soup = BeautifulSoup(html, 'html.parser')
    enlaces_con_titulo = []

    # Buscar todos los elementos <li> que puedan contener los enlaces y los títulos
    for li in soup.find_all('li'):
        # Extraer el título (si está presente)
        titulo_elemento = li.find(class_="titulo_anuncio")
        if titulo_elemento:
            titulo_texto = titulo_elemento.get_text(strip=True)
        else:
            # Si no hay <div class="titulo_anuncio">, buscar texto cerca del enlace
            titulo_texto = ""
            for element in li.contents:
                if element.name == "a":  # Si encontramos un enlace, dejamos de buscar
                    break
                if isinstance(element, str):  # Si es texto, lo agregamos al título
                    titulo_texto += element.strip() + " "

        # Buscar enlaces específicos dentro del <li>
        for a in li.find_all('a', href=True):
            href = a['href']
            nombre_archivo = os.path.basename(href)

            # Verificar si el enlace coincide con el patrón "c#######.htm"
            if re.match(r'^c\d+\.htm$', nombre_archivo, re.IGNORECASE):
                # Guardar el enlace con su título correspondiente
                enlaces_con_titulo.append((nombre_archivo, titulo_texto.strip()))
            elif re.match(r'^e\d+\.htm$', nombre_archivo, re.IGNORECASE):
                enlaces_con_titulo.append((nombre_archivo, titulo_texto))

    return enlaces_con_titulo
"""
"""
def extraer_enlaces(html):
    
    Dado el HTML de una página, extrae todos los enlaces HTML (aquellos cuyo href termina en .htm)
    junto con el título correspondiente de cada anuncio.
    
    Se consideran dos estructuras:
      1. El anuncio está contenido en un <li> dentro de un <ul class="anuncios"> y el título
         se halla en un <div class="titulo_anuncio">.
      2. El anuncio está en un <li> donde el título es el texto que aparece fuera de los enlaces.
    
    Devuelve una lista de tuplas: (nombre_archivo, título).
    
    from bs4 import NavigableString
    import os, re
    soup = BeautifulSoup(html, 'html.parser')
    resultados = []

    # Primero, buscar los <ul> con clase "anuncios"
    ul_anuncios = soup.find_all('ul', class_="anuncios")
    if ul_anuncios:
        # Procesar cada anuncio (<li> directo dentro del <ul class="anuncios">)
        for ul in ul_anuncios:
            for li in ul.find_all('li', recursive=False):
                # 1. Extraer título
                titulo_div = li.find('div', class_="titulo_anuncio")
                if titulo_div:
                    titulo = titulo_div.get_text(strip=True)
                else:
                    # Si no hay div específico, extraemos el texto fuera de los enlaces.
                    title_parts = []
                    for elem in li.descendants:
                        if isinstance(elem, NavigableString) and elem.parent.name != "a":
                            texto = elem.strip()
                            if texto:
                                title_parts.append(texto)
                    titulo = " ".join(title_parts)
                
                # 2. Buscar el enlace HTML: buscamos la primera <a> cuyo href termine en ".htm"
                enlace_html = None
                for a in li.find_all('a', href=True):
                    href = a['href']
                    if re.search(r'\.htm$', href, re.IGNORECASE):
                        # Nos quedamos solo con el nombre del archivo
                        enlace_html = os.path.basename(href)
                        break

                if enlace_html and titulo:
                    resultados.append((enlace_html, titulo))
    else:
        # Fallback: si no se encuentran <ul class="anuncios">, procesar todos los <li> del documento
        for li in soup.find_all('li'):
            enlace_html = None
            for a in li.find_all('a', href=True):
                href = a['href']
                if re.search(r'\.htm$', href, re.IGNORECASE):
                    enlace_html = os.path.basename(href)
                    break
            if enlace_html:
                titulo_div = li.find('div', class_="titulo_anuncio")
                if titulo_div:
                    titulo = titulo_div.get_text(strip=True)
                else:
                    title_parts = []
                    for elem in li.descendants:
                        if isinstance(elem, NavigableString) and elem.parent.name != "a":
                            texto = elem.strip()
                            if texto:
                                title_parts.append(texto)
                    titulo = " ".join(title_parts)
                resultados.append((enlace_html, titulo))
    return resultados
    """
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
        except ValueError:
            raise ValueError("El formato de fecha debe ser DD/MM/YYYY o YYYY-MM-DD")
    fecha_formateada = fecha_obj.strftime("%Y-%m-%d")
    anio = fecha_obj.strftime("%Y")
    
    # Obtención del HTML
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Error al obtener la url: {e}")
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
        #print(f"Registro añadido en {ruta_archivo}")
    except Exception as e:
        print(f"Error al escribir en el archivo: {e}")


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
    
    print(f"\nProcesando {fecha.strftime('%Y-%m-%d')} -> {url}")
    try:
        response = requests.get(url)
    except Exception as e:
        print(f"Error al solicitar la URL: {e}")
        return None

    # Si la respuesta es 404, la página no existe
    if response.status_code == 404:
        print("Página no encontrada (404).")
        return None

    # Comprobar si la página contiene el mensaje de boletín no disponible
    if "Por motivos técnicos" in response.text:
        print("Boletín no disponible (mensaje técnico).")
        return None

    # Extraer enlaces del HTML
    enlaces = extraer_enlaces(response.text)
    # print(len(enlaces), "enlaces encontrados.")
    # for enlace, titulo in enlaces[0:10]:
    #     print(f"  - {enlace}: {titulo}")
    # input()


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
    datos = main(añoinicio, añofin, idioma, args.directory, bolname)


