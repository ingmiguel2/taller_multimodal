"""Parte 2: audio -> transcripción (Whisper en Groq) -> respuesta del modelo.

2.1 Transcribe cada archivo listado en audios/metadatos.json.
2.2 Envía cada transcripción al modelo para que responda.

Genera resultados_parte2.md (tablas listas para copiar al informe) y
resultados_parte2.json. Si un audio falla, lo informa y sigue con el siguiente.

Variables de entorno (.env): GROQ_API_KEY
Opcionales: STT_MODEL (por defecto whisper-large-v3-turbo), LLM_MODEL_AUDIO (por defecto qwen/qwen3.8-27b)
"""
import json
import os
import re
import unicodedata
import wave
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent
CARPETA_AUDIOS = BASE / "audios"
METADATOS = CARPETA_AUDIOS / "metadatos.json"
SALIDA_MD = BASE / "resultados_parte2.md"
SALIDA_JSON = BASE / "resultados_parte2.json"

MODELO_STT = os.getenv("STT_MODEL", "whisper-large-v3-turbo")
MODELO_LLM = os.getenv("LLM_MODEL_AUDIO", "qwen/qwen3.8-27b")
MAX_BYTES = 25 * 1024 * 1024  # límite del plan gratuito de Groq
FORMATOS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".mp4", ".mpeg", ".mpga"}

SYSTEM_PROMPT = (
    "Eres un asistente experto en nutrición y en la lectura de etiquetas e información "
    "nutricional de alimentos empacados. Responde en español, de forma clara y breve "
    "(máximo 6 líneas). Si la pregunta es ambigua o la transcripción parece tener errores, "
    "dilo y responde con la interpretación más probable."
)


def duracion_segundos(ruta):
    """Duración en segundos para archivos WAV; None para otros formatos."""
    if ruta.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(ruta), "rb") as w:
            return w.getnframes() / w.getframerate()
    except (wave.Error, EOFError):
        return None


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", texto)


def tasa_error_palabras(referencia, hipotesis):
    """WER: (sustituciones + inserciones + borrados) / palabras de la referencia."""
    ref, hip = _normalizar(referencia), _normalizar(hipotesis)
    if not ref:
        return 0.0 if not hip else 1.0
    previa = list(range(len(hip) + 1))
    for i, r in enumerate(ref, start=1):
        actual = [i]
        for j, h in enumerate(hip, start=1):
            costo = 0 if r == h else 1
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + costo))
        previa = actual
    return previa[-1] / len(ref)


def celda(texto):
    """Escapa texto para una celda de tabla Markdown."""
    return str(texto).replace("|", "\\|").replace("\n", " ").strip()


def transcribir(cliente, ruta):
    """2.1 Transcripción desde archivo con Whisper."""
    with open(ruta, "rb") as f:
        resultado = cliente.audio.transcriptions.create(
            file=(ruta.name, f.read()),
            model=MODELO_STT,
            language="es",
            temperature=0,
        )
    return resultado.text.strip()


def responder(llm, transcripcion):
    """2.2 Respuesta del modelo a partir de la transcripción."""
    from langchain_core.messages import HumanMessage, SystemMessage

    respuesta = llm.invoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(transcripcion)])
    return respuesta.content.strip()


def main():
    from groq import Groq
    from utils.load_model import cargar_llm

    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("Falta la variable GROQ_API_KEY en el archivo .env")

    metadatos = json.loads(METADATOS.read_text(encoding="utf-8"))
    cliente = Groq()
    llm = cargar_llm(model_name=MODELO_LLM, max_tokens=4096, reasoning_effort="low")

    resultados = []
    for n, item in enumerate(metadatos, start=1):
        ruta = CARPETA_AUDIOS / item["archivo"]
        fila = {"n": n, **item, "duracion_s": None, "transcripcion": "", "wer": None,
                "respuesta": "", "error": ""}
        print(f"\n===== Audio {n}: {ruta.name} ({item['hablante']}, {item['condicion']}) =====")

        try:
            if not ruta.exists():
                raise FileNotFoundError(f"No existe {ruta}. Grábalo con grabar_audios.py")
            if ruta.suffix.lower() not in FORMATOS:
                raise ValueError(f"Formato no soportado: {ruta.suffix}")
            if ruta.stat().st_size > MAX_BYTES:
                raise ValueError("El archivo supera 25 MB (límite del plan gratuito de Groq)")

            dur = duracion_segundos(ruta)
            fila["duracion_s"] = round(dur, 1) if dur is not None else None
            if dur is not None and not 10 <= dur <= 30:
                print(f"AVISO: dura {dur:.1f} s y el taller pide entre 10 y 30 s")

            print(f"Lo que se dijo : {item['dijo']}")
            fila["transcripcion"] = transcribir(cliente, ruta)
            fila["wer"] = round(tasa_error_palabras(item["dijo"], fila["transcripcion"]), 3)
            print(f"Transcripción  : {fila['transcripcion']}")
            print(f"Error de palabras (WER): {fila['wer']:.1%}")

            fila["respuesta"] = responder(llm, fila["transcripcion"])
            print(f"Respuesta del modelo:\n{fila['respuesta']}")
        except Exception as e:  # informa y continúa con el siguiente audio
            fila["error"] = f"{type(e).__name__}: {e}"
            print(f"ERROR en {ruta.name}: {fila['error']}")

        resultados.append(fila)

    SALIDA_JSON.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# Resultados Parte 2", "", f"Modelo de audio: `{MODELO_STT}` · Modelo de respuesta: `{MODELO_LLM}`", "",
          "## 2.1 Transcripción desde archivo", "",
          "| Audio | Hablante | Condición | Duración (s) | Lo que se dijo | Transcripción | WER |",
          "|---|---|---|---|---|---|---|"]
    for r in resultados:
        trans = r["transcripcion"] or f"ERROR: {r['error']}"
        wer = f"{r['wer']:.1%}" if r["wer"] is not None else "-"
        md.append(f"| {celda(r['archivo'])} | {celda(r['hablante'])} | {celda(r['condicion'])} | "
                  f"{r['duracion_s'] if r['duracion_s'] is not None else 'N/D'} | {celda(r['dijo'])} | "
                  f"{celda(trans)} | {wer} |")
    md += ["", "## 2.2 Respuesta del modelo a partir de la transcripción", "",
           "| Audio | Transcripción enviada al modelo | Respuesta del modelo |", "|---|---|---|"]
    for r in resultados:
        md.append(f"| {celda(r['archivo'])} | {celda(r['transcripcion'])} | {celda(r['respuesta'] or r['error'])} |")
    SALIDA_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nListo. Resultados en {SALIDA_MD.name} y {SALIDA_JSON.name}")


if __name__ == "__main__":
    main()
