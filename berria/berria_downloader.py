import datetime
from pathlib import Path

import requests


def get_last_date_from_folder(folder: Path, year: int) -> datetime.date:
    pattern = f"berria_{year}-*.xml"
    files = sorted(folder.glob(pattern))
    if not files:
        # No existing files: start at Jan 1 of the year
        return datetime.date(year, 1, 1) - datetime.timedelta(days=1)
    # Filenames are named like berria_yyyy-mm-1dd.xml
    last_file = files[-1].name  # e.g. 'berria_2025-03-16.xml'
    date_str = last_file[len("berria_"):-len(".xml")]  # '2025-03-16'
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def get_start_and_end_dates(base_dir: Path):
    # Find the start and end dates
    end_date = datetime.date.today() - datetime.timedelta(days=4)  # Berria is ~4 days behind

    years = range(2024, end_date.year + 1)

    last_date = None

    for year in years:
        folder = base_dir / str(year)
        if folder.exists():
            last_date_in_folder = get_last_date_from_folder(folder, year)
            if last_date is None or last_date_in_folder > last_date:
                last_date = last_date_in_folder

    if last_date is None:
        start_date = datetime.date(2024, 1, 1)  # no files at all, start from 01/01/2024
        print(f"Fetching from {start_date} through {end_date}...")
    else:
        start_date = last_date + datetime.timedelta(days=1)
        print(f"Resuming from {start_date} through {end_date}...")

    return start_date, end_date


def download_for_date(d: datetime.date, base_url: str, base_dir: Path):
    year_str = d.strftime("%Y")
    folder = base_dir / year_str
    folder.mkdir(parents=True, exist_ok=True)

    fname = f"berria_{d.strftime('%Y-%m-%d')}.xml"
    out_path = folder / fname
    if out_path.exists():
        print(f"  Skipping {fname}, already downloaded.")
        return

    url = f"{base_url}/{year_str}/{fname}"
    print(f"  Downloading {url} → {out_path}")
    resp = requests.get(url)
    if resp.status_code == 200:
        content = resp.content

        if content.lstrip().startswith(b"<?xml"):
            out_path.write_bytes(content)
            print(f"    → Saved {fname}\n")
        else:
            print(f"    → Skipped {fname}: response not XML (probably a 404 page)\n")
    else:
        print(f"    → Failed (status {resp.status_code})\n")
