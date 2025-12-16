# PARLEUS Dataset  
**A Fully Basque Dataset of Basque Parliament Debates**

PARLEUS is a dataset created to fully capture the multilingual dynamics of debates in the Basque Parliament (Eusko Legebiltzarra). The dataset is constructed from official PDF transcripts available on the Parliament’s website.

These transcripts contain the **original speeches**—which may be in **Basque**, **Spanish**, or involve **code-switching**—as well as their **official translations** into the other language. Each PDF is formatted in two parallel columns:  
- **Left column:** original speech  
- **Right column:** translation  

However, mistakes and inconsistencies in the PDFs (typos, misalignments, formatting issues) make automatic sentence-by-sentence alignment difficult. Many of these issues were corrected manually during dataset creation.

PARLEUS follows an extraction, alignment and enrichment process, producing a high-quality resource that includes sentence-level multilingual data, speaker metadata, party affiliation, and inferred debate topics.

---

## 📦 Dataset Overview

Each dataset instance includes:
- Speech (Basque or Spanish)  
- Language 
- Speaker name  
- Political party  
- Debate topic  
- Session metadata (date, session ID, legislature)

---

## 🛠️ Data Collection & Processing Pipeline

### 1. Collecting PDFs  
- Choose dataset timespan (in this case: **2012–present**).  
- For each legislature, obtain the XML index from the Legebiltzarra website containing all transcript URLs.  

### 2. Extracting Metadata & Downloading Transcripts  
- Iterate through each item in the XML file.  
- Extract metadata such as:
  - **Session ID**  
  - **Date**  
- Access the transcript PDF via its URL and download it.

### 3. Reading and Parsing the PDFs  
- Extract text from each PDF.  
- Verify whether it uses the expected **two-column layout** (original + translation).  
- For each page:
  - Split the text into **left** and **right** columns.  
  - Save each column separately.

### 4. Aligning and Processing Speech Segments  
Process left and right columns **simultaneously**:

1. **Speaker Detection**  
   A regular expression was used to detect speaker labels:  
   - ≥ 10 uppercase letters, spaces, or hyphens  
   - Up to 30 trailing arbitrary characters  
   - Ending in `:` or `).`

2. **Cross-Column Check**  
   Ensure the detected speaker is identical in both columns.

3. **Sentence Extraction**  
   Split the speech into sentences.

4. **Language Identification**  
   Use **FastText** to detect the language of each sentence (Basque/Spanish).

5. **Storage**  
   Save:
   - Speaker  
   - Speech in both languages  
   - Language-separated sentence lists  

---

## 🧩 Metadata Enrichment

### Speaker Party Mapping  
A mapping of all speakers to their political parties was created for each legislature.  
This information was obtained from the official Legebiltzarra website.

### Topic Extraction  
The President of the Basque Parliament (*Lehendakaria*) introduces each new agenda item with consistent phrasing, such as:  
- *“Gai-zerrendako k puntua…”*  
- *“…orden del día…”*  

Using a regex pattern, these markers were detected, and the **following sentence** was extracted as the **debate topic**.

---

## 🚀 USAGE

### 1) PARSE PDF TO TXT:
```bash
$ python3 parse_pdf_txt.py parse_pdf/legislatura_10/c_pleno_open_data_10.xml 10
```
**Output**: json_output_10.json


### 2) EXTRACT AND SEPARATE INTERVENTIONS FOR EACH DOCUMENT:
NOTE: we asume that we have the json outputs of the previous step in a subfolder below the root_path of the argument for each legislature --> legislature_\<num\> 
```bash
$ python3 parse_interventions.py parse_pdf
```
**Output**: legislature_\<num\>/json_intervenciones_\<num\>.json


### 3) DIVIDE LANGUAGES:
```bash
$ python3 parse_interventions.py parse_pdf
```
**Output**: legislature_<num>/parlamentu_\<num\>_eu.json

**Output**: legislature_<num>/parlamentu_\<num\>_es.json


### 4) ADD ID TO DOCS:
```bash
$ python3 add_id_docs.py parse_pdf
```
**Output**: legislature_<num>/parlamentu_\<num\>_eu_final.jsonl

**Output**: legislature_<num>/parlamentu_\<num\>_es_final.jsonl

**FINAL Output**: parleus_\<lang\>.jsonl

---