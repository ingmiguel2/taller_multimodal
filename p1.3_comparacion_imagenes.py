from pathlib import Path
from utils.load_model import cargar_llm
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import base64

load_dotenv()

CARPETA_IMAGENES = Path(__file__).parent / "imagenes"

imagenes = sorted(CARPETA_IMAGENES.glob("*.png"))
if not imagenes:
    raise FileNotFoundError(f"No hay imágenes .png en {CARPETA_IMAGENES}")

for i, imagen in enumerate(imagenes, start=1):
    print(f"{i}. {imagen.name}")

# El usuario escribe 2 o 3 números separados por coma, por ejemplo: 1,4
entrada = input("Números de las imágenes (2 o 3, ej. 1,4): ")
numeros = [int(n) for n in entrada.replace("(", "").replace(")", "").split(",")]

if not 2 <= len(numeros) <= 3:
    raise ValueError("Debes elegir 2 o 3 imágenes.")
if any(n < 1 or n > len(imagenes) for n in numeros):
    raise ValueError(f"Los números deben estar entre 1 y {len(imagenes)}.")

rutas = [imagenes[n - 1] for n in numeros]

# Un solo mensaje: primero la instrucción y luego cada imagen
# (con una etiqueta de texto para que el modelo sepa cuál es cuál).
comparar_preparacion = input(
    "¿Comparar también las formas de preparación? (s/n): "
).strip().lower() == "s"

instruccion = (
    "Cada imagen muestra el empaque de un producto alimenticio con su tabla de "
    "información nutricional. Compara los productos usando los valores de la columna "
    "'Por porción': calorías, carbohidratos totales, proteínas, azúcares totales y sodio. "
    "Si la tabla trae varias columnas (por ejemplo 'Por 100 g' o 'Por 100 mL' y 'Por porción'), "
    "usa SIEMPRE la columna correspondiente al tamaño de porción indicado, nunca la de "
    "100 g o 100 mL. Si un valor no se alcanza a leer, escribe 'no legible' en lugar de adivinar. "
    "Preséntalo en una tabla comparativa indicando el tamaño de porción de cada producto "
    "y aclara si es distinto entre los productos. "
)

if comparar_preparacion:
    instruccion += (
        "Además, compara las formas de preparación o de consumo que indique cada empaque; "
        "si alguno no las indica o no se alcanzan a leer, dilo. "
    )

instruccion += (
    "Termina con un resumen conjunto: qué producto aporta más energía, cuál tiene "
    "menos azúcar y cuál sería mejor opción según el objetivo nutricional."
)

contenido = [{"type": "text", "text": instruccion}]

for n, ruta in enumerate(rutas, start=1):
    imagen_bytes = ruta.read_bytes()

    # Now base64 encode
    img_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

    contenido.append({"type": "text", "text": f"Imagen {n} ({ruta.name}):"})
    contenido.append({"type": "image", "base64": img_b64, "mime_type": "image/png"})


llm_model = cargar_llm(model_name="qwen/qwen3.8-27b",  max_tokens=4096, reasoning_effort="low")

multimodal_question = HumanMessage(content=contenido)

response = llm_model.invoke([multimodal_question])

print(response.content)