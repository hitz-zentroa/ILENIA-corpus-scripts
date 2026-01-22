import json 
import argparse


def main(path):

    metadata = []
    with open(path, 'r') as f_json:
        for line in f_json:
            metadata.append(json.loads(line))

    ultimo_organismo_visto = ""

    for item in metadata:
        # Obtenemos el organismo actual y limpiamos espacios en blanco por seguridad
        organismo_actual = item.get("organismo_emisor", "").strip()
        
        if organismo_actual:
            # Si tiene valor, actualizamos nuestra "memoria"
            ultimo_organismo_visto = organismo_actual
        else:
            # Si está vacío, le asignamos el último visto
            item["organismo_emisor"] = ultimo_organismo_visto
    
    # Guardar el JSONL corregido
    new_path = path.replace('.jsonl', '_corregido.jsonl')
    with open(new_path, 'w') as f_json:
        for item in metadata:
            f_json.write(json.dumps(item, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Corregir fichero JSONL del BOB")
    parser.add_argument('path', type=str, help='Fichero JSONL de entrada a corregir')
    args = parser.parse_args()
    main(args.path)