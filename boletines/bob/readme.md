# BOB (Boletín Oficial de Bizkaia) Scraping Scripts

This folder contains Python scripts for scraping and extracting text from the Official Bulletin of Bizkaia (BOB - https://www.bizkaia.eus/es/bob).

## Overview

The Official Bulletin of Bizkaia is published in PDF format. These scripts download the PDFs and extract their text content, generating JSONL files containing all articles for each year.

## Scripts

### bob_scrape.py

Downloads PDF files from the BOB website and extracts metadata.

**Usage:**
```bash
python bob_scrape.py destination_directory/ start_year end_year language[es,eu]
```

**Output:**
- One folder per year containing the downloaded PDFs
- One JSONL file per year with article metadata (excluding article text)

**JSONL Format:**
```json
{"fecha": "2025-08-26", "seccion": "Bizkaiko Lurralde Historikoko Toki Administrazioa", "organismo_emisor": "Berangoko Udala", "titulo": "Bitarteko funtzionarioa izendatzea. Agentea.", "link": "https://www.bizkaia.eus/lehendakaritza/Bao_bob/2025/08/26/II-5032_eus.pdf", "autonumerico": 7, "nombre_original_pdf": "II-5032_eus.pdf"}
```

### corregir_jsonl.py

Fills in missing `organismo_emisor` fields in the JSONL files. The BOB website only displays the issuing organization for the first article in a group, so this script propagates that information to subsequent articles.

### pdf_to_text.py

Extracts text content from articles published **after April 3, 2017** (when the PDF format changed).

**Usage:**
```bash
python pdf_to_text.py year_directory/ input_jsonl.jsonl output_jsonl.jsonl
```

**Example:**
```bash
python pdf_to_text.py 2018/ datos_2018.jsonl articulos_2018.jsonl
```

**Output:**
Adds a `contenido_texto` field to each article:

```json
{"fecha": "2025-08-26", "seccion": "Bizkaiko Lurralde Historikoko Toki Administrazioa", "organismo_emisor": "Berangoko Udala", "titulo": "Bitarteko funtzionarioa izendatzea. Agentea.", "link": "https://www.bizkaia.eus/lehendakaritza/Bao_bob/2025/08/26/II-5032_eus.pdf", "autonumerico": 7, "nombre_original_pdf": "II-5032_eus.pdf", "contenido_texto": "II. ATALA\nBIZKAIKO LURRALDE HISTORIKOKO TOKI ADMINISTRAZIOA\nBerangoko Udala\nBitarteko funtzionarioa izendatzea. Agentea\nUztaileko 21eko 2025-909 zenbakiko Alkatetza Dekretuaren bidez, Mikel Rodriguez\nJambrina jauna bitarteko funtzionario izendatu zen Udaltzaingoko Agente izateko, eta\nhorrek ondorioak izango ditu 2025eko uztailaren 23tik lanpostu hutsa bete arte (31627).\nHori guztia argitara ematen da, indarrean dagoen legeria betez.\nBerangon, 2025eko abuztuaren 18an.—Alkatea, Itziar Aguinagalde Avedillo"}
```

### oldformat_pdf_to_text.py

Extracts text from PDFs published between **January 1, 2011 and March 30, 2017** (old format).

**Usage:** Same as `pdf_to_text.py`

**Disclaimer:** Old format PDFs have two columns with mixed Basque and Spanish text, which means 100% article recovery is not always possible.

### older_pdf_to_text.py

Extracts text from PDFs published in **2008, 2009, and 2010**.

Similar to `oldformat_pdf_to_text.py` but with modifications to handle format differences specific to these years, which otherwise resulted in significant article loss.

## Workflow

1. Run `bob_scrape.py` to download PDFs and generate metadata JSONL files
2. Run `corregir_jsonl.py` to fill in missing organization information
3. Run the appropriate text extraction script based on year:
   - `older_pdf_to_text.py` for 2008-2010
   - `oldformat_pdf_to_text.py` for 2011-2017 (before April 3)
   - `pdf_to_text.py` for April 3, 2017 onwards

## Requirements

- Python 3.x
- pdfplumber
