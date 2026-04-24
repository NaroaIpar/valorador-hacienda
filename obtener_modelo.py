from playwright.sync_api import sync_playwright
import time

def extraer_datos_allianz(matricula):
    with sync_playwright() as p:
        # Si prefieres que abra tu Chrome normal en lugar de Chromium, puedes añadir: channel="chrome"
        # browser = p.chromium.launch(headless=False, channel="chrome") 
        # CÁMBIALO A HEADLESS=TRUE Y QUITA EL CHANNEL
        # --- CONFIGURACIÓN ANTI-CRASH PARA LA NUBE ---
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        # ---------------------------------------------
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Abriendo Allianz Direct...")
            # En webs modernas (SPAs), es mejor usar 'networkidle' o dejar el valor por defecto
            page.goto("https://www.allianzdirect.es/seguro-de-coche/calcular-precio/#/vehicleSearch", wait_until="domcontentloaded", timeout=60000)            
            # --- 1. GESTIÓN DE COOKIES ---
            print("Esperando banner de cookies...")
            try:
                selector_cookies = "#onetrust-accept-btn-handler"
                # Esperamos a que esté visible
                page.wait_for_selector(selector_cookies, state="visible", timeout=10000)
                # Le damos un pequeño respiro a la animación de la web antes de clicar
                time.sleep(1)
                page.click(selector_cookies)
                print("✅ Cookies aceptadas.")
                # Damos un segundo para que el banner desaparezca de la pantalla
                time.sleep(1)
            except Exception as e:
                print("⚠️ No apareció el banner de cookies o ya estaba cerrado.")

            # --- 2. INTRODUCIR MATRÍCULA Y BUSCAR ---
            print(f"Buscando campo de matrícula para {matricula}...")
            
            # Usamos el atributo data-testid que es infalible para el testing
            selector_input = "input[data-testid='userdata.insuredProperty.licensePlate']"
            
            page.wait_for_selector(selector_input, state="visible", timeout=15000)
            
            # Rellenamos la matrícula
            page.fill(selector_input, matricula)
            print("Matrícula introducida.")

            # Pulsamos Enter para que la web busque el coche
            page.keyboard.press("Enter")
            print("Pulsado Enter, esperando a la base de datos...")

            # --- 3. ESPERAR RESULTADOS ---
            print("Esperando a que la web identifique el vehículo...")
            
            # 1. Esperamos específicamente al contenedor del primer resultado.
            # Esto evita que leamos el mensaje de "cargando" o "¡Aquí está!"
            selector_resultado = "div[data-testid='vehicleSearchResult-0']"
            page.wait_for_selector(selector_resultado, state="visible", timeout=20000)
            
            # 2. Extraer el nombre del modelo.
            # Según el HTML, está dentro de un span con la clase "radio-label"
            elemento_modelo = page.locator(f"{selector_resultado} span.radio-label").first
            
            # inner_text() saca el texto y strip() le quita los espacios en blanco que sobran al final
            nombre_completo = elemento_modelo.inner_text().strip()
            
            if not nombre_completo or len(nombre_completo) < 3:
                raise Exception("El nombre extraído parece estar vacío o ser erróneo.")

            print(f"✨ ÉXITO: {nombre_completo}")
            
            # --- 4. LIMPIEZA DE DATOS ---
            palabras = nombre_completo.split(" ")
            marca = palabras[0].upper()
            version_completa = " ".join(palabras[1:])
            
            return {
                "marca": marca,
                "version_completa": version_completa
            }

        except Exception as e:
            print(f"❌ Error en Allianz: {e}")
            page.screenshot(path="debug_allianz.png")
            return None
        finally:
            browser.close()

# if __name__ == "__main__":
#     res = extraer_datos_allianz("2348HJS")
#     print(f"\nRESULTADO PARA MAIN: {res}")