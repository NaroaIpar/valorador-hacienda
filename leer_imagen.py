import os
import json
from google import genai

import streamlit as st


def extraer_datos_pdf(ruta_pdf, api_key):
    client = genai.Client(api_key=api_key)
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
            # Convertimos el error técnico a texto para poder buscar palabras clave
            error_tecnico = str(e)
            
            # --- TRADUCTOR DE ERRORES PARA EL USUARIO ---
            if "503" in error_tecnico or "UNAVAILABLE" in error_tecnico:
                st.error("🚦 **Atasco en la nube:** Hay muchas personas usando la Inteligencia Artificial en este momento. Espera unos 30 segundos y vuelve a darle al botón.")
                
            elif "429" in error_tecnico or "RESOURCE_EXHAUSTED" in error_tecnico:
                st.error("⏳ **Límite de velocidad:** Has hecho muchas valoraciones seguidas muy rápido. El sistema te ha puesto en pausa para no saturarse. Espera 1 minuto y vuelve a intentarlo.")
                
            elif "400" in error_tecnico or "API_KEY_INVALID" in error_tecnico:
                st.error("🔑 **Problema con la llave:** La clave de Google no funciona. Avisa al Desarrollador/a para que revise la caja fuerte (Secrets) de Streamlit.")
                
            elif "JSONDecodeError" in error_tecnico:
                st.error("🧩 **Confusión de la IA:** La Inteligencia Artificial ha leído el PDF pero se ha hecho un lío al escribir los datos. Vuelve a intentarlo, a la segunda suele acertar.")
                
            else:
                # Si es un error nuevo que no conocemos, mostramos un mensaje genérico
                st.error("❌ **No se ha podido procesar este documento.**")
            
            # --- ZONA PARA LA DESARROLLADORA (Oculto por defecto) ---
            with st.expander("🛠️ Ver detalle técnico (Solo para mantenimiento)"):
                st.code(error_tecnico)
                
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