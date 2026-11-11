"""Graba los audios de la Parte 2 leyendo las frases de audios/metadatos.json.

Uso:
    python grabar_audios.py                 # graba los 4 audios (20 s cada uno)
    python grabar_audios.py --duracion 25   # cambia la duración
    python grabar_audios.py --solo 2 4      # vuelve a grabar solo el 2 y el 4

Para cada audio pide el nombre de quien habla y si hay ruido de fondo,
y deja esos datos guardados en metadatos.json.
"""
import argparse
import json
import time
from pathlib import Path

import sounddevice as sd
from scipy.io.wavfile import write
from tqdm import tqdm

CARPETA_AUDIOS = Path(__file__).parent / "audios"
METADATOS = CARPETA_AUDIOS / "metadatos.json"
SAMPLE_RATE = 16000  # Whisper trabaja a 16 kHz; reduce el tamaño del archivo


def grabar(duracion):
    audio = sd.rec(int(duracion * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    for _ in tqdm(range(duracion * 10), desc="Grabando"):
        time.sleep(0.1)
    sd.wait()
    return audio


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duracion", type=int, default=20, help="segundos por audio (10 a 30)")
    parser.add_argument("--solo", type=int, nargs="*", help="números de audio a (re)grabar, ej. 2 4")
    args = parser.parse_args()

    if not 10 <= args.duracion <= 30:
        raise ValueError("La duración debe estar entre 10 y 30 segundos.")

    metadatos = json.loads(METADATOS.read_text(encoding="utf-8"))

    for n, item in enumerate(metadatos, start=1):
        if args.solo and n not in args.solo:
            continue

        print(f"\n=== Audio {n} de {len(metadatos)} ({item['archivo']}) ===")
        print(f'Frase a leer en voz alta:\n  "{item["dijo"]}"')

        hablante = input(f"¿Quién habla? [{item['hablante']}]: ").strip() or item["hablante"]
        condicion = input(f"¿Con ruido o sin ruido? [{item['condicion']}]: ").strip().lower() or item["condicion"]
        if condicion == "con ruido":
            print("Pon ruido de fondo (TV, música, calle) antes de grabar.")

        while True:
            input("Presiona Enter y empieza a hablar...")
            audio = grabar(args.duracion)

            print("Reproduciendo...")
            sd.play(audio, samplerate=SAMPLE_RATE)
            sd.wait()

            if input("¿Se escucha bien? (s/n) [s]: ").strip().lower() != "n":
                break

        write(CARPETA_AUDIOS / item["archivo"], SAMPLE_RATE, audio)
        item["hablante"] = hablante
        item["condicion"] = condicion
        METADATOS.write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Guardado: audios/{item['archivo']}")


if __name__ == "__main__":
    main()
