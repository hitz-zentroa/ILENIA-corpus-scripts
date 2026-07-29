
import argparse
import json
import re
import sys
from collections import Counter

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable


# Orden importante: de patrones mas especificos/rigidos a mas laxos,
# para evitar que un patron generico "engulla" partes de otro identificador.
# La clave interna (DNI, NIE, CIF...) se usa para el contador; la etiqueta
# visible en el texto depende del idioma elegido (ver LABELS mas abajo).
PATTERNS = [
    ("IBAN",       re.compile(r'\bES\d{2}[\s]?(?:\d{4}[\s]?){5}\b')),
    # ("MATRICULA",  re.compile(r'\b\d{4}[\s-]?[BCDFGHJKLMNPRSTVWXYZ]{3}\b')),
    ("NIE",        re.compile(r'\b[XYZxyz][\s-]?\d{7}[\s-]?[A-Za-z]\b')),
    ("DNI",        re.compile(r'\b\d{8}[\s-]?[A-Za-z]\b')),
    ("CIF",        re.compile(r'\b[A-HJNPQSUVW]\d{7}[A-J0-9]\b')),
    ("SS",         re.compile(r'\b\d{2}/\d{8}/\d{2}\b')),
    ("EMAIL",      re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')),
    # ("TELEFONO",   re.compile(r'\b(?:(?:\+34|0034)[ -]?)?[6789]\d{8}\b|\b(?:(?:\+34|0034)[ -]?)?[6789]\d{2}[ -]\d{3}[ -]\d{3}\b')),
]

# Etiquetas de placeholder segun idioma. La clave interna del contador
# siempre es en castellano (para mantener consistencia en las estadisticas);
# solo cambia lo que se inserta en el texto.
LABELS = {
    "es": {
        "IBAN": "IBAN",
        "MATRICULA": "MATRICULA",
        "NIE": "NIE",
        "DNI": "DNI",
        "CIF": "CIF",
        "SS": "SEG_SOCIAL",
        "TELEFONO": "TELEFONO",
        "EMAIL": "EMAIL",
    },
    "eu": {
        "IBAN": "IBAN",
        "MATRICULA": "MATRIKULA",
        "NIE": "AIZ",          # Atzerritarren Identifikazio Zenbakia
        "DNI": "NAN",          # Nortasun Agiri Nazionala
        "CIF": "IFK",          # Identifikazio Fiskal Kodea
        "SS": "GIZ_SEG",       # Gizarte Segurantza
        "TELEFONO": "TELEFONOA",
        "EMAIL": "E-POSTA"
    },
}


def anonimizar_texto(texto: str, contador: Counter, labels: dict) -> str:
    """Sustituye cada identificador detectado por un placeholder (segun idioma) y actualiza el contador global."""
    if not texto:
        return texto

    for etiqueta_interna, patron in PATTERNS:
        placeholder = labels[etiqueta_interna]

        def _reemplazo(match, etiqueta_interna=etiqueta_interna, placeholder=placeholder):
            contador[etiqueta_interna] += 1
            return f"<{placeholder}>"

        texto = patron.sub(_reemplazo, texto)

    return texto


def contar_lineas(path: str) -> int:
    """Cuenta lineas rapido para dimensionar la barra de progreso, sin cargar todo en memoria."""
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def procesar(input_path: str, output_path: str, campo: str, lang: str) -> Counter:
    labels = LABELS[lang]
    total_lineas = contar_lineas(input_path)
    contador_global = Counter()
    lineas_ok = 0
    lineas_sin_campo = 0
    lineas_error_json = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:

        for linea in tqdm(fin, total=total_lineas, desc="Anonimizando", unit="linea"):
            linea = linea.strip()
            if not linea:
                continue

            try:
                registro = json.loads(linea)
            except json.JSONDecodeError:
                lineas_error_json += 1
                fout.write(linea + "\\n")
                continue

            if campo not in registro or not isinstance(registro[campo], str):
                lineas_sin_campo += 1
                fout.write(json.dumps(registro, ensure_ascii=False) + "\\n")
                continue

            registro[campo] = anonimizar_texto(registro[campo], contador_global, labels)
            fout.write(json.dumps(registro, ensure_ascii=False) + "\n")
            lineas_ok += 1

    print("\\n--- Resumen del proceso ---")
    print(f"Idioma placeholders     : {lang}")
    print(f"Lineas totales leidas   : {total_lineas}")
    print(f"Lineas procesadas OK    : {lineas_ok}")
    print(f"Lineas sin el campo     : {lineas_sin_campo}")
    print(f"Lineas con error JSON   : {lineas_error_json}")
    print("\\n--- Identificadores anonimizados por tipo ---")
    if contador_global:
        for etiqueta, cantidad in contador_global.most_common():
            print(f"{etiqueta:<10}: {cantidad}")
        print(f"{'TOTAL':<10}: {sum(contador_global.values())}")
    else:
        print("No se ha detectado ningun identificador.")

    return contador_global


def main():
    parser = argparse.ArgumentParser(
        description="Anonimiza identificadores personales directos (DNI, NIE, CIF, SS, telefono, IBAN, matricula) en un campo de texto de un JSONL."
    )
    parser.add_argument("--input", required=True, help="Ruta al JSONL de entrada")
    parser.add_argument("--output", required=True, help="Ruta al JSONL de salida")
    parser.add_argument("--field", required=True, help="Nombre del campo de texto a anonimizar")
    parser.add_argument("--lang", choices=["es", "eu"], default="es",
                         help="Idioma de los placeholders: es (castellano) o eu (euskera). Por defecto: es")
    args = parser.parse_args()

    procesar(args.input, args.output, args.field, args.lang)


if __name__ == "__main__":
    main()
