import argparse
import logging
import os
import time
import requests

from bs4 import BeautifulSoup

from util import download_pdf


headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def cmd_default(url, corpus_name):

    base_folder = os.path.join("pdfs", corpus_name)
    os.makedirs(base_folder, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    issue_elements = soup.select("div.issues.media-list li a")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    download_num = 0
    total_issues = len(issues)
    logging.warning(f"Total issues found: {total_issues}")

    for issue_title, issue_url in issues:
        time.sleep(1)
        logging.warning(f"Processing issue: {issue_title}")

        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url.replace("http", "https"), headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        articles = issue_soup.select("div.article-summary.media")
        for article in articles:
            title_tag = article.select_one("h3.media-heading a")
            pdf_tag = article.select_one("a.galley-link")

            if not (title_tag and pdf_tag):
                logging.warning("PDF or title elements not found -- skipping article")
                continue

            title = title_tag.get_text(strip=True)
            pdf_url = pdf_tag["href"]

            safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
            pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

            pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
            pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")
            pdf_link_tag = pdf_soup.find("a", class_="download")
            if not pdf_link_tag:
                logging.warning("PDF hyperlink not found -- skipping article")
                continue

            pdf_link = pdf_link_tag["href"]
            try:
                download_pdf(headers, pdf_link, pdf_path)
                download_num += 1
            except Exception as e:
                logging.exception(f"PDF download failed: {e}")

    logging.warning(f"{download_num}/{total_issues} PDFs downloaded")


def cmd_osagaiz(url, corpus_name):

    base_folder = os.path.join("pdfs", corpus_name)
    os.makedirs(base_folder, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    issue_elements = soup.select("div.card.issue-summary h2.issue-summary-series a")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    download_num = 0
    total_issues = len(issues)
    logging.warning(f"Total issues found: {total_issues}")

    for issue_title, issue_url in issues:
        time.sleep(1)
        logging.warning(f"Processing issue: {issue_title}")

        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        articles = issue_soup.select("div.article-summary")
        for article in articles:
            title_tag = article.select_one("div.article-summary-title a")
            pdf_tag = article.select_one("div.article-summary-galleys a.btn")

            if not (title_tag and pdf_tag):
                logging.warning("PDF or title elements not found -- skipping article")
                continue

            title = title_tag.get_text(strip=True)
            pdf_url = pdf_tag["href"]

            safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
            pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

            pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
            pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")

            pdf_link_tag = pdf_soup.select_one("div.pdf-download-button a.btn")
            if pdf_link_tag:
                logging.warning("PDF hyperlink not found -- skipping article")
                continue

            pdf_link = pdf_link_tag["href"]
            try:
                download_pdf(headers, pdf_link, pdf_path)
                download_num += 1
            except Exception as e:
                logging.exception(f"PDF download failed: {e}")


def cmd_uztaro(url, corpus_name):

    base_folder = os.path.join("pdfs", corpus_name)
    os.makedirs(base_folder, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces de issues
    issue_elements = soup.select("div.obj_issue_summary a.title")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    download_num = 0
    total_issues = len(issues)
    logging.warning(f"Total issues found: {total_issues}")

    for issue_title, issue_url in issues:
        time.sleep(1)
        logging.warning(f"Processing issue: {issue_title}")

        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        articles = issue_soup.select("div.obj_article_summary")
        for article in articles:
            title_tag = article.select_one("h3.title a")
            pdf_tag = article.select_one("a.obj_galley_link.pdf")

            if not (title_tag and pdf_tag):
                logging.warning("PDF or title elements not found -- skipping article")
                continue

            title = title_tag.get_text(strip=True)
            pdf_url = pdf_tag["href"]

            safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
            pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

            pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
            pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")

            pdf_link_tag = pdf_soup.find("a", class_="download")
            if not pdf_link_tag:
                logging.warning("PDF hyperlink not found -- skipping article")
                continue

            pdf_link = pdf_link_tag["href"]
            try:
                download_pdf(headers, pdf_link, pdf_path)
                download_num += 1
            except Exception as e:
                logging.exception(f"PDF download failed: {e}")

    logging.warning(f"{download_num}/{total_issues} PDFs downloaded")


def cmd_kondaira(url, corpus_name):

    base_folder = os.path.join("pdfs", corpus_name)
    os.makedirs(base_folder, exist_ok=True)

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    issue_elements = soup.select("div.obj_issue_summary a.title")
    issues = [(a.get_text(strip=True), a["href"]) for a in issue_elements]

    download_num = 0
    total_issues = len(issues)
    logging.warning(f"Total issues found: {total_issues}")

    for issue_title, issue_url in issues:
        time.sleep(1)
        logging.warning(f"Processing issue: {issue_title}")

        safe_issue_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in issue_title)
        issue_folder = os.path.join(base_folder, safe_issue_title)
        os.makedirs(issue_folder, exist_ok=True)

        issue_resp = requests.get(issue_url, headers=headers, timeout=10)
        issue_soup = BeautifulSoup(issue_resp.text, "html.parser")

        articles = issue_soup.select("div.obj_article_summary")
        for article in articles:
            title_tag = article.select_one("h3.title a")
            pdf_tag = article.select_one("a.obj_galley_link.pdf")

            if not (title_tag and pdf_tag):
                logging.warning("PDF or title elements not found -- skipping article")
                continue

            title = title_tag.get_text(strip=True)
            pdf_url = pdf_tag["href"]

            safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
            pdf_path = os.path.join(issue_folder, f"{safe_title}.pdf")

            if not pdf_url:
                logging.warning("PDF hyperlink not found -- skipping article")
                continue

            try:
                download_pdf(headers, pdf_url, pdf_path)
                download_num += 1
            except Exception as e:
                logging.exception(f"PDF download failed: {e}")

    logging.warning(f"Total de PDFs descargados: {download_num} de {total_issues} issues.")


def cmd_ekonomiaz(_, corpus_name):

    base_folder = os.path.join("pdfs", corpus_name)
    os.makedirs(base_folder, exist_ok=True)
    download_num = 0

    for i in range(76, 105):
        time.sleep(1)
        logging.warning(f"Processing issue: {i}")

        url = f"https://www.euskadi.eus/web01-a2reveko/es/k86aEkonomiazWar/ekonomiaz/getPubl?idPubl={i}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a", class_="verdana10")

        for a in links:
            span = a.find("span")
            if not (span and "euskera" in span.get_text().lower()):
                continue

            title = str(i) + "_" + span.get_text().strip()
            pdf_url = a["href"].replace("®", "&reg")

            safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in title)
            pdf_path = os.path.join(base_folder, f"{safe_title}.pdf")

            pdf_resp = requests.get(pdf_url, headers=headers, timeout=10)
            pdf_soup = BeautifulSoup(pdf_resp.text, "html.parser")
            pdf_link_tag = pdf_soup.find("a", href=lambda x: x and "downloadPDF" in x)
            if not pdf_link_tag:
                logging.warning("PDF hyperlink not found -- skipping article")
                continue

            pdf_link = pdf_link_tag["href"].replace("8%C2%AE", "&reg").replace("®", "&reg")
            try:
                download_pdf(headers, pdf_link, pdf_path)
                download_num += 1
            except Exception as e:
                logging.exception(f"PDF download failed: {e}")

    logging.warning(f"{download_num} PDFs downloaded")


if __name__ == "__main__":

    COMMANDS = {
        "default": cmd_default,
        "osagaiz": cmd_osagaiz,
        "uztaro": cmd_uztaro,
        "kondaira": cmd_kondaira,
        "ekonomiaz": cmd_ekonomiaz,
    }

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, fn in COMMANDS.items():
        sp = subparsers.add_parser(name)

        sp.add_argument("url")
        sp.add_argument("corpus")
        sp.set_defaults(_handler=fn)

    args = parser.parse_args()
    args._handler(args.url, args.corpus)
