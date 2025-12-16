import gzip
import json
import os

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

def load_removals(removals_path, attribute_name):
    """
    Load duplicate character span removal instructions into a dict:
    { id: [(start, end), ...] }
    """
    removals = {}
    with gzip.open(removals_path, "rt", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            rid = obj.get("id")
            ranges = obj.get("attributes", {}).get(attribute_name, [])
            if ranges:
                removals[rid] = [(start, end) for start, end, _ in ranges]
    return removals


def filter_text(text, ranges):
    """
    Remove only leading/trailing duplicate spans by character index.
    Stop as soon as a non-duplicate region is reached.
    """
    if not ranges:
        return text

    length = len(text)
    ranges = sorted(ranges, key=lambda x: x[0])  # sort by start index

    # Trim from start
    start_idx = 0
    for (s, e) in ranges:
        if s == start_idx:
            start_idx = e  # extend trimming
        else:
            break  # stop at first non-leading duplicate

    # Trim from end
    end_idx = length
    for (s, e) in sorted(ranges, key=lambda x: -x[1]):  # sort by end descending
        if e == end_idx:
            end_idx = s  # shrink backward
        else:
            break  # stop at first non-trailing duplicate

    # Extract middle portion that survives
    return text[start_idx:end_idx].strip()


def process(input_path, attributes_path, attribute_name, output_path):
    removals = load_removals(attributes_path, attribute_name)

    with (
        gzip.open(input_path, "rt", encoding="utf-8") as rf,
        gzip.open(output_path, "wt", encoding="utf-8") as wf
    ):

        for line in rf:
            obj = json.loads(line)
            rid = obj.get("id")
            if rid in removals and "text" in obj:
                obj["text"] = filter_text(obj["text"], removals[rid])
            wf.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_jobs(jobs, workers=4):
    """ Run multiple (input, removals, output) jobs in parallel. """
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process, inp, rem, att, out): (inp, out) for inp, rem, att, out in jobs}
        for future in as_completed(futures):
            inp, out = futures[future]
            try:
                future.result()
                print(f"Finished: {inp} -> {out}")
            except Exception as e:
                print(f"Error processing {inp}: {e}")


if __name__ == "__main__":

    jobs = []
    for corpus in Path("/corpus/documents").rglob("*.jsonl.gz"):
        if '03_par-dedup' in corpus.name:
            continue
        documents_path = str(corpus)
        attributes_path = "/corpus/attributes/bff_duplicate_par/" + documents_path.split("/documents/")[-1]
        if "02_text-dedup" in documents_path:
            output_path = documents_path.replace("02_text-dedup", "03_par-dedup")
        else:
            output_path = documents_path.replace(".jsonl.gz", ".03_par-dedup.jsonl.gz")
        job = (documents_path, attributes_path, "bff_duplicate_par", output_path)
        if os.path.exists(output_path):
            continue
        jobs.append(job)
    run_jobs(jobs, workers=8)
