import streamlit as st
import os
import json
import asyncio
import sys
import signal
import uuid
import re

os.system("playwright install chromium")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from leer_imagen import extraer_datos_pdf
from obtener_modelo import extraer_datos_allianz
from obtener_valoracion import obtener_valoracion_gipuzkoa

st.set_page_config(page_title="Ipar Artekaritza", page_icon="🛡️", layout="wide")

# --- SIDEBAR: API KEY (para la pestaña de Valoración) ---
with st.sidebar:
    st.subheader("🔑 Clave de Google Gemini")
    st.markdown(
        "Para usar la valoración automática necesitas una clave gratuita de Google. "
        "Sigue estos pasos:\n\n"
        "1. Entra en [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)\n"
        "2. Pulsa el botón **\"Crear clave de API\"** (arriba a la derecha)\n"
        "3. Copia la clave y pégala aquí abajo"
    )
    api_key_usuario = st.text_input(
        "Pega aquí tu API Key",
        type="password",
        placeholder="AIza...",
    )
    if api_key_usuario:
        gemini_api_key = api_key_usuario
    else:
        try:
            gemini_api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            gemini_api_key = None

    if not gemini_api_key:
        st.warning("Introduce tu API Key para usar la Valoración Automática.")

# Memoria de sesión
if 'paso' not in st.session_state:
    st.session_state.paso = 'inicio'
    st.session_state.datos_coche = {}
    st.session_state.opciones = []
    st.session_state.precio_final = None

# ── PESTAÑAS PRINCIPALES ──
tab1, tab2 = st.tabs(["📋 Gestión Documental", "🚗 Valoración Automática Hacienda"])

# ── TAB 1: Interfaz HTML (React + Gemini fetch directo) ──
with tab1:
    with open("interface.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=920, scrolling=True)

# ── TAB 2: Valoración automática con Playwright ──
with tab2:
    st.title("🚗 Asistente de Valoración Automática")

    # PASO INICIAL: SUBIDA DE ARCHIVO O ENTRADA MANUAL
    if st.session_state.paso == 'inicio':
        tab_auto, tab_manual = st.tabs(["📄 Subir PDF (Automático con IA)", "✏️ Introducir datos manualmente"])

        # --- TAB AUTOMÁTICO ---
        with tab_auto:
            st.markdown("Sube el **Permiso de Circulación** para empezar.")
            archivo_pdf = st.file_uploader("Arrastra tu PDF aquí", type=["pdf"])

            if archivo_pdf:
                buscar_allianz = st.checkbox(
                    "🔍 Buscar modelo comercial en Allianz",
                    value=True,
                    help="Mejora la referencia del modelo al buscar en Hacienda. Desactívalo si quieres ir más rápido o si Allianz suele fallar."
                )
                if st.button("🚀 Iniciar Análisis", type="primary", disabled=not gemini_api_key):
                    codigo_unico = uuid.uuid4().hex
                    ruta_temp = f"temp_permiso_{codigo_unico}.pdf"
                    with open(ruta_temp, "wb") as f:
                        f.write(archivo_pdf.getbuffer())

                    try:
                        # --- A. Leer con IA ---
                        with st.status("🤖 Analizando PDF con Inteligencia Artificial...", expanded=True) as status:
                            status.write("Subiendo documento de forma segura...")
                            datos = extraer_datos_pdf(ruta_temp, gemini_api_key)

                            if datos:
                                status.update(label="✅ PDF leído con éxito", state="complete", expanded=False)
                                st.success("📄 Datos extraídos del documento:")
                                st.json(datos)
                            else:
                                status.update(label="❌ Error al leer el PDF", state="error")
                                st.info("💡 Si el error persiste, puedes introducir los datos manualmente en la pestaña **✏️ Introducir datos manualmente**.")
                                st.stop()

                        assert datos is not None
                        # --- B. Buscar en Allianz (opcional) ---
                        if buscar_allianz:
                            with st.status("🔍 Consultando base de datos de Allianz...", expanded=True) as status:
                                status.write(f"Buscando la matrícula {datos['id']}...")
                                res_allianz = extraer_datos_allianz(datos['id'])

                                if res_allianz:
                                    datos.update(res_allianz)
                                    status.update(label="✅ Modelo comercial encontrado", state="complete", expanded=False)
                                    st.info(f"✨ Modelo Allianz: **{datos['marca']} {datos['version_completa']}**")
                                else:
                                    status.update(label="⚠️ No se conectó con Allianz", state="complete", expanded=False)
                                    st.warning("Usando nombre técnico del PDF.")

                        st.session_state.datos_coche = datos

                        # --- C. Hacienda Fase 1 ---
                        with st.status("🏛️ Conectando con Hacienda de Gipuzkoa...", expanded=True) as status:
                            def mensajero_web(texto):
                                status.write(texto)

                            opciones = obtener_valoracion_gipuzkoa(datos, log_func=mensajero_web)

                            status.update(label="✅ Tablas de Hacienda escaneadas", state="complete", expanded=False)
                            st.session_state.opciones = opciones
                            st.session_state.paso = 'seleccionar'
                            st.rerun()

                    finally:
                        if os.path.exists(ruta_temp):
                            os.remove(ruta_temp)
                            print(f"🧹 Limpieza: Archivo {ruta_temp} borrado.")

        # --- TAB MANUAL ---
        with tab_manual:
            st.markdown("Introduce los datos del vehículo directamente para ir más rápido.")

            with st.form("form_datos_manuales"):
                col1, col2 = st.columns(2)
                with col1:
                    f_matricula = st.text_input("🏷️ Matrícula", placeholder="1234ABC")
                    f_fecha = st.text_input("📅 Fecha de matriculación", placeholder="DD/MM/YYYY")
                    f_marca = st.text_input("🚗 Marca", placeholder="AUDI",
                                            help="En MAYÚSCULAS como aparece en Hacienda (ej: VOLKSWAGEN, BMW)")
                    f_version = st.text_input("📋 Versión completa (opcional)", placeholder="Q5 3.0 TDI 240 QUATTRO",
                                              help="Solo para el informe final. Si la dejas vacía se usará el modelo de búsqueda.")
                with col2:
                    f_modelo = st.text_input("🔍 Modelo (para búsqueda en Hacienda)", placeholder="Q5",
                                             help="Normalmente la primera palabra del campo D.3 del permiso")
                    f_cc = st.number_input("⚙️ Cilindrada (cc)", min_value=0, step=1, value=0)
                    f_kw = st.number_input("⚡ Potencia (kW)", min_value=0, step=1, value=0)
                    f_combustible = st.selectbox("⛽ Combustible", options=["D", "G"],
                                                 format_func=lambda x: "Diésel" if x == "D" else "Gasolina")

                f_buscar_allianz = st.checkbox(
                    "🔍 Buscar modelo comercial en Allianz",
                    value=False,
                    help="Consulta Allianz con la matrícula para obtener el nombre comercial completo del modelo."
                )
                submit_manual = st.form_submit_button("🔍 Buscar en Hacienda", type="primary", use_container_width=True)

            if submit_manual:
                errores = []
                if not f_matricula.strip():
                    errores.append("La matrícula es obligatoria.")
                if not f_fecha.strip():
                    errores.append("La fecha de matriculación es obligatoria.")
                elif not re.match(r'^\d{2}/\d{2}/\d{4}$', f_fecha.strip()):
                    errores.append("La fecha debe tener el formato DD/MM/YYYY (ej: 13/03/2012).")
                if not f_marca.strip():
                    errores.append("La marca es obligatoria.")
                if not f_modelo.strip():
                    errores.append("El modelo de búsqueda es obligatorio.")
                if f_cc <= 0:
                    errores.append("La cilindrada debe ser mayor que 0.")
                if f_kw <= 0:
                    errores.append("La potencia debe ser mayor que 0.")

                if errores:
                    for e in errores:
                        st.error(e)
                else:
                    datos_manual = {
                        "id": f_matricula.strip().upper(),
                        "fecha_mat": f_fecha.strip(),
                        "tipo_vehiculo": "Turismos y Todo Terrenos",
                        "marca": f_marca.strip().upper(),
                        "version_completa": f_version.strip() if f_version.strip() else f_modelo.strip().upper(),
                        "modelo_buscar": f_modelo.strip().upper(),
                        "cc": int(f_cc),
                        "kw": int(f_kw),
                        "combustible": f_combustible,
                    }
                    if f_buscar_allianz:
                        with st.status("🔍 Consultando base de datos de Allianz...", expanded=True) as status:
                            status.write(f"Buscando la matrícula {datos_manual['id']}...")
                            res_allianz = extraer_datos_allianz(datos_manual['id'])

                            if res_allianz:
                                datos_manual.update(res_allianz)
                                status.update(label="✅ Modelo comercial encontrado", state="complete", expanded=False)
                                st.info(f"✨ Modelo Allianz: **{datos_manual['marca']} {datos_manual['version_completa']}**")
                            else:
                                status.update(label="⚠️ No se conectó con Allianz", state="complete", expanded=False)
                                st.warning("No se encontró el modelo en Allianz. Se usarán los datos introducidos.")

                    st.session_state.datos_coche = datos_manual

                    with st.status("🏛️ Conectando con Hacienda de Gipuzkoa...", expanded=True) as status:
                        def mensajero_manual(texto):
                            status.write(texto)

                        opciones = obtener_valoracion_gipuzkoa(datos_manual, log_func=mensajero_manual)

                        status.update(label="✅ Tablas de Hacienda escaneadas", state="complete", expanded=False)
                        st.session_state.opciones = opciones
                        st.session_state.paso = 'seleccionar'
                        st.rerun()

    # PASO DE SELECCIÓN
    elif st.session_state.paso == 'seleccionar':

        with st.expander("📄 Ver datos extraídos (PDF + Allianz)", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Datos técnicos (Gemini):**")
                st.write(f"🏷️ **Matrícula:** {st.session_state.datos_coche.get('id')}")
                st.write(f"📅 **Fecha:** {st.session_state.datos_coche.get('fecha_mat')}")
                st.write(f"⚙️ **Motor:** {st.session_state.datos_coche.get('cc')} cc | {st.session_state.datos_coche.get('kw')} kW | {st.session_state.datos_coche.get('combustible')}")
            with col2:
                st.markdown("**Nombre comercial (Allianz):**")
                st.success(f"{st.session_state.datos_coche.get('marca')} {st.session_state.datos_coche.get('version_completa')}")

        st.divider()
        st.subheader("📍 Selecciona la versión exacta en Hacienda:")

        if st.session_state.opciones:
            seleccion = st.radio("Coincidencias encontradas:", st.session_state.opciones)

            if st.button("⚖️ Obtener Valoración Final", type="primary"):
                with st.status("🏛️ Extrayendo valoración oficial...", expanded=True) as status:
                    def mensajero_web(texto):
                        status.write(texto)

                    status.write(f"Seleccionando modelo: {seleccion[:30]}...")
                    precio = obtener_valoracion_gipuzkoa(st.session_state.datos_coche, modelo_a_seleccionar=seleccion, log_func=mensajero_web)

                    status.update(label="✅ Valoración extraída", state="complete", expanded=False)
                    st.session_state.precio_final = precio
                    st.session_state.paso = 'finalizado'
                    st.rerun()
        else:
            st.error("No se encontraron modelos compatibles en Hacienda.")
            if st.button("⬅️ Volver a intentar"):
                st.session_state.paso = 'inicio'
                st.rerun()

    # PASO FINAL
    elif st.session_state.paso == 'finalizado':
        st.balloons()
        st.success("✅ ¡Proceso completado con éxito!")

        with st.container(border=True):
            st.subheader("📄 Informe Oficial de Valoración")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Datos Técnicos del Permiso:**")
                st.write(f"🏷️ **Matrícula:** {st.session_state.datos_coche.get('id')}")
                st.write(f"📅 **Fecha Mat.:** {st.session_state.datos_coche.get('fecha_mat')}")
                st.write(f"⚙️ **Motor:** {st.session_state.datos_coche.get('cc')} cc | {st.session_state.datos_coche.get('kw')} kW | {st.session_state.datos_coche.get('combustible')}")
            with col2:
                st.markdown("**Identificación Comercial:**")
                st.info(f"{st.session_state.datos_coche.get('marca')} {st.session_state.datos_coche.get('version_completa')}")

            st.divider()
            st.metric("💰 Base Liquidable (Hacienda Gipuzkoa)", f"{st.session_state.precio_final} €")

        informe_texto = f"""
    INFORME DE VALORACIÓN DE VEHÍCULO
    =================================
    Matrícula: {st.session_state.datos_coche.get('id')}
    Fecha Matriculación: {st.session_state.datos_coche.get('fecha_mat')}
    Marca: {st.session_state.datos_coche.get('marca')}
    Modelo Comercial (Allianz): {st.session_state.datos_coche.get('version_completa')}

    -- Datos Técnicos --
    Cilindrada: {st.session_state.datos_coche.get('cc')} cc
    Potencia: {st.session_state.datos_coche.get('kw')} kW
    Combustible: {st.session_state.datos_coche.get('combustible')}

    =================================
    BASE LIQUIDABLE OFICIAL: {st.session_state.precio_final} €
    =================================
    """

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                label="📥 Descargar Informe (TXT)",
                data=informe_texto,
                file_name=f"Valoracion_{st.session_state.datos_coche.get('id')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_btn2:
            if st.button("🔄 Valorar otro coche", type="primary", use_container_width=True):
                st.session_state.paso = 'inicio'
                st.session_state.datos_coche = {}
                st.session_state.precio_final = None
                st.rerun()
