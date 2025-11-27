# Berria Crawl

This repository contains a Python pipeline for downloading and parsing XML files from Berria, a Basque news source, and converting them into JSONL (JSON Lines) format for downstream processing.

## Features

- Download daily XML files, organized by year folders (e.g. `2024/`, `2025/`)
- Resume downloading from the last available date to avoid duplicates
- Parse XML files into JSONL, one JSON object per line
- Clean and normalize article text (HTML removal, whitespace normalization, control character stripping)
- Optional dataset formatter to restructure JSONL output for training/analysis
- Command-line interface to run the full pipeline or only specific steps

## Repository Structure

- `berria_pipeline.py`: Main pipeline script; orchestrates downloading and parsing
- `berria_downloader.py`: Handles date range detection and XML downloads
- `ixaml_parser.py`: Parses XML into JSONL and performs text cleaning
- `berria_dataset_formatter.py`: Optional script to reformat JSONL files for training/analysis

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/berria-crawl.git
cd berria-crawl
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install `requests` for HTTP downloads:
```bash
pip install requests
```

## Configuration

In `berria_downloader.py` and `berria_pipeline.py`, there is a placeholder base URL for the Berria XML files:
```python
base_url = "https://www.berria.eus/placeholder"
```

Replace this with the real base URL path that serves the XML files. The code assumes filenames of the form:
```
berria_YYYY-MM-DD.xml
```

and directories grouped by year, e.g.:
```
2024/berria_2024-01-01.xml
2024/berria_2024-01-02.xml
...
```

## Usage

All commands are run from the repository root.

### Full pipeline (download + parse)

Runs the downloader, then parses all available XML files into a single JSONL file named from the latest date, e.g. `berria_31_03_2025.jsonl`:
```bash
python berria_pipeline.py
```

### Download only

Only download missing XML files:
```bash
python berria_pipeline.py --download-only
```

### Parse only

Only parse existing XML files into JSONL:
```bash
python berria_pipeline.py --parse-only
```

### Custom base directory

By default, the base directory is the current working directory. To store XML files and JSONL output in a specific path:
```bash
python berria_pipeline.py --base-dir /path/to/berria
```

This directory will contain year subfolders like `2024/`, `2025/`, and the resulting `berria_DD_MM_YYYY.jsonl` file.

### Format dataset (optional)

After generating the JSONL file, you can optionally reformat it for training or analysis using the dataset formatter:
```bash
python berria_dataset_formatter.py berria_31_03_2025.jsonl berria_formatted.jsonl
```

This script transforms each record by:
- Placing the `url` field first
- Creating a consolidated `text` field from: title (`titularra`), subtitle (`azpititularra`), author and date (`egilea`, `fetxa`), and main text (`testua`)
- Preserving all original fields after the `text` field

Example transformation:
```json
{"url": "https://...", "text": "Titularra\n\nAzpititularra\n\nEgilea: Izen-Abizenak / Data: 2025-03-31\n\nArtikuluaren testua...", "titularra": "Titularra", ...}
```

## How it works

### Downloading

1. Determines a start date based on the latest existing XML file per year folder
2. Uses today minus a small offset of 4 days as the end date, to account for publication delay
3. Iterates day-by-day, building URLs like:
```
   {BASE_URL}/{YEAR}/berria_YYYY-MM-DD.xml
```
4. Skips files that already exist and only saves responses that look like valid XML

### Parsing and cleaning

1. Scans year folders named like `2024`, `2025` and finds all `berria_YYYY-MM-DD.xml` files
2. Parses each XML file and iterates over `<row>` elements and nested `<field name="...">` elements
3. For each field:
   - Decodes HTML entities
   - Converts `<p>` and `<br>` tags to newlines
   - Removes simple HTML tags and custom markers
   - Normalizes whitespace and removes forbidden control characters
4. Writes each row as a single JSON object line in a `.jsonl` file

### Dataset formatting (optional)

The optional `berria_dataset_formatter.py` script restructures the parsed JSONL output:
1. Reads each line from the input JSONL file
2. Constructs a clean `text` field by concatenating:
   - Title (`titularra`)
   - Subtitle (`azpititularra`)
   - Author and date metadata (`egilea`, `fetxa`)
   - Main article text (`testua`)
3. Places `url` first, followed by `text`, then all remaining original fields
4. Writes each transformed record as a new line in the output JSONL file

## Output

The final output is a JSONL file, for example:
```
berria_31_03_2025.jsonl
```

Each line is an independent JSON object representing one article or row, which is convenient for streaming and large-scale processing.

If you use the dataset formatter, you'll get a reformatted file like:
```
berria_formatted.jsonl
```

where each record has a consolidated `text` field suitable for language model training or text analysis.