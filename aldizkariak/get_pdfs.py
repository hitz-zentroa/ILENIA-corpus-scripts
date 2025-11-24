import time
import requests
from bs4 import BeautifulSoup
import os
from requests_html import HTMLSession
import html

def main(url, corpus_name):
    base_folder = os.path.join("pdfs", corpus_name)  # Carpeta principal dentro de "pdfs"
    os.makedirs(base_folder, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces de issues
    issue_elements = soup.select("div.issues.media-list li a")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    cont_pdfs = 0
    total_issues = len(issues)
    print(f"Total de issues encontrados: {total_issues}")
    

    for issue_title, issue_url in issues:
        time.sleep(1)
        print(f"Procesando issue: {issue_title}")

        # Limpiar nombre de carpeta del issue
        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url.replace("http", "https"), headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        # Buscar todos los artículos
        articles = issue_soup.select("div.article-summary.media")
        for article in articles:
            title_tag = article.select_one("h3.media-heading a")
            pdf_tag = article.select_one("a.galley-link")
            
            if title_tag and pdf_tag:
                title = title_tag.get_text(strip=True)
                pdf_url = pdf_tag["href"]

                safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
                pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

                # Descargar PDF
                #print(f"  Descargando: {title}")
                pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
                pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")
                
                pdf_link_tag = pdf_soup.find("a", class_="download")
                if pdf_link_tag:
                    pdf_link = pdf_link_tag["href"]
                    with requests.get(pdf_link, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        with open(pdf_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                            cont_pdfs += 1
            else:
                print("  No se encontró PDF o título para este artículo.")

    print(f"Total de PDFs descargados: {cont_pdfs} de {total_issues} issues.")


def main_osagaiz(url, corpus_name):
    base_folder = os.path.join("pdfs", corpus_name)  # Carpeta principal dentro de "pdfs"
    os.makedirs(base_folder, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces de issues
    issue_elements = soup.select("div.card.issue-summary h2.issue-summary-series a")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    cont_pdfs = 0
    total_issues = len(issues)
    print(f"Total de issues encontrados: {total_issues}")
    

    for issue_title, issue_url in issues:
        time.sleep(1)
        print(f"Procesando issue: {issue_title}")

        # Limpiar nombre de carpeta del issue
        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        # Buscar todos los artículos
        articles = issue_soup.select("div.article-summary")

        for article in articles:
            title_tag = article.select_one("div.article-summary-title a")
            pdf_tag = article.select_one("div.article-summary-galleys a.btn")

            if title_tag and pdf_tag:
                title = title_tag.get_text(strip=True)
                pdf_url = pdf_tag["href"]

                safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
                pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

                # Descargar PDF
                #print(f"  Descargando: {title}")
                pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
                pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")
               
                pdf_link_tag = pdf_tag = pdf_soup.select_one("div.pdf-download-button a.btn")
                if pdf_link_tag:
                    pdf_link = pdf_link_tag["href"]
                    #print(f"  Descargando: {pdf_link}")
                    with requests.get(pdf_link, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        with open(pdf_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                            cont_pdfs += 1
            else:
                print("  No se encontró PDF o título para este artículo.")

    print(f"Total de PDFs descargados: {cont_pdfs} de {total_issues} issues.")

def main_uztaro(url, corpus_name):
    base_folder = os.path.join("pdfs", corpus_name)  # Carpeta principal dentro de "pdfs"
    os.makedirs(base_folder, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces de issues
    issue_elements = soup.select("div.obj_issue_summary a.title")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    cont_pdfs = 0
    total_issues = len(issues)
    print(f"Total de issues encontrados: {total_issues}")
    

    for issue_title, issue_url in issues:
        time.sleep(1)
        print(f"Procesando issue: {issue_title}")

        # Limpiar nombre de carpeta del issue
        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        # Buscar todos los artículos
        articles = issue_soup.select("div.obj_article_summary")

        for article in articles:
            title_tag = article.select_one("h3.title a")
            #title = title_tag.get_text(strip=True)
            pdf_tag = article.select_one("a.obj_galley_link.pdf")

            if title_tag and pdf_tag:
                title = title_tag.get_text(strip=True)
                pdf_url = pdf_tag["href"]

                safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
                pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

                # Descargar PDF
                #print(f"  Descargando: {title}")
                pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
                pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")
               
                pdf_link_tag = pdf_soup.find("a", class_="download")
                if pdf_link_tag:
                    pdf_link = pdf_link_tag["href"]
                    #print(f"  Descargando: {pdf_link}")
                    with requests.get(pdf_link, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        with open(pdf_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                            cont_pdfs += 1
            else:
                print("  No se encontró PDF o título para este artículo.")

    print(f"Total de PDFs descargados: {cont_pdfs} de {total_issues} issues.")

def main_kondaira(url, corpus_name):
    base_folder = os.path.join("pdfs", corpus_name)  # Carpeta principal dentro de "pdfs"
    os.makedirs(base_folder, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces de issues
    issue_elements = soup.select("div.obj_issue_summary a.title")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    cont_pdfs = 0
    total_issues = len(issues)
    print(f"Total de issues encontrados: {total_issues}")
    

    for issue_title, issue_url in issues:
        time.sleep(1)
        print(f"Procesando issue: {issue_title}")

        # Limpiar nombre de carpeta del issue
        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        # Buscar todos los artículos
        articles = issue_soup.select("div.obj_article_summary")

        for article in articles:
            title_tag = article.select_one("h3.title a")
            #title = title_tag.get_text(strip=True)
            pdf_tag = article.select_one("a.obj_galley_link.pdf")

            if title_tag and pdf_tag:
                title = title_tag.get_text(strip=True)
                pdf_url = pdf_tag["href"]

                safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
                pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

                # Descargar PDF
                
                if pdf_url:
                    #print(f"  Descargando: {pdf_link}")
                    with requests.get(pdf_url, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        with open(pdf_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                            cont_pdfs += 1
            else:
                print("  No se encontró PDF o título para este artículo.")

    print(f"Total de PDFs descargados: {cont_pdfs} de {total_issues} issues.")

def main_ekonomiaz(url, corpus_name):
    base_folder = os.path.join("pdfs", corpus_name)  # Carpeta principal dentro de "pdfs"
    os.makedirs(base_folder, exist_ok=True)
    cont_pdfs = 0
    
    for i in range(76, 105):
        print(f"Procesando idPubl={i}")
        url = f"https://www.euskadi.eus/web01-a2reveko/es/k86aEkonomiazWar/ekonomiaz/getPubl?idPubl={i}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Buscar todos los enlaces
        links = soup.find_all("a", class_="verdana10")

        # Filtrar los que tengan span con texto "euskera"
        for a in links:
            span = a.find("span")
            if span and "euskera" in span.get_text().lower():
                pdf_path_title = str(i) + "_" + span.get_text().strip() + ".pdf"
                print(a["href"].replace("®", "&reg"))
                #cont_pdfs += 1
                url_euskera = a["href"].replace("®", "&reg")
        
                response = requests.get(url_euskera, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                a = soup.find("a", href=lambda x: x and "downloadPDF" in x)

                if a:
                    pdf_url = a["href"].replace("8%C2%AE", "&reg").replace("®", "&reg")
                    #pdf_url = html.unescape(pdf_url)
                    print(f"  Descargando: {pdf_url}")
                    
                    
                    #print(f"  Descargando: {pdf_link}")
                    with requests.get(pdf_url, headers=headers, stream=True) as r:
                        r.raise_for_status()
                        with open(os.path.join(base_folder, pdf_path_title), "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                            cont_pdfs += 1
                else:
                    print("  No se encontró Descargar")

    print(f"Total de PDFs descargados: {cont_pdfs}")

if __name__ == "__main__":
    corpus_name = "ekonomiaz"
    # for i in range(2, 7): # va desde 2 hasta 6
    #     url = f"https://aldizkariak.ueu.eus/index.php/uztaro/issue/archive/{i}"
    #     main_uztaro(url, corpus_name)
    url = "https://www.euskadi.eus/web01-a2reveko/eu/k86aEkonomiazWar/ekonomiaz/inicio"
    main_ekonomiaz(url, corpus_name)

