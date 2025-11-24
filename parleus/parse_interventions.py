import argparse
from collections import defaultdict
import json
import re

def main(root_path: str):
    for i in range(10, 13):
        print(f"Parsing interventions for legislatura {i}")
        parse_interventions(i, root_path)

def parse_interventions(legislatura, root_path="parse_pdf"):
    
    # leemos el fichero json de output
    fname_output = f"{root_path}/legislatura_{legislatura}/json_output_{legislatura}.json"
    fname_alderdiak = f"{root_path}/legislatura_{legislatura}/alderdiak_{legislatura}.json"
    
    output_path = f"{root_path}/legislatura_{legislatura}/json_intervenciones_{legislatura}.json"

    with open(fname_output, "r", encoding='utf-8') as f:
        json_output = json.load(f)

    with open(fname_alderdiak, "r") as f:
        json_alderdiak = json.load(f)
    
    print(len(json_output))
    no_speakers = set()
    # lista para guardar los jsons de salida
    json_outputs = []
    # recorremos el json de output
    for i, json_input in enumerate(json_output):
        # printear cada 20 ids
            
        legislatura = json_input["legislatura"]
        id = json_input["num_sesion"]
        fecha = json_input["fecha"]
        url = json_input["url"]
        texto_original = json_input["original"]
        texto_traducido = json_input["traduccion"]


        # Expresión regular para encontrar los nombres y su intervención
        pattern = r'([A-ZÁÉÍÓÚÑÜÖ\s\-]{10,}.{0,30}?(:|\)\.))'

        #text = "ABC algo: texto1 XYZ más cosas: texto2 OTRO más: texto3"

        # parsear TEXTO ORIGINAL
        matches = list(re.finditer(pattern, texto_original))

        results_original = []
        intervenciones_original = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(texto_original)
            speaker_full = match.group(1)
            speaker = " ".join(re.findall(r'\b[A-ZÁÉÍÓÚÜÖÑ]+(?:\s+[A-ZÁÉÍÓÚÜÖÑ]+)*\b', speaker_full))
            derecha = texto_original[start:end].strip()
            if speaker in json_alderdiak:
                party = json_alderdiak[speaker]
            else:
                party = ""
                # comprobar si algun key del json de alderdiak esta en el speaker
                for key in json_alderdiak.keys():
                    if key in speaker:
                        party = json_alderdiak[key]
                        speaker = key
                        #print("encontrado key en speaker:", key)
                        break
                if "(" in speaker_full:
                    resultado = re.findall(r'\((.*?)\)', speaker_full)

                    if resultado:
                        nombre = resultado[0]
                        en_mayusculas = nombre.upper()
                        if en_mayusculas in json_alderdiak:
                            # obtener el partido del json
                            party = json_alderdiak[en_mayusculas]
                            speaker = f"{speaker} ({en_mayusculas})"
                        else:
                            speaker = f"{speaker} ({nombre})"
                            no_speakers.add(speaker_full)
            results_original.append((speaker, party, derecha))
            intervencion = {
                "speaker": speaker,
                "party": party,
                "text": derecha
            }
            # añadir la intervencion a la lista
            intervenciones_original.append(intervencion)
            

        # parsear TEXTO TRADUCIDO
        matches = list(re.finditer(pattern, texto_traducido))

        results_traducido = []
        intervenciones_traducido = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(texto_traducido)
            speaker_full = match.group(1)
            # coger solo la parte en mayusculas del speaker aun que haya mas texto
            speaker = " ".join(re.findall(r'\b[A-ZÁÉÍÓÚÜÖÑ]+(?:\s+[A-ZÁÉÍÓÚÜÖÑ]+)*\b', speaker_full))
            derecha = texto_traducido[start:end].strip()
            # si el speaker esta en el json de alderdiak, le añadimos el partido
            if speaker in json_alderdiak:
                party = json_alderdiak[speaker]
            else:
                party = ""
                # comprobar si algun key del json de alderdiak esta en el speaker
                for key in json_alderdiak.keys():
                    if key in speaker:
                        party = json_alderdiak[key]
                        speaker = key
                        #print("encontrado key en speaker:", key)
                        break
                if "(" in speaker_full:
                    resultado = re.findall(r'\((.*?)\)', speaker_full)

                    if resultado:
                        nombre = resultado[0]
                        en_mayusculas = nombre.upper()
                        if en_mayusculas in json_alderdiak:
                            # obtener el partido del json
                            party = json_alderdiak[en_mayusculas]
                            speaker = f"{speaker} ({en_mayusculas})"
                        else:
                            speaker = f"{speaker} ({nombre})"
                            no_speakers.add(speaker_full)
            results_traducido.append((speaker, party, derecha))
            intervencion = {
                "speaker": speaker,
                "party": party,
                "text": derecha
            }
            # añadir la intervencion a la lista
            intervenciones_traducido.append(intervencion)
            
            
        # comprobar si estan alineados los speakers de cada resultado
        if len(results_original) != len(results_traducido):
            print(f"Error: el numero de speakers no coincide en la sesion {id} del dia {fecha}")
            print(f"Original: {len(results_original)} - Traducido: {len(results_traducido)}")
        for i, (orig, trad) in enumerate(zip(results_original, results_traducido)):
            # comprobar si los speakers coinciden o no
            speaker_orig = orig[0]
            speaker_trad = trad[0]
            
            if (speaker_orig in json_alderdiak and speaker_trad not in json_alderdiak) or (speaker_orig not in json_alderdiak and speaker_trad in json_alderdiak):
                if len(speaker_orig.split()) > len(speaker_trad.split()):
                    # acortar el nombre del speaker original quitando la pirmera palabra
                    speaker_orig = " ".join(speaker_orig.split()[1:])
                # si al final tiene 1 o 2 letras mas el original, le quitamos esas letras
                if len(speaker_orig) == len(speaker_trad) + 1:
                    speaker_orig = speaker_orig[:-1]
                    intervenciones_original[i]["speaker"] = speaker_orig
                if len(speaker_orig) == len(speaker_trad) + 2:
                    speaker_orig = speaker_orig[:-2]
                    print(intervenciones_original[i]["speaker"])
                    intervenciones_original[i]["speaker"] = speaker_orig
                    print(intervenciones_original[i]["speaker"])
                
                if (speaker_orig in speaker_trad) or (speaker_trad in speaker_orig):
                    continue
                if (speaker_orig in json_alderdiak and speaker_trad not in json_alderdiak) or (speaker_orig not in json_alderdiak and speaker_trad in json_alderdiak) or (speaker_orig != speaker_trad): 
                    print(f"Error: los speakers no coinciden en la sesion {id} del dia {fecha}, en la intervencion {i}/{len(results_original)}")
                    print(f"{speaker_orig} | {speaker_trad}")
                    print()
                    
                    # cortar las listas hasta el índice anterior (i-1)
                    intervenciones_original = intervenciones_original[:i]
                    intervenciones_traducido = intervenciones_traducido[:i]
                    break
            
            
        if len(intervenciones_original) != len(intervenciones_traducido):
            print("NO SE HA ARREGLADO EL ERROR")
        
        # guardar en un json la info con las dos columnas
        final_json = {
                "legislatura": legislatura,
                "num_sesion": id,
                "fecha": fecha,
                "url": json_input["url"],
                "intervenciones_original": intervenciones_original,
                "intervenciones_traducido": intervenciones_traducido
            }
        # añadir el json a la lista
        json_outputs.append(final_json)
               
    print(no_speakers)

    # Guardamos el JSON en un fichero
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(json_outputs, f, ensure_ascii=False, indent=4)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse interventions from parliamentary sessions")
    parser.add_argument("--root_path", type=str, help="Root path to parse interventions for")
    args = parser.parse_args()
    main(args.root_path)