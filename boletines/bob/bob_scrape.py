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




def procesar_fecha(fecha, idioma, bnum_cont, directorio, ano):
    """
    Descargar y procesar los datos del boletín para una fecha dada
    """

    bolname = "bob" if idioma == "es" else "bao"
    results = "resultados" if idioma == "es" else "emaitzak"
    print(f"Procesando fecha: {fecha.strftime('%Y-%m-%d')} con bnum_cont: {bnum_cont}")
    base_url = f"https://www.bizkaia.eus/{idioma}/{bolname}/{results}?p_p_id=IYBIWBCC&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_IYBIWBCC_mvcRenderCommandName=%2Fdetail&_IYBIWBCC_bdate={fecha.strftime('%Y%m%d')}&_IYBIWBCC_bnum={bnum_cont:03d}"
    # print("URL:", base_url)
    response = requests.get(base_url)
    # print(response.status_code)
    if response.status_code == 200 or response.status_code == 204:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Procesar el contenido de la página
        # si se encuentra el siguiente texto, significa que no existe y se returnea False
        # "No se han encontrado resultados"
        no_results_text = "No se han encontrado resultados"
        if no_results_text in soup.get_text():
            return False
        
        ##################################
        # Codigo para extraer y guardar los datos

        # 1. Preparar directorios y variables iniciales
        carpeta_pdfs = os.path.join(directorio if directorio else ".", f"{ano}_{idioma}")
        if not os.path.exists(carpeta_pdfs):
            os.makedirs(carpeta_pdfs)
            
        archivo_jsonl = os.path.join(directorio if directorio else ".", f"datos_{ano}_{idioma}.jsonl")
        
        # 2. Obtener el link del boletín completo (si existe) para comparar
        elem_bol_completo = soup.find(id="downloadParts0")
        url_bol_completo = elem_bol_completo['href'] if elem_bol_completo else None
        # Limpiar fragmentos del link completo para comparación (ej: #page=1)
        url_bol_completo_clean = url_bol_completo.split('#')[0] if url_bol_completo else None

        autonumerico = 1

        # 3. Iterar por cada sección (H3)
        secciones = soup.find_all('h3')

        for h3 in secciones:
            texto_seccion = h3.get_text(strip=True)
            
            # El contenido de la sección está en el siguiente elemento <ul>
            ul_contenido = h3.find_next_sibling('ul')
            
            # Si no hay lista inmediatamente después, pasamos al siguiente h3
            if not ul_contenido:
                continue

            # Iterar sobre los artículos (elementos li dentro del ul)
            articulos = ul_contenido.find_all('li', recursive=False)

            for articulo in articulos:
                # Buscar organismo emisor y título por sus IDs parciales
                # Usamos lambda para buscar IDs que empiecen por el texto clave
                elem_entidad = articulo.find(id=lambda x: x and x.startswith('emisorEntidad'))
                elem_resumen = articulo.find(id=lambda x: x and x.startswith('emisorResumen'))

                # Si no hay resumen/título, saltamos (puede ser un elemento de formato vacío)
                if not elem_resumen:
                    continue

                # Extraer textos
                organismo_emisor = elem_entidad.get_text(strip=True) if elem_entidad else ""
                titulo_articulo = elem_resumen.get_text(strip=True)

                # Buscar el link al PDF dentro del artículo
                link_elem = articulo.find('a', href=lambda x: x and '.pdf' in x.lower())
                
                if link_elem:
                    url_pdf = link_elem['href']
                    # Asegurar que el link es absoluto
                    if url_pdf.startswith('/'):
                        url_pdf = f"https://www.bizkaia.eus{url_pdf}"
                    
                    # Obtener nombre original del archivo (sin parámetros URL)
                    nombre_original = url_pdf.split('/')[-1].split('#')[0].split('?')[0]

                    # 4. Lógica de nombrado y descarga
                    url_pdf_clean = url_pdf.split('#')[0]
                    es_completo = (url_bol_completo_clean and url_pdf_clean == url_bol_completo_clean)

                    if es_completo:
                        # Caso especial: link al boletín completo
                        nombre_pdf_final = f"{fecha.strftime('%Y%m%d')}_completo_{nombre_original}"
                        descargar = True
                        ruta_final = os.path.join(carpeta_pdfs, nombre_pdf_final)
                        
                        # Si ya existe el completo descargado, no lo bajamos otra vez
                        if os.path.exists(ruta_final):
                            descargar = False
                    else:
                        # Caso normal: artículo individual
                        nombre_pdf_final = f"{fecha.strftime('%Y%m%d')}_{autonumerico}_{nombre_original}"
                        descargar = True
                        ruta_final = os.path.join(carpeta_pdfs, nombre_pdf_final)

                    # 5. Guardar en JSONL
                    datos_articulo = {
                        "fecha": fecha.strftime('%Y-%m-%d'),
                        "seccion": texto_seccion,
                        "organismo_emisor": organismo_emisor,
                        "titulo": titulo_articulo,
                        "link": url_pdf,
                        "autonumerico": autonumerico,
                        "nombre_original_pdf": nombre_original
                    }
                    
                    with open(archivo_jsonl, "a", encoding="utf-8") as f:
                        f.write(json.dumps(datos_articulo, ensure_ascii=False) + "\n")

                    # 6. Descargar PDF
                    if descargar:
                        try:
                            # Usamos stream=True para descarga eficiente
                            pdf_resp = requests.get(url_pdf, stream=True)
                            if pdf_resp.status_code == 200:
                                with open(ruta_final, 'wb') as f_pdf:
                                    for chunk in pdf_resp.iter_content(chunk_size=8192):
                                        f_pdf.write(chunk)
                        except Exception as e:
                            print(f"Error descargando {nombre_pdf_final}: {e}")

                    # Incrementar contador solo si hemos procesado un artículo con PDF válido
                    autonumerico += 1
       
        ##################################

        return True
    return False


def main(añoinicio, añofin, idioma, directorio):
    """ Procesa las fechas entre añoinicio y añofin (inclusive) y guarda los datos en el directorio especificado."""

    for año in range(añoinicio, añofin + 1):
        # inicializar contador de boletines cada año
        bnum_cont = 1
        start_date = datetime(año, 1, 1)
        end_date = datetime(año, 12, 31)

        for fecha in daterange(start_date, end_date):
            if procesar_fecha(fecha, idioma, bnum_cont, directorio, ano=str(año)):
                bnum_cont += 1
            # else el dia no existe y no se hace nada
    
    print("Proceso completado.")
    print("Last bnum_cont:", bnum_cont)



if __name__ == '__main__':

    # argument parser
    parser = argparse.ArgumentParser(description="Obtener actos administrativos del BOPV")
    parser.add_argument("directory", type=str, help="Directorio donde se guardarán los datos")
    parser.add_argument("añoinicio", type=int, help="Año de inicio")
    parser.add_argument("añofin", type=int, help="Año de fin")
    # idioma = eu o es , solo esas dos opciones
    parser.add_argument("idioma", choices=["eu", "es"], help="Idioma de los datos")
    args = parser.parse_args()

    idioma = args.idioma

    añoinicio = args.añoinicio
    añofin = args.añofin
    datos = main(añoinicio, añofin, idioma, args.directory)


