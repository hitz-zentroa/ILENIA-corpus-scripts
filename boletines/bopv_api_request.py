import argparse
import os
import time
from contextlib import suppress
from datetime import datetime
from typing import Iterable

import jsonlines
import pytz
import requests
from bs4 import BeautifulSoup, Tag


def cambiar_a_zona_horaria_española(fecha_iso):
    """Convierte una fecha en formato ISO 8601 a la zona horaria de España (Madrid) y devuelve solo la fecha en formato 'YYYY-MM-DD'."""

    fecha_obj = datetime.strptime(fecha_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
    zona_madrid = pytz.timezone("Europe/Madrid")
    fecha_madrid = fecha_obj.astimezone(zona_madrid)
    publicationDate = fecha_madrid.strftime("%Y-%m-%d")
    return publicationDate


def collect_text(soup_iter: Iterable[Tag], extract: bool = False, sep: str = '\n') -> str:
    text = ''
    for root_tag in soup_iter:
        if not root_tag:
            continue
        with suppress(AttributeError):
            for ele in root_tag.descendants:
                if not ele:
                    continue
                if isinstance(ele, str):
                    text += ele
                elif ele.name in ('br', 'p'):
                    text += sep
                if extract:
                    ele.extract()
        text += sep
    return text


def limpiar_texto(texto):
    soup = BeautifulSoup(texto, 'html.parser')
    text = soup.get_text(separator="\n", strip=True)
    return text


def obtener_bopv(base_url, year, idioma, page=1):
    """Obtener actos administrativos del BOPV para un año concreto"""

    lang = "BASQUE" if idioma == "eu" else "SPANISH"
    url = f"{base_url}/bopv/administrative-acts/{year}?lang={lang}&currentPage={page}"
    print(url)
    headers = {"Accept": "application/json"}

    max_retries = 5  # Número máximo de intentos
    timeout = 10  # Tiempo máximo de espera por intento
    wait_time = 5  # Tiempo de espera entre intentos

    for intento in range(max_retries):

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()  # Lanza una excepción si el código de estado es un error (4xx, 5xx)
            return response.json()  # respuesta en formato JSON
        except requests.exceptions.RequestException as e:
            print(f"Error en el intento {intento + 1}: {e}")
            if intento < max_retries - 1:
                print(f"Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)  # Espera antes de reintentar
            else:
                print("Se agotaron los intentos, no se pudo obtener respuesta.")
                return None


def main(añoinicio, añofin, idioma, directory):
    """Guardar actos administrativos del BOPV en ficheros JSONL por cada año"""

    # guardar datos en un fichero JSONL por cada año
    # cada linea del fichero es un acto administrativo
    for year in range(añoinicio, añofin + 1):
        print(f"Obteniendo datos del año {year}...")
        with jsonlines.open(os.path.join(directory, f'bopv_{idioma}_{year}.jsonl'), mode='a') as writer:
            # obtener los datos de la primera pagina
            result = obtener_bopv(base_url, year, idioma)
            # ver numero de paginas totales 
            total_pages = result["totalPages"]
            print(f"Total de páginas: {total_pages}")
            for page in range(1, total_pages + 1):
                result = obtener_bopv(base_url, year, idioma, page)
                if result:
                    items = result["items"]
                    for item in items:
                        titulo = item.get("name", "")
                        normative_range = item.get("normativeRange", "")
                        estado = item.get("state", "")
                        scope = item.get("territorialScope", "")
                        numBulletin = item.get("numBulletin", "")
                        numOrder = item.get("numOrder", "")
                        numDisposal = item.get("numDisposal", "")
                        publicationDateISO = item.get("publishDate", "2000-01-01T23:00:00Z")
                        publicationDate = cambiar_a_zona_horaria_española(publicationDateISO)
                        disposalDateISO = item.get("disposalDate", "2000-01-01T23:00:00Z")
                        disposalDate = cambiar_a_zona_horaria_española(disposalDateISO)
                        issuingBody = item.get("issuingBody", "")
                        department = item.get("department", "")
                        section = item.get("section", "")
                        formatted_themes = "; ".join(
                            f"{theme['name']}: {', '.join(subject['name'] for subject in theme['subjects'])}"
                            for theme in item.get("themes", [])
                        )
                        text = item["text"]
                        titulo_texto = limpiar_texto(text.get("index", ""))
                        contenido_texto = limpiar_texto(text.get("content", ""))
                        url = item.get("mainEntityOfPage", "")
                        writer.write({
                            "titulo": titulo,
                            "normative_range": normative_range,
                            "estado": estado,
                            "ambito": scope,
                            "numBulletin": numBulletin,
                            "numOrder": numOrder,
                            "numDisposal": numDisposal,
                            "fechaPublicacion": publicationDate,
                            "fechaDisposicion": disposalDate,
                            "organismo": issuingBody,
                            "departamento": department,
                            "seccion": section,
                            "temas": formatted_themes,
                            "titulo_texto": titulo_texto,
                            "contenido_texto": contenido_texto,
                            "url": url
                        })


if __name__ == "__main__":
    base_url = "https://api.euskadi.eus"

    # argument parser
    parser = argparse.ArgumentParser(description="Obtener actos administrativos del BOPV")
    parser.add_argument("directory", type=str, help="Directorio donde se guardarán los datos")
    parser.add_argument("añoinicio", type=int, help="Año de inicio")
    parser.add_argument("añofin", type=int, help="Año de fin")
    # idioma = eu o es , solo esas dos opciones
    parser.add_argument("idioma", choices=["eu", "es"], help="Idioma de los datos")
    args = parser.parse_args()

    añoinicio = args.añoinicio
    añofin = args.añofin
    main(añoinicio, añofin, args.idioma, args.directory)
