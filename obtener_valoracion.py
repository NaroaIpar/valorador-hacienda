import time
import re
from playwright.sync_api import sync_playwright


def obtener_valoracion_gipuzkoa(coche, modelo_a_seleccionar=None, log_func=print):
    with sync_playwright() as p:
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
        page = browser.new_page()
        
        try:
            # PASO 1: Inicio
            log_func("PASO 1: Inicio")
            page.goto("https://ssl7.gipuzkoa.net/vehiculos/defaultc.asp")
            page.get_by_text("Haga su valoración ahora").click()
            
            # PASO 2: Fecha matriculación
            log_func("PASO 2: Fecha matriculación")
            
            # Separamos la fecha
            dia, mes, anio = coche["fecha_mat"].split("/")

            # 1. Buscamos el texto exacto que está justo encima de las cajitas y hacemos clic en él
            # Usamos un texto parcial lo suficientemente único
            texto_etiqueta = page.locator("text=Introduzca la fecha de la 1ª matriculación")
            texto_etiqueta.wait_for()
            texto_etiqueta.click()

            # 2. Ahora que el foco del ratón está en ese texto, al dar Tabulador 
            # caeremos inevitablemente en el primer hueco disponible (el Día)
            page.keyboard.press("Tab")
            page.keyboard.type(dia)
            
            # 3. Tabulamos al segundo hueco (el Mes)
            page.keyboard.press("Tab")
            page.keyboard.type(mes)
            
            # 4. Tabulamos al tercer hueco (el Año)
            page.keyboard.press("Tab")
            page.keyboard.type(anio)

            # Continuamos
            page.click("input[value='Continuar']")


            # PASO 3: Tipo de medio de transporte
            log_func("PASO 3: Tipo de medio de transporte")
            # Buscamos el radio button que corresponde al texto del tipo de vehículo
            page.check(f"text={coche['tipo_vehiculo']}")
            page.click("input[value='Continuar']")

            # PASO 4: Seleccionar MARCA
            log_func("PASO 4: Seleccionar MARCA")
            page.wait_for_selector("select[name='marca']")
            page.select_option("select[name='marca']", label=coche["marca"])
            page.click("input[value='Continuar']")

            # PASO 5: Búsqueda
            modelos_encontrados = []
            found = False
            while not found:
                page.wait_for_selector("table")
                filas = page.locator("tr").all()
                
                for fila in filas:
                    texto = fila.inner_text().replace('\n', ' ').strip()
                    if (coche["modelo_buscar"] in texto and str(coche["cc"]) in texto and 
                        str(coche["kw"]) in texto and coche["combustible"] in texto):
                        
                        # Si ya sabemos cuál queremos (Fase 2)
                        if modelo_a_seleccionar and modelo_a_seleccionar in texto:
                            fila.locator("input[type='radio']").click()
                            found = True
                            break
                        # Si solo estamos explorando (Fase 1)
                        elif modelo_a_seleccionar is None:
                            modelos_encontrados.append(texto)

                if found: break

                # Lógica del botón siguiente
                boton_siguiente = page.locator("a.siguientePag")
                if boton_siguiente.is_visible():
                    with page.expect_navigation():
                        boton_siguiente.click()
                else:
                    break # No hay más páginas

            # --- RETORNO SEGÚN LA FASE ---
            if modelo_a_seleccionar is None:
                return modelos_encontrados # Devolvemos la lista para la web
            
            # PASO 6: Si hemos seleccionado uno, sacar el precio
            page.click("input[value='Continuar']")
            page.wait_for_selector("text=Base liquidable:")
            cuerpo = page.content()
            import re
            match = re.search(r'Base liquidable:.*?([\d\.]+)', cuerpo, re.DOTALL)
            return match.group(1) if match else None

        finally:
            browser.close()


# if __name__ == "__main__":
#     lista_coches = [{
#         "id": "2348 HJS",
#         "fecha_mat": "13/03/2012",
#         "tipo_vehiculo": "Turismos y Todo Terrenos",
#         "marca": "AUDI",
#         "modelo_buscar": "Q5", # Solo la palabra clave del modelo
#         "version_completa": "Q5 3.0 TDI 240 QUATTRO S-TRONIC", # Lo guardamos como referencia
#         "cc": 2967,
#         "kw": 176,
#         "combustible": "D"
#     }]
#     for v in lista_coches:
#         obtener_valoracion_gipuzkoa(v)
#         time.sleep(2)