# Resultados Parte 2

Modelo de audio: `whisper-large-v3-turbo` · Modelo de respuesta: `qwen/qwen3.8-27b`

## 2.1 Transcripción desde archivo

| Audio | Hablante | Condición | Duración (s) | Lo que se dijo | Transcripción | WER |
|---|---|---|---|---|---|---|
| audio_1.mp3 | Integrante 1 | sin ruido | N/D | ¿Cuál es la diferencia entre azúcares totales y azúcares añadidos en la tabla de información nutricional de un alimento? | cuál es la diferencia entre azúcares totales y azúcares añadidos en la tabla de información nutricional de un alimento | 0.0% |
| audio_2.mp3 | Integrante 2 | sin ruido | N/D | Si una porción de un producto tiene ciento treinta y nueve miligramos de sodio, ¿se considera un alimento alto o bajo en sodio? | Si una porción de un producto tiene 139 miligramos de sodio, se considera un alimento alto o bajo en sodio. | 17.4% |
| audio_3.mp3 | Integrante 1 | sin ruido | N/D | ¿Cómo puedo calcular las calorías por porción si conozco los gramos de carbohidratos totales, proteínas y grasas totales? | cómo puedo calcular las calorías por porción si conozco los gramos de carbohidratos totales proteínas y grasas totales | 0.0% |
| audio_4.mp3 | Integrante 2 | con ruido | N/D | ¿Qué significa el porcentaje de valor diario en una etiqueta nutricional y por qué cambia entre la columna por cien gramos y la columna por porción? | ¿Qué significa el porcentaje de valor diario en una etiqueta nutricional y por qué cambia entre la columna por 100 gramos y la columna por porción? | 3.8% |

## 2.2 Respuesta del modelo a partir de la transcripción

| Audio | Transcripción enviada al modelo | Respuesta del modelo |
|---|---|---|
| audio_1.mp3 | cuál es la diferencia entre azúcares totales y azúcares añadidos en la tabla de información nutricional de un alimento | **Azúcares totales** = suma de todos los azúcares presentes en el alimento, tanto los naturales (como los de la fruta o la leche) como los añadidos.  **Azúcares añadidos** = solo los que se incorporaron durante el procesamiento (azúcar, miel, jarabes, concentrados de fruta, etc.).  En resumen: totales = naturales + añadidos. Los añadidos son los que más conviene vigilar, ya que no aportan nutrientes y su exceso se asocia a obesidad, diabetes y enfermedades cardiovasculares. |
| audio_2.mp3 | Si una porción de un producto tiene 139 miligramos de sodio, se considera un alimento alto o bajo en sodio. | Con **139 mg de sodio por porción**, el alimento se considera **bajo en sodio**, ya que el límite para esa clasificación es ≤ 140 mg por porción.  Para referencia: - **Bajo en sodio:** ≤ 140 mg - **Alto en sodio:** ≥ 400 mg  Así que 139 mg queda justo por debajo del umbral de "bajo". |
| audio_3.mp3 | cómo puedo calcular las calorías por porción si conozco los gramos de carbohidratos totales proteínas y grasas totales | Usa la fórmula:  **Calorías = (g carbohidratos × 4) + (g proteínas × 4) + (g grasas × 9)**  Ejemplo: si una porción tiene 30 g de carbohidratos, 10 g de proteína y 5 g de grasa: (30×4) + (10×4) + (5×9) = 120 + 40 + 45 = **205 kcal**  Nota: el alcohol aporta 7 kcal/g, pero no suele aparecer en etiquetas de alimentos. |
| audio_4.mp3 | ¿Qué significa el porcentaje de valor diario en una etiqueta nutricional y por qué cambia entre la columna por 100 gramos y la columna por porción? | El **% Valor Diario (%VD)** indica qué proporción de la cantidad diaria recomendada de un nutriente aporta esa cantidad del alimento (basada en una dieta de 2,000 kcal).  Cambia entre columnas porque el %VD se calcula sobre la **cantidad real de nutriente presente** en esa porción. Si la porción es de 30 g, hay menos grasa, azúcar, etc. que en 100 g, por lo que el %VD será menor. Es simplemente una proporción: a más gramos, más nutriente, mayor %VD. |
