import time
import json
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import random
from bs4 import BeautifulSoup

class BONScraper:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,eu;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        })
        
        # Archivo para guardar el progreso y poder reanudar
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        
        self.lang_config = {
            "es": {"sumario": "https://bon.navarra.es/es/boletin/-/sumario/{year}/{number}"},
            "eu": {"sumario": "https://bon.navarra.es/eu/buletina/-/sumario/{year}/{number}"}
        }

    def _parse_date(self, date_str: str) -> str:
        """Convierte fechas en formato '2 de enero de 2008' o '2008ko urtarrilaren 2a' a 'YYYY-MM-DD'."""
        date_str = date_str.lower()
        
        meses_es = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
        }
        meses_eu = {
            "urtarrilaren": "01", "otsailaren": "02", "martxoaren": "03", "apirilaren": "04",
            "maiatzaren": "05", "ekainaren": "06", "uztailaren": "07", "abuztuaren": "08",
            "irailaren": "09", "urriaren": "10", "azaroaren": "11", "abenduaren": "12"
        }
        
        # Intentar extraer formato euskera: ej "2008ko urtarrilaren 2a"
        match_eu = re.search(r"(\d{4})ko\s+([a-z]+)\s+(\d+)", date_str)
        if match_eu:
            year, month_str, day = match_eu.groups()
            month = meses_eu.get(month_str, "01")
            return f"{year}-{month}-{int(day):02d}"
            
        # Intentar extraer formato castellano: ej "2 de enero de 2008"
        match_es = re.search(r"(\d+)\s+de\s+([a-z]+)\s+de\s+(\d{4})", date_str)
        if match_es:
            day, month_str, year = match_es.groups()
            month = meses_es.get(month_str, "01")
            return f"{year}-{month}-{int(day):02d}"
            
        # Si por algún motivo no coincide con los patrones, devuelve el string original para no perder el dato
        return date_str

    def load_checkpoint(self) -> Dict[str, int]:
        """Carga el progreso guardado. Si no existe, devuelve valores por defecto."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {"year": None, "number": 1, "article_counter": 1}

    def save_checkpoint(self, year: int, number: int, article_counter: int):
        """Guarda el estado actual para poder reanudar si el script se interrumpe."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                "year": year, 
                "number": number, 
                "article_counter": article_counter
            }, f)

    def get_html(self, url: str, max_retries: int = 4) -> Optional[BeautifulSoup]:
        """Descarga la página con camuflaje, pausas dinámicas y reintentos en caso de corte."""
        for attempt in range(max_retries):
            try:
                # Se aumenta un poco el timeout por si la base de datos de 2008 va más lenta
                response = self.session.get(url, timeout=20)
                if response.status_code == 404:
                    return None  
                response.raise_for_status()
                
                # Pausa dinámica (jitter) normal si todo va bien
                time.sleep(random.uniform(0.7, 1.5)) 
                
                return BeautifulSoup(response.text, 'html.parser')

            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                # Controla el error exacto que te ha saltado ("Connection aborted / reset by peer")
                print(f"  [!] Conexión cortada en {url}. Intento {attempt + 1}/{max_retries}. Esperando 5s...")
                if attempt == max_retries - 1:
                    return None
                time.sleep(5)
                
            except requests.RequestException as e:
                # Otros errores HTTP (como 500, 502, 503)
                print(f"  [!] Error descargando {url}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(5)
                
        return None

    def extract_article_data(self, soup: BeautifulSoup, url: str, article_id: str) -> Dict[str, Any]:
        data = {
            "id": article_id, 
            "url": url, 
            "titulo": "", 
            "secciones": [],  # Ahora es una lista que agrupará todas las jerarquías de sección
            "fechaPublicacion": "", 
            "organismo": "", 
            "contenido_texto": ""
        }
        
        wrapper = soup.find(class_=re.compile("anuncio|detalle", re.I))
        if wrapper:
            lines = [line.strip() for line in wrapper.text.split('\n') if line.strip()]
            
            if not lines:
                return data
                
            # Línea 0: Siempre es el número de boletín y fecha
            data['fechaPublicacion'] = self._parse_date(lines[0])
            
            idx = 1
            secciones = []
            
            # Buscar recursivamente todas las líneas que sean "secciones"
            # Empiezan por "I. ", "II. " o "1.", "1.1.", "1.2.2.", etc.
            while idx < len(lines):
                line = lines[idx]
                is_section = False
                
                # Regex para números romanos: I., II., III., IV., V., VI.
                if re.match(r'^(I|II|III|IV|V|VI)\.\s', line):
                    is_section = True
                # Regex para numerales: 1., 1.1., 2.2.1.
                elif re.match(r'^\d+(\.\d+)*\.\s', line):
                    is_section = True
                    
                if is_section:
                    secciones.append(line)
                    idx += 1
                else:
                    break
                    
            data['secciones'] = secciones
            
            # Comprobar si la siguiente línea es el Organismo (Ayuntamiento, Tribunal...)
            # Suelen estar escritas íntegramente en MAYÚSCULAS y ser cortas
            if idx < len(lines):
                line = lines[idx]
                if line.isupper() and len(line) < 100:
                    data['organismo'] = line
                    idx += 1
                    
            # La siguiente línea es el título real del anuncio
            if idx < len(lines):
                data['titulo'] = lines[idx]
                idx += 1
                
            # Todo lo demás es el contenido íntegro
            if idx < len(lines):
                data['contenido_texto'] = "\n".join(lines[idx:])
                
        return data

    def scrape_bulletin(self, year: int, number: int, article_counter: int) -> int:
        url_sumario_es = self.lang_config["es"]["sumario"].format(year=year, number=number)
        
        print(f"\n[*] Procesando boletín {year}/{number}...")
        
        soup_es = self.get_html(url_sumario_es)
        if not soup_es:
            return -1  # Señal de fin de año

        links_es = soup_es.find_all('a', href=re.compile(r'/es/anuncio/'))
        
        urls_es = []
        for link in links_es:
            href = link.get('href')
            if href.startswith('/'): href = "https://bon.navarra.es" + href
            if href not in urls_es: urls_es.append(href)

        if not urls_es:
            return article_counter

        print(f"  [+] Encontrados {len(urls_es)} artículos.")
        
        file_es_path = self.output_dir / f"bon_es_{year}.jsonl"
        file_eu_path = self.output_dir / f"bon_eu_{year}.jsonl"

        with open(file_es_path, 'a', encoding='utf-8') as f_es, \
             open(file_eu_path, 'a', encoding='utf-8') as f_eu:
             
            for url_es in urls_es:
                url_eu = url_es.replace("/es/anuncio/", "/eu/iragarkia/")
                
                soup_art_es = self.get_html(url_es)
                soup_art_eu = self.get_html(url_eu)

                if soup_art_es:
                    data_es = self.extract_article_data(soup_art_es, url_es, f"bon_es_{article_counter}")
                    f_es.write(json.dumps(data_es, ensure_ascii=False) + "\n")
                    
                if soup_art_eu:
                    data_eu = self.extract_article_data(soup_art_eu, url_eu, f"bon_eu_{article_counter}")
                    f_eu.write(json.dumps(data_eu, ensure_ascii=False) + "\n")
                
                article_counter += 1

        return article_counter

    def run(self, start_year: int, end_year: int):
        checkpoint = self.load_checkpoint()
        
        current_year = checkpoint["year"] if checkpoint["year"] and start_year <= checkpoint["year"] <= end_year else start_year
        current_number = checkpoint["number"] if checkpoint["year"] == current_year else 1
        article_counter = checkpoint["article_counter"] if checkpoint["year"] == current_year else 1

        try:
            for year in range(current_year, end_year + 1):
                print(f"\n=================== AÑO {year} ===================")
                
                for number in range(current_number, 400):
                    new_counter = self.scrape_bulletin(year, number, article_counter)
                    
                    if new_counter == -1:
                        print(f"[!] Boletín {number} del {year} no existe. Pasando al siguiente año.")
                        current_number = 1
                        article_counter = 1
                        self.save_checkpoint(year + 1, 1, 1)
                        break 
                    else:
                        article_counter = new_counter
                        self.save_checkpoint(year, number + 1, article_counter)
                        
        except KeyboardInterrupt:
            print("\n[!] Ejecución cancelada por el usuario. El progreso ha sido guardado.")
            sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Obtener actos administrativos del BON (Navarra)")
    parser.add_argument("directory", type=str, help="Directorio donde se guardarán los datos (ej. output_bon)")
    parser.add_argument("añoinicio", type=int, help="Año de inicio")
    parser.add_argument("añofin", type=int, help="Año de fin")
    
    args = parser.parse_args()
    
    scraper = BONScraper(output_dir=args.directory)
    scraper.run(start_year=args.añoinicio, end_year=args.añofin)
