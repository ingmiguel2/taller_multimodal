# taller_multimodal
taller_multimodal
Taller de entrada multimodal (imágenes) y audio. Dominio: etiquetas de información nutricional de alimentos empacados.
Instalación
> Cargando el código de Bash…
​
Variables de entorno
Crear un archivo .env en esta carpeta (ya está en .gitignore, no se sube al repositorio):
> Cargando el código de Plain Text…
​
Opcionales: LLM_MODEL (modelo por defecto de utils/load_model.py), STT_MODEL (por defecto whisper-large-v3-turbo), LLM_MODEL_AUDIO (por defecto qwen/qwen3.8-27b).
Cómo ejecutar
Parte
Comando
Qué hace
1.1
python p1_pregunta_Imagen.py
Pregunta sobre una imagen local (base64)
1.2
python p1.2_extraccion_estructurada.py
Extracción estructurada en JSON, validación y % de aciertos
1.3
python p1.3_comparacion_imagenes.py
Comparación de 2 o 3 imágenes en una solicitud
2 (grabar)
python grabar_audios.py
Graba los 4 audios en audios/ y guarda hablante/condición en audios/metadatos.json
2.1 y 2.2
python p2_audio.py
Transcribe cada audio con Whisper, envía la transcripción al modelo y escribe resultados_parte2.md / .json
Los audios también se pueden grabar con el celular (wav, mp3, m4a, ogg o webm, máx. 25 MB) y copiarlos a audios/ con los nombres de metadatos.json.
Estructura
imagenes/: imágenes usadas en la Parte 1 (error.png se usa para el error provocado).
audios/: grabaciones de la Parte 2 y metadatos.json (hablante, condición y frase dicha de cada audio).
utils/: carga del modelo.
