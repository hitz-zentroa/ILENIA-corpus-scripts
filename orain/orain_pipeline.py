import argparse
import requests
import json
import xml.etree.ElementTree as ET
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

from orain_scrapping_urls import scrap_file
from orain_separate_docs import separar_docs_por_idioma

def get_max_date_from_jsonl(filepath: Path) -> str:
    """Reads a JSONL file and returns the most recent date found."""
    max_date = None
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            doc = json.loads(line)
            # Fallback to fecha_publicacion if actualizacion is empty/None
            doc_date = doc.get("fecha_actualizacion") or doc.get("fecha_publicacion")
            if doc_date:
                # Ensure we only compare the YYYY-MM-DD part
                doc_date = doc_date.split("T")[0]
                if max_date is None or doc_date > max_date:
                    max_date = doc_date
    return max_date

def merge_jsonl_by_id(target_filepath: Path, new_jsonl_filepath: Path):
    """Overwrites or adds new articles into the yearly JSONL using unique_id."""
    data = {}
    
    # 1. Load existing yearly data
    if target_filepath.exists():
        with open(target_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                doc = json.loads(line)
                data[doc["unique_id"]] = doc
                
    # 2. Update with new data (overwriting duplicates from the same day)
    if new_jsonl_filepath.exists():
        with open(new_jsonl_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                doc = json.loads(line)
                data[doc["unique_id"]] = doc
                
    # 3. Write everything back
    target_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(target_filepath, 'w', encoding='utf-8') as f:
        for doc in data.values():
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

def get_urls_for_dates(target_dates: set, output_filepath: Path):
    """Fetches EU sitemaps based on the years of the target dates."""
    HEADERS = {"User-Agent": "OrainArchiveCrawler/1.0"}
    DELAY = 0.5
    namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    session = requests.Session()
    session.headers.update(HEADERS)

    # Determine which years we need archive sitemaps for
    years = {d.split("-")[0] for d in target_dates}
    
    # Always include the news sitemap, plus the specific yearly archives
    sitemaps_eu = ["https://orain.eus/eu/sitemap-news.xml"]
    for y in years:
        sitemaps_eu.append(f"https://orain.eus/eu/sitemap-archive-{y}.xml")

    articles_dict = {}
    urls_eu_set = set()
    current_id = 1

    print(f"Buscando URLs para las fechas: {sorted(list(target_dates))}")

    for sitemap_url in sitemaps_eu:
        print(f"  Revisando sitemap: {sitemap_url}")
        try:
            response = session.get(sitemap_url, timeout=15)
            # If a future year archive doesn't exist yet, just skip it safely
            if response.status_code == 404:
                continue
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            urls = root.findall('ns:url', namespaces)

            for url in urls:
                loc = url.find('ns:loc', namespaces)
                if loc is None or not loc.text:
                    continue

                url_eu = loc.text
                if url_eu in urls_eu_set:
                    continue
                urls_eu_set.add(url_eu)

                # Extract date from URL (e.g. .../2026/03/04/...)
                parts = url_eu.strip("/").split("/")
                try:
                    y, m, d = parts[-4], parts[-3], parts[-2]
                    fecha = f"{y}-{m}-{d}" if y.isdigit() else None
                except IndexError:
                    fecha = None

                if fecha in target_dates:
                    articles_dict[url_eu] = {
                        "id": current_id,
                        "fecha": fecha,
                        "url_es": None,  # We ignore Spanish completely
                        "url_eu": url_eu
                    }
                    current_id += 1
                    
        except requests.RequestException as e:
            print(f"  Error descargando {sitemap_url}: {e}")

        time.sleep(DELAY)

    # Save URLs JSON
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(list(articles_dict.values()), f, ensure_ascii=False, indent=2)

    return output_filepath, len(articles_dict)

def build_master_file(output_dir: Path, today_jsonl: Path, master_filepath: Path):
    """Combines all yearly JSONLs + today's transient JSONL into one master file."""
    with open(master_filepath, 'w', encoding='utf-8') as out_f:
        # Append all yearly files
        for year_dir in sorted(output_dir.glob("20*")):
            if year_dir.is_dir():
                yearly_file = year_dir / f"orain_{year_dir.name}_eu.jsonl"
                if yearly_file.exists():
                    with open(yearly_file, 'r', encoding='utf-8') as in_f:
                        for line in in_f:
                            out_f.write(line)
                            
        # Append today's transient file
        if today_jsonl and today_jsonl.exists():
            with open(today_jsonl, 'r', encoding='utf-8') as in_f:
                for line in in_f:
                    out_f.write(line)

def run_scraping_phase(urls_file: Path, output_dir: Path) -> Path:
    """Helper to run the external scraper and separator logic."""
    scraped_json = Path(scrap_file(str(urls_file)))
    final_jsonl = separar_docs_por_idioma(scraped_json, output_dir)
    return Path(final_jsonl)

def main(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    today_dt = datetime.now()
    today_str = today_dt.strftime("%Y-%m-%d")
    yesterday_str = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    current_year = today_dt.strftime("%Y")

    yearly_dir = output_dir / current_year
    yearly_dir.mkdir(exist_ok=True)
    yearly_file = yearly_dir / f"orain_{current_year}_eu.jsonl"

    # --- PHASE 1: HISTORICAL (Up to Yesterday) ---
    max_date = get_max_date_from_jsonl(yearly_file) if yearly_file.exists() else f"{current_year}-01-01"
    print(f"Última fecha en archivo histórico ({current_year}): {max_date}")

    if max_date < yesterday_str:
        print(f"\n--- FASE 1: Actualizando histórico ({max_date} -> {yesterday_str}) ---")
        
        # Create a list of dates from max_date to yesterday
        start_dt = datetime.strptime(max_date, "%Y-%m-%d")
        yesterday_dt = datetime.strptime(yesterday_str, "%Y-%m-%d")
        delta = yesterday_dt - start_dt
        dates_to_fetch = {(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)}
        
        temp_hist_urls = output_dir / "temp_historical_urls.json"
        _, count = get_urls_for_dates(dates_to_fetch, temp_hist_urls)
        
        if count > 0:
            hist_jsonl = run_scraping_phase(temp_hist_urls, output_dir)
            print("Fusionando datos históricos para eliminar duplicados...")
            merge_jsonl_by_id(yearly_file, hist_jsonl)
            
            # Clean up historical temp files
            os.remove(hist_jsonl)
            os.remove(str(temp_hist_urls).replace(".json", "_scrapeado.json"))
        else:
            print("No se encontraron noticias históricas nuevas.")
        
        if temp_hist_urls.exists(): os.remove(temp_hist_urls)
    else:
        print("\n--- FASE 1: Archivo histórico ya está al día (hasta ayer). Saltando... ---")

    # --- PHASE 2: TODAY'S NEWS (Transient) ---
    print(f"\n--- FASE 2: Descargando noticias de hoy ({today_str}) ---")
    temp_today_urls = output_dir / "temp_today_urls.json"
    _, count_today = get_urls_for_dates({today_str}, temp_today_urls)
    
    today_jsonl = None
    if count_today > 0:
        today_jsonl = run_scraping_phase(temp_today_urls, output_dir)
        os.remove(str(temp_today_urls).replace(".json", "_scrapeado.json"))
    else:
        print("No se encontraron noticias para hoy (todavía).")
        
    if temp_today_urls.exists(): os.remove(temp_today_urls)

    # --- PHASE 3: MASTER FILE GENERATION ---
    print("\n--- FASE 3: Generando archivo Master ---")
    master_filepath = output_dir / f"orain_{today_str}_master_eu.jsonl"
    build_master_file(output_dir, today_jsonl, master_filepath)
    
    # Clean up today's transient file now that it's in the master
    if today_jsonl and today_jsonl.exists():
        os.remove(today_jsonl)

    print(f"\n✅ Pipeline completado. Archivo listo para indexar: {master_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orain Crawler Pipeline (Lambda Architecture)")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent, 
                        help="Directorio principal de datos (ej. data/orain)")
    args = parser.parse_args()
    
    main(args.output_dir)
