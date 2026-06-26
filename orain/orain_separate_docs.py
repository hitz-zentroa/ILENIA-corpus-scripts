import json
from pathlib import Path

def separar_docs_por_idioma(input_file: Path, output_dir: Path):
    """
    Lee el archivo JSON scrapeado, filtra solo los artículos en euskera ('eu')
    con contenido válido, y los guarda en un archivo JSONL final.
    """
    # Create the final output filename in the correct directory
    output_filename = input_file.name.replace(".json", "_eu.jsonl")
    output_filepath = output_dir / output_filename

    # Abrir el archivo de salida en modo escritura
    with open(output_filepath, "w", encoding="utf-8") as out_f, \
         open(input_file, "r", encoding="utf-8") as in_f:
        
        data = json.load(in_f)

        # Procesar cada artículo, enfocándonos solo en 'eu'
        for item in data:
            doc_id = item.get("id")
            lang = "eu"
            contenido = item.get(lang)
            
            # Solo si hay contenido en euskera y el texto no está vacío (> 10 palabras)
            if contenido and contenido.get("texto") and len(contenido.get("texto").split()) > 10:
                fecha_pub = contenido.get("fecha_publicacion")
                fecha_act = contenido.get("fecha_actualizacion")

                if fecha_pub:
                    fecha_pub = fecha_pub.split("T")[0]
                if fecha_act:
                    fecha_act = fecha_act.split("T")[0]

                doc = {
                    "unique_id": f"orain_{doc_id}_{lang}",
                    "idioma": lang,
                    **contenido,
                    "fecha_publicacion": fecha_pub,
                    "fecha_actualizacion": fecha_act,
                }
                
                # Escribir línea JSON en el archivo
                out_f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"✅ Archivo JSONL (euskera) generado: {output_filepath}")
    
    return output_filepath
