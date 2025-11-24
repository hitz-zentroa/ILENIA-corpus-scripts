import argparse
import json
import re
from nltk.tokenize import sent_tokenize

import fasttext


def detect_language(text):
    """
    Detect the language of the given text using FastText.
    """
    # Predict the language
    predictions = model.predict(text, k=1)
    
    # Get the predicted language code
    lang_code = predictions[0][0].split("__")[-1]
    if lang_code not in ["es", "eu"]:
        # If the language is not Spanish or Basque, return "es"
        #print(f"NO LANGUAGE DETECTED ({lang_code}): {text}")
        lang_code = "eu"
    
    return lang_code

def main(root_path: str):
    for i in range(10, 13):
        print(f"Dividing languages for legislatura {i}")
        divide_languages(i, root_path)

def divide_languages(legislature, root_path="parse_pdf"):
    
    # leemos el fichero json de output
    fname_input = f"{root_path}/legislatura_{legislature}/json_intervenciones_{legislature}.json"
    
    # leer el fichero de entrada
    with open(fname_input, "r", encoding='utf-8') as f:
        data = json.load(f)
        
    
    diferencias = []
    articulos = 0
    # recorremos el json de input
    lista_euskera = []
    lista_castellano = []
    topic_eu_num = 0
    topic_es_num = 0

    for i, json_input in enumerate(data):
        # printear cada 20 ids
        if i % 50 == 0:
            print("ID SESION: ", json_input["num_sesion"])
        
        # extraer la info
        legislatura = json_input["legislatura"]
        id = json_input["num_sesion"]
        fecha = json_input["fecha"]
        intervenciones_original = json_input["intervenciones_original"]
        intervenciones_traducido = json_input["intervenciones_traducido"]
        url = json_input["url"]
        
        topic_eu = ""
        topic_es = ""

        
        if len(intervenciones_original) != len(intervenciones_traducido):
            print(f"ERROR: Diferente número de intervenciones en la sesión {id} ({len(intervenciones_original)} vs {len(intervenciones_traducido)})")
        

        # recorremos las dos listas de intervenciones a la vez
        for intervencion_original, intervencion_traducido in zip(intervenciones_original, intervenciones_traducido):
            # extraer el texto original y traducido
            speaker_original = intervencion_original["speaker"]
            speaker_traducido = intervencion_traducido["speaker"]
            
            texto_original = intervencion_original["text"]
            texto_traducido = intervencion_traducido["text"]

            party_original = intervencion_original["party"]
            party_traducido = intervencion_traducido["party"]

            
            # tokenizar cada texto
            frases_original = sent_tokenize(texto_original)
            frases_traducido = sent_tokenize(texto_traducido)
            
            diferencia = abs(len(frases_original) - len(frases_traducido))
            if "el" in frases_traducido[-1].lower().split() or "la" in frases_traducido[-1].lower().split():
                articulos +=1
            
            if speaker_original == "LEHENDAKARIAK" or speaker_original == "LEHENDAKARIA" or speaker_original == "LEHENDAKARIAK (TEJERIA OTERMIN)" or speaker_original == "LEHENDAKARIAK (TEJERIA ORTERMIN)" or speaker_original == "LEHENDAKARIAK (OTERMIN TEJERIA)":
                # intentar obtener el tema de la intervención
                coincidencia = re.search(r'Gai-zerrendako.*?puntu.*?:\s+"(.*?)"', texto_original)
                if coincidencia:
                    topic_eu = coincidencia.group(1)
                    topic_eu_num += 1
                    topic_es = ""
                coincidencia = re.search(r'orden del día:\s+\"(.*?)\"', texto_traducido)
                if coincidencia:
                    topic_es = coincidencia.group(1)
                    topic_es_num += 1
                    
                continue
            
            # comprobar que el número de frases es el mismo
            
            if len(frases_original) != len(frases_traducido):
                # Si la diferencia es solo de 1, eliminamos la última del más largo
                if abs(len(frases_original) - len(frases_traducido)) == 1:
                    if len(frases_original) > len(frases_traducido):
                        #print("→ Cortando la última frase del original")
                        frases_original = frases_original[:-1]
                        diferencia = 0
                    else:
                        #print("→ Cortando la última frase del traducido")
                        frases_traducido = frases_traducido[:-1]
                        diferencia = 0

                
            
            # si la diferencia es mayor a 2, comprobamos si el porcentaje del idioma es mayor al 80%
            if diferencia >= 2:
                num_euskera = 0
                num_castellano = 0
                # recorrer las frases del texto original
                for frase_original in frases_original:
                    # extraer el idioma del texto original
                    idioma_texto_original = detect_language(frase_original)
                    
                    if idioma_texto_original == "eu":
                        num_euskera += 1
                    elif idioma_texto_original == "es":
                        num_castellano += 1
                    else:
                        print(f"NO LANGUAGE DETECTED ({idioma_texto_original}): defaulting to Basque.")
                        num_castellano += 1

                # comprobar si el porcentaje de euskera es mayor al 60%
                if num_euskera / len(frases_original) > 0.6:
                    # si es mayor al 60%, lo consideramos euskera
                    # lo añadimos a la lista del euskera el original y el traducido a español
                    #print(f"→ Euskera detectado: \n {texto_original}")
                    lista_euskera.append({
                        "legislatura": legislatura,
                        "id": id,
                        "fecha": fecha,
                        "speaker": speaker_original,
                        "party": party_original,
                        "topic": topic_eu,
                        "text": texto_original,
                        "language": "eu",
                        "url": url
                    })

                    lista_castellano.append({
                        "legislatura": legislatura,
                        "id": id,
                        "fecha": fecha,
                        "speaker": speaker_traducido,
                        "party": party_traducido,
                        "topic": topic_es,
                        "text": texto_traducido,
                        "language": "es",
                        "url": url
                    })
                elif num_castellano / len(frases_original) > 0.6:
                    #print(f"→ Castellano detectado:\n {texto_original}")
                    # si es mayor al 80%, lo consideramos castellano
                    lista_euskera.append({
                        "legislatura": legislatura,
                        "id": id,
                        "fecha": fecha,
                        "speaker": speaker_original,
                        "party": party_original,
                        "topic": topic_eu,
                        "text": texto_traducido,
                        "language": "eu",
                        "url": url
                    })

                    lista_castellano.append({
                        "legislatura": legislatura,
                        "id": id,
                        "fecha": fecha,
                        "speaker": speaker_traducido,
                        "party": party_traducido,
                        "topic": topic_es,
                        "text": texto_original,
                        "language": "es",
                        "url": url
                    })
                

            if diferencia == 0:
                # recorrer las frases a la vez
                frases_eu = []
                frases_es = []
                for frase_original, frase_traducido in zip(frases_original, frases_traducido):
                    # extraer el idioma del texto original
                    idioma_texto_original = detect_language(frase_original)
                    
                    if idioma_texto_original == "eu":
                        frases_eu.append(frase_original)
                        frases_es.append(frase_traducido)
                    elif idioma_texto_original == "es":
                        frases_es.append(frase_original)
                        frases_eu.append(frase_traducido)
                    else:
                        print(f"NO LANGUAGE DETECTED ({idioma_texto_original}): defaulting to Basque.")
                        frases_es.append(frase_original)
                        frases_eu.append(frase_traducido)
                
                # añadimos a la lista
                lista_euskera.append({
                    "legislatura": legislatura,
                    "id": id,
                    "fecha": fecha,
                    "speaker": speaker_original,
                    "party": party_original,
                    "topic": topic_eu,
                    "text": " ".join(frases_eu),
                    "language": "eu",
                    "url": url
                })
                lista_castellano.append({
                    "legislatura": legislatura,
                    "id": id,
                    "fecha": fecha,
                    "speaker": speaker_traducido,
                    "party": party_traducido,
                    "topic": topic_es,
                    "text": " ".join(frases_es),
                    "language": "es",
                    "url": url
                })
            
        
    
    print(len(lista_euskera))
    print(len(lista_castellano))
    print(topic_eu_num)
    print(topic_es_num)

    # guardar en dos ficheros json
    with open(f"{root_path}/parlamentu_{legislature}_eu.json", "w", encoding='utf-8') as f:
        json.dump(lista_euskera, f, ensure_ascii=False, indent=4)
    with open(f"{root_path}/parlamentu_{legislature}_es.json", "w", encoding='utf-8') as f:
        json.dump(lista_castellano, f, ensure_ascii=False, indent=4)
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Divide interventions by language")
    parser.add_argument("--root_path", type=str, help="Root path to divide languages for")
    parser.add_argument("--model_path", type=str, help="Path to the language detection model")
    args = parser.parse_args()
    model = fasttext.load_model(args.model_path)
    main(args.root_path)