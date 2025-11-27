#!/usr/bin/env python3
"""
Pipeline to download Berria XML files and parse them into JSONL.
Usage examples:

# Download and parse:
python pipeline.py

# Only download:
python pipeline.py --download-only

# Only parse:
python pipeline.py --parse-only

# Specify base directory:
python pipeline.py --base-dir /path/to/berria
"""

import argparse
from pathlib import Path
import datetime
import time
import sys

# Import your existing modules
import berria_downloader
import ixaml_parser


def run_pipeline(base_dir: Path, download=True, parse=True):
    if download:
        print("Starting download...")
        start_date, end_date = berria_downloader.get_start_and_end_dates(base_dir)
        current_date = start_date
        base_url = "https://www.berria.eus/placeholder"  # Replace with actual URL for Berria XML files

        while current_date <= end_date:
            berria_downloader.download_for_date(current_date, base_url, base_dir)
            # Be polite with Berria servers, it won't take that long :)
            time.sleep(1)
            current_date += datetime.timedelta(days=1)

    if parse:
        print("Starting parsing...")
        year_folders, last_date = ixaml_parser.find_year_folders_and_last_date(base_dir)
        if last_date is None:
            print("No XML files found to parse. Exiting.")
            return
        

        # Output filename: berria_DD_MM_YYYY.jsonl
        formatted_date = last_date.strftime("%d_%m_%Y")
        output_filename = f"berria_{formatted_date}.jsonl"
        ixaml_parser.parse_folders_to_jsonl(year_folders, output_filename)
        print(f"Parsing completed. Output file: {output_filename}")

def main():
    parser = argparse.ArgumentParser(description="Berria XML Downloader and Parser Pipeline")
    # Default base directory is current directory
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).parent, help="Base directory for Berria XML files")
    parser.add_argument("--download-only", action="store_true", help="Only download XML files")
    parser.add_argument("--parse-only", action="store_true", help="Only parse XML files to JSONL")
    args = parser.parse_args()

    base_dir = args.base_dir

    if args.download_only and args.parse_only:
        print("Cannot use --download-only and --parse-only together.")
        sys.exit(1)
    
    download, parse = not args.parse_only, not args.download_only

    run_pipeline(base_dir, download=download, parse=parse)

if __name__ == "__main__":
    main()