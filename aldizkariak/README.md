# Basque Journals PDF Extraction and Processing

This project provides scripts to **download, process, and structure PDFs** from various Basque journals. It extracts the PDFs from journal websites and converts them into structured JSONL files containing the text and metadata.

The workflow is divided into three main scripts:

---

## 1️⃣ `get_pdfs.py`

This script **downloads PDFs** from multiple Basque journals. For each journal, it creates a folder with subfolders for each issue, containing all the PDFs.

### Journals and URLs

- **Ekaia**: [https://ojs.ehu.eus/index.php/ekaia](https://ojs.ehu.eus/index.php/ekaia)  
- **Gogoa**: [https://ojs.ehu.eus/index.php/Gogoa](https://ojs.ehu.eus/index.php/Gogoa)  
- **Tantak**: [https://ojs.ehu.eus/index.php/Tantak/](https://ojs.ehu.eus/index.php/Tantak/)  
- **Ekonomiaz**: [https://www.euskadi.eus/web01-a2reveko/es/k86aEkonomiazWar/ekonomiaz/inicio](https://www.euskadi.eus/web01-a2reveko/es/k86aEkonomiazWar/ekonomiaz/inicio)  
- **Kondaira**: [https://aldizkariak.ueu.eus/index.php/kondaira](https://aldizkariak.ueu.eus/index.php/kondaira)  
- **Uztaro**: [https://aldizkariak.ueu.eus/index.php/uztaro](https://aldizkariak.ueu.eus/index.php/uztaro)  
- **Osagaiz**: [https://aldizkariak.ueu.eus/index.php/osagaiz](https://aldizkariak.ueu.eus/index.php/osagaiz)  

### Usage

```
python get_pdfs.py {default,osagaiz,uztaro,kondaira,ekonomiaz} url corpus

positional arguments:
  url -- root URL for the journal to be downloaded
  corpus -- name of the corpus, used to compute the output path
```

> Output: A folder for each journal, containing subfolders for each issue, which store the PDFs.

---

## 2️⃣ `pdf2md.py`

This script **reads all the downloaded PDFs** from the journals and converts them into **JSONL files** with the text content and metadata of each PDF.  

- Each JSONL instance contains:
  - Journal name  
  - Issue information  
  - PDF filename  
  - Full text content  
  - Metadata (authors, date, volume, issue number, etc.)

---

## 3️⃣ `pdf2md_ikergazte.py`

This script is specialized for the **IkerGazte journal**, which has a specific PDF format.  

- Reads all PDFs from IkerGazte  
- Extracts text and metadata  
- Saves the data in a **JSONL file**  

---