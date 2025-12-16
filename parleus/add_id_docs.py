import argparse
import json


def process_multiple_json(lang: str, root_path: str):
    current_id = 1

    output_paths = []

    for i in range(10, 13):
        output_path = f"{root_path}/legislatura_{i}/parlamentu_{i}_{lang}_final.jsonl"
        output_paths.append(output_path)
        with open(output_path, 'w', encoding='utf-8') as out:
            input_path = f"{root_path}/legislatura_{i}/parlamentu_{i}_{lang}.json"
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item["unique_id"] = f"parl_{lang}_{current_id}"
                    out.write(json.dumps(item, ensure_ascii=False) + "\n")
                    current_id += 1

    output_file = f"{root_path}/parleus_{lang}.jsonl"

    # leer los 3 jsonl y juntarlos en uno
    with open(output_file, "w", encoding='utf-8') as outfile:
        for input_file in output_paths:
            with open(input_file, "r", encoding='utf-8') as infile:
                for line in infile:
                    # cargar el json
                    json_line = json.loads(line)
                    # escribir en el nuevo fichero
                    outfile.write(json.dumps(json_line, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add unique IDs to documents")
    parser.add_argument("--root_path", type=str, help="Root path to add IDs for")
    args = parser.parse_args()
    # Procesar los tres archivos por idioma
    process_multiple_json("es", args.root_path)
    process_multiple_json("eu", args.root_path)
