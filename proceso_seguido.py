import os
import json
import sys

# Importamos tus tres super-módulos
from leer_imagen import extraer_datos_pdf
from obtener_modelo import extraer_datos_allianz
from obtener_valoracion import obtener_valoracion_gipuzkoa

def main():
    print("==================================================")
    print("🤖 INICIANDO ASISTENTE DE VALORACIÓN DE VEHÍCULOS")
    print("==================================================\n")

    ruta_mi_pdf = "0001_permiso circulacion.pdf" 

    # --- PASO 0: LECTURA DEL PDF ---
    print("--- PASO 0: Extrayendo datos del Permiso con IA ---")
    if not os.path.exists(ruta_mi_pdf):
        print(f"⚠️ ERROR CRÍTICO: No se encontró el archivo '{ruta_mi_pdf}'.")
        sys.exit(1) # Detenemos el script aquí

    datos_coche = extraer_datos_pdf(ruta_mi_pdf)
    
    if not datos_coche:
        print("⚠️ ERROR CRÍTICO: La IA no pudo leer el documento.")
        sys.exit(1) # Detenemos el script aquí

    print("\n✅ Datos base extraídos del PDF:")
    print(json.dumps(datos_coche, indent=4, ensure_ascii=False))


    # --- PASO 1: ALLIANZ ---
    print(f"\n--- PASO 1: Buscando nombre comercial en Allianz ({datos_coche['id']}) ---")
    res_allianz = extraer_datos_allianz(datos_coche['id'])

    if res_allianz:
        # Actualizamos el diccionario con los datos limpios de Allianz
        datos_coche.update(res_allianz)
        print(f"✅ Nombre comercial actualizado: {datos_coche['marca']} {datos_coche['version_completa']}")
    else:
        print("⚠️ Aviso: No se pudo conectar con Allianz. Usaremos el nombre técnico del PDF para buscar en Hacienda.")


    # --- PASO 2: HACIENDA GIPUZKOA ---
    print(f"\n--- PASO 2: Consultando Base Liquidable en Hacienda ---")
    valor = obtener_valoracion_gipuzkoa(datos_coche)

    # --- RESULTADO FINAL ---
    print("\n==================================================")
    if valor:
        print(f"🚀 ÉXITO: La base liquidable del vehículo es {valor} €")
    else:
        print("❌ FIN: No se pudo encontrar el modelo exacto en las tablas de Hacienda.")
    print("==================================================")

if __name__ == "__main__":
    main()