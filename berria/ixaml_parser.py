import datetime
import html
import json
import os
import re
import xml.etree.ElementTree as ET


def find_year_folders_and_last_date(base_dir='.'):
    """
    Detect folders that look like '2024', '2025', etc.
    While scanning them, also determine the newest article date
    by reading XML filenames (berria_YYYY-MM-DD.xml).
    Returns (sorted_folder_list, last_date_or_None).
    """
    year_folders = []
    last_date = None

    for name in os.listdir(base_dir):
        # Folder must be 4 digits (e.g., "2024")
        if len(name) == 4 and name.isdigit():
            folder_path = os.path.join(base_dir, name)
            if os.path.isdir(folder_path):
                year_folders.append(folder_path)

                # Scan this folder for XML filenames
                for fname in os.listdir(folder_path):
                    if fname.startswith('berria_') and fname.endswith('.xml'):
                        date_str = fname[len("berria_"):-len(".xml")]  # 'YYYY-MM-DD'
                        try:
                            d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            if last_date is None or d > last_date:
                                last_date = d
                        except ValueError:
                            continue

    return sorted(year_folders), last_date


def clean_text(text):
    if not text:
        return text

    # 1. Decode HTML entities
    text = html.unescape(text)

    # 2. Turn <p> and <br> into newlines
    text = re.sub(r'</?p\s*[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # 3. Remove [articles:12345]‑style tags
    text = re.sub(r'\[articles:\d+\]', '', text)

    # 4. Strip any other HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # 5. Replace non‑breaking spaces
    text = text.replace('\xa0', ' ')

    # 6. Remove iframe‑resize scripts
    text = re.sub(
        r'iFrameResize\(\{.*?\}\,\s*\'#[^\)]+\'\);?',
        '',
        text,
        flags=re.DOTALL
    )

    # 7. Normalize line‑endings and collapse spaces/tabs (but keep \n)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)

    # 8. Squash 3+ newlines into exactly 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 9. Trim whitespace on each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines).strip()

    return text


# compile once at module level
_INVALID_XML_CHARS = re.compile(
    r'[\x00-\x08\x0B\x0C\x0E-\x1F]'
)


def parse_folders_to_jsonl(folder_paths, jsonl_file):
    with open(jsonl_file, 'w', encoding='utf-8') as outfile:
        for folder_path in folder_paths:
            xml_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith('.xml')],
                key=lambda x: x
            )
            for filename in xml_files:
                file_path = os.path.join(folder_path, filename)
                try:
                    # first, try the normal parse
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                except ET.ParseError as e1:
                    print(f"  [ParseError] {filename}: {e1}. Attempting to strip invalid chars…")

                    # read raw text
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        raw = f.read()

                    # strip all forbidden control characters
                    cleaned = _INVALID_XML_CHARS.sub('', raw)

                    try:
                        # parse from string
                        root = ET.fromstring(cleaned)
                    except ET.ParseError as e2:
                        print(f"    → [FATAL ERROR] Still failed after cleaning: {e2}. Skipping.")
                        continue
                    else:
                        print(f"    → Success after cleaning, proceeding.")

                except Exception as e:
                    print(f"Error opening {filename}: {e}")
                    continue

                # if we get here, 'root' must be valid
                for row in root.findall('row'):
                    row_data = {}
                    for field in row.findall('field'):
                        name = field.get('name')
                        raw = field.text
                        row_data[name] = clean_text(raw) if raw is not None else None

                    outfile.write(json.dumps(row_data, ensure_ascii=False) + '\n')

                print(f"Processed {folder_path}/{filename}")
