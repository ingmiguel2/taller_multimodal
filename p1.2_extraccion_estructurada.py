"""
Taller multimodal - Extracción estructurada desde imágenes.

Dominio elegido: etiquetas de productos alimenticios.
Pasos:
  1. Esquema con 5 campos útiles (Pydantic).
  2. El modelo extrae los campos de 3 imágenes, con salida JSON.
  3. El JSON se valida en el código: si no cumple el esquema, se informa (no se cae).
  4. Se compara campo por campo con el valor real y se reporta el % de aciertos.
"""
import base64
import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ValidationError

from utils.load_model import cargar_llm

load_dotenv()

CARPETA_IMAGENES = Path(__file__).parent / "imagenes"
NUM_IMAGENES = 3


# ---------------------------------------------------------------------------
# 1. ESQUEMA (6 campos). Todos opcionales: si no se ven, el modelo pone null.
# ---------------------------------------------------------------------------
class EtiquetaProducto(BaseModel):
    calorias_por_porcion: Optional[float] = None
    carbohidratos_totales_g: Optional[float] = None
    proteinas_g: Optional[float] = None
    azucares_totales_g: Optional[float] = None
    sodio_mg: Optional[float] = None


CAMPOS = list(EtiquetaProducto.model_fields.keys())


# ---------------------------------------------------------------------------
# VALORES REALES (lo que TÚ lees en cada imagen). Llave = nombre del archivo.
# Usa None si el dato no aparece en la imagen.
# Si una imagen no está aquí, el script te pedirá los valores por consola.
# ---------------------------------------------------------------------------
# OJO: cambia las llaves por los nombres reales de tus archivos.
# Todos los valores son de la columna "Por porción".
VALORES_REALES = {
    "imagen_3.png": {
        "calorias_por_porcion": 155,
        "carbohidratos_totales_g": 33,
        "proteinas_g": 3.6,
        "azucares_totales_g": 21,
        "sodio_mg": 139,
    },
    "imagen_4.png": {
        "calorias_por_porcion": 98,
        "carbohidratos_totales_g": 17,
        "proteinas_g": 3.5,   # VERIFICA: en la foto se ve borroso
        "azucares_totales_g": 0,
        "sodio_mg": 0,
    },
    "imagen_5.png": {
        "calorias_por_porcion": 17,
        "carbohidratos_totales_g": 4.1,
        "proteinas_g": 0.2,   # VERIFICA: en la foto se ve borroso
        "azucares_totales_g": 3.9,
        "sodio_mg": 119,
    }
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
PROMPT = f"""Eres un sistema de extracción de datos. Analiza la imagen y extrae
SOLO estos campos: {", ".join(CAMPOS)}.

Reglas:
- La imagen es la tabla de información nutricional de un producto.
- Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional ni markdown.
- Si un campo no es visible o no se puede leer, usa null.
- Usa siempre los valores de la columna "Por porción" (no los de "Por 100 g/mL").
- Todos los campos son números sin unidades (ej. 21, no "21 g").

Formato exacto:
{{
  "calorias_por_porcion": 0,
  "carbohidratos_totales_g": 0,
  "proteinas_g": 0,
  "azucares_totales_g": 0,
  "sodio_mg": 0
}}"""


def contenido_a_texto(content) -> str:
    """response.content puede ser str o lista de bloques."""
    if isinstance(content, str):
        return content
    partes = []
    for bloque in content:
        if isinstance(bloque, dict):
            partes.append(bloque.get("text", ""))
        else:
            partes.append(str(bloque))
    return "".join(partes)


def extraer_json(texto: str) -> str:
    """Quita <think>, fences ``` y devuelve el primer objeto {...}."""
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    texto = texto.replace("```json", "").replace("```", "").strip()
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1:
        return texto
    return texto[inicio : fin + 1]


def normalizar(valor):
    """Normaliza para comparar: minúsculas, sin tildes, sin espacios extra."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    s = unicodedata.normalize("NFD", str(valor))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s).strip().lower()
    try:
        return float(s)
    except ValueError:
        return s


def pedir_valores_reales(nombre_archivo: str) -> dict:
    print(f"\nEscribe los valores REALES de {nombre_archivo} (Enter = no aparece / null):")
    reales = {}
    for campo in CAMPOS:
        v = input(f"  {campo}: ").strip()
        reales[campo] = v if v else None
    return reales


def extraer_de_imagen(llm, ruta: Path):
    """Devuelve (EtiquetaProducto | None, texto_crudo, error | None)."""
    img_b64 = base64.b64encode(ruta.read_bytes()).decode("utf-8")
    mime = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"

    mensaje = HumanMessage(content=[
        {"type": "text", "text": PROMPT},
        {"type": "image", "base64": img_b64, "mime_type": mime},
    ])

    respuesta = llm.invoke([mensaje])
    crudo = contenido_a_texto(respuesta.content)

    # --- 3. Validación: informar en lugar de fallar ---
    try:
        datos = json.loads(extraer_json(crudo))
        return EtiquetaProducto(**datos), crudo, None
    except json.JSONDecodeError as e:
        return None, crudo, f"JSON inválido: {e}"
    except (ValidationError, TypeError) as e:
        return None, crudo, f"No cumple el esquema: {e}"


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def elegir_imagenes(imagenes: list) -> list:
    """Muestra la lista numerada y deja escoger una o varias imágenes."""
    print("\nImágenes disponibles:")
    for i, img in enumerate(imagenes, start=1):
        print(f"  {i}. {img.name}")

    while True:
        entrada = input(
            f"\nNúmero(s) de la(s) imagen(es) a evaluar, separados por coma "
            f"(ej. 3,4,5; se recomiendan {NUM_IMAGENES}): "
        )
        try:
            numeros = [int(n) for n in re.split(r"[,\s]+", entrada.strip()) if n]
            if not numeros:
                raise ValueError("No escribiste ningún número.")
            fuera = [n for n in numeros if not 1 <= n <= len(imagenes)]
            if fuera:
                raise ValueError(f"Fuera de rango (1-{len(imagenes)}): {fuera}")
            # sin repetidos, conservando el orden
            numeros = list(dict.fromkeys(numeros))
            return [imagenes[n - 1] for n in numeros]
        except ValueError as e:
            print(f"Entrada inválida: {e}")


def main():
    imagenes = sorted(
        list(CARPETA_IMAGENES.glob("*.png"))
        + list(CARPETA_IMAGENES.glob("*.jpg"))
        + list(CARPETA_IMAGENES.glob("*.jpeg"))
    )
    if not imagenes:
        raise FileNotFoundError(f"No hay imágenes en {CARPETA_IMAGENES}")
    imagenes = elegir_imagenes(imagenes)
    if len(imagenes) != NUM_IMAGENES:
        print(f"Aviso: elegiste {len(imagenes)} imagen(es); el taller pide {NUM_IMAGENES}.")

    llm = cargar_llm(model_name="qwen/qwen3.8-27b", max_tokens=4096, reasoning_effort="low")

    total_campos = 0
    total_aciertos = 0
    resumen = []

    for ruta in imagenes:
        print("\n" + "=" * 60)
        print(f"Imagen: {ruta.name}")
        print("=" * 60)

        extraido, crudo, error = extraer_de_imagen(llm, ruta)

        if error:
            print(f"[VALIDACIÓN FALLIDA] {error}")
            print("Respuesta cruda del modelo:\n", crudo)
            extraido_dict = {c: None for c in CAMPOS}
        else:
            extraido_dict = extraido.model_dump()
            print("[VALIDACIÓN OK] JSON extraído:")
            print(json.dumps(extraido_dict, indent=2, ensure_ascii=False))

        reales = VALORES_REALES.get(ruta.name) or pedir_valores_reales(ruta.name)

        # --- 4. Comparación campo por campo ---
        print(f"\n{'Campo':<24}{'Extraído':<28}{'Real':<28}Resultado")
        print("-" * 90)
        aciertos = 0
        for campo in CAMPOS:
            ext, real = extraido_dict.get(campo), reales.get(campo)
            ok = normalizar(ext) == normalizar(real)
            aciertos += ok
            print(f"{campo:<24}{str(ext):<28}{str(real):<28}{'✔' if ok else '✘'}")

        pct = aciertos / len(CAMPOS) * 100
        print(f"\nAciertos en {ruta.name}: {aciertos}/{len(CAMPOS)} ({pct:.1f}%)")

        total_campos += len(CAMPOS)
        total_aciertos += aciertos
        resumen.append((ruta.name, aciertos, len(CAMPOS), pct, error is None))

    # --- Reporte final ---
    print("\n" + "#" * 60)
    print("REPORTE FINAL")
    print("#" * 60)
    for nombre, a, t, p, valido in resumen:
        estado = "JSON válido" if valido else "JSON NO válido"
        print(f"{nombre:<30}{a}/{t}  {p:5.1f}%   ({estado})")
    print(f"\nPorcentaje global de aciertos: {total_aciertos}/{total_campos} "
          f"= {total_aciertos / total_campos * 100:.1f}%")


if __name__ == "__main__":
    main()