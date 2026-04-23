import os
import json
from google import genai

import streamlit as st

# La nube leerá la clave de la caja fuerte secreta de Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

def extraer_datos_pdf(ruta_pdf):
    print(f"📄 Subiendo el documento '{ruta_pdf}' a Gemini...")
    
    try:
        # Subimos el PDF a la nube temporal de Gemini
        documento_subido = client.files.upload(file=ruta_pdf)
        
        # El Prompt estricto
        prompt = """
        Analiza la primera página de este documento PDF, que es un Permiso de Circulación español (puede estar rotado, léelo ajustando la orientación). 
        Extrae la información de las casillas correspondientes y devuélvela ESTRICTAMENTE como un objeto JSON válido, sin bloques de código markdown ni texto adicional.
        
        Aplica estas reglas de formateo exactas para cada clave del JSON:
        - "id": Lee el Campo A (Matrícula). Quita todos los espacios en blanco.
        - "fecha_mat": Lee el Campo I (Fecha de matriculación). Asegúrate de que el formato sea DD/MM/YYYY (cambia guiones por barras).
        - "tipo_vehiculo": Pon siempre "Turismos y Todo Terrenos" por defecto.
        - "marca": Lee el Campo D.1 (Marca).
        - "version_completa": Lee el Campo D.3 (Modelo/Versión completa).
        - "modelo_buscar": Basándote en el Campo D.3, extrae SOLO la primera palabra o identificador principal del modelo (ej. si D.3 es 'Q5 3.0 TDI', pon solo 'Q5').
        - "cc": Lee el Campo P.1 (Cilindrada). Devuelve SOLO el número entero.
        - "kw": Lee el Campo P.2 (Potencia). Devuelve SOLO el número entero.
        - "combustible": Lee el Campo P.3. Si indica 'DIESEL', 'GASOLEO' o similar, pon "D". Si indica 'GASOLINA', pon "G".
        """

        print("🧠 Analizando el documento y extrayendo campos...")
        
        # Hacemos la petición usando el modelo Flash (ideal para documentos rápidos)
        respuesta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[documento_subido, prompt]
        )
        
        # Limpieza de la respuesta por si la IA añade "```json"
        texto_json = respuesta.text.strip()
        if texto_json.startswith("```json"):
            texto_json = texto_json[7:]
        if texto_json.endswith("```"):
            texto_json = texto_json[:-3]
            
        # Convertimos a diccionario
        coche_diccionario = json.loads(texto_json.strip())
        
        # Borramos el archivo de la nube por privacidad
        client.files.delete(name=documento_subido.name)
        
        return coche_diccionario

    except Exception as e:
        print(f"❌ Error al procesar el PDF: {e}")
        return None

# # --- Zona de pruebas ---
# if __name__ == "__main__":
#     # Asegúrate de poner el nombre exacto de tu PDF aquí
#     ruta_mi_pdf = "permiso_circulacion_ejemplo.pdf" 
    
#     if os.path.exists(ruta_mi_pdf):
#         datos_coche = extraer_datos_pdf(ruta_mi_pdf)
        
#         if datos_coche:
#             print("\n✅ ¡ÉXITO! Diccionario generado listo para Playwright:\n")
#             print("coche =", json.dumps(datos_coche, indent=4, ensure_ascii=False))
#     else:
#         print(f"⚠️ No se encontró el archivo en la ruta: {ruta_mi_pdf}")