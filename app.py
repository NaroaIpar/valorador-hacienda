import streamlit as st
import os
import json
import asyncio
import sys
import signal # Añade esto en tus imports de arriba del todo

os.system("playwright install chromium") # <-- Añade esto para la nube

# --- 1. REPARACIÓN PARA WINDOWS + PLAYWRIGHT ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Importamos tus módulos
from leer_imagen import extraer_datos_pdf
from obtener_modelo import extraer_datos_allianz
from obtener_valoracion import obtener_valoracion_gipuzkoa

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Valorador Pro", page_icon="🚗")


# --- BARRA LATERAL: CONTROLES DEL SISTEMA ---
with st.sidebar:
    st.header("⚙️ Controles del Sistema")
    st.write("Cuando termines de usar la aplicación, pulsa este botón antes de cerrar la pestaña para liberar la memoria del ordenador.")
    
    if st.button("🛑 Apagar Servidor y Salir", type="primary", use_container_width=True):
        st.success("Apagando el sistema... Ya puedes cerrar esta pestaña.")
        # Esta instrucción "mata" el proceso de la terminal instantáneamente
        os.kill(os.getpid(), signal.SIGTERM)
# --------------------------------------------

# Inicializamos la memoria de la sesión si no existe
if 'paso' not in st.session_state:
    st.session_state.paso = 'inicio'
    st.session_state.datos_coche = {}
    st.session_state.opciones = []
    st.session_state.precio_final = None

st.title("🚗 Asistente de Valoración Automática")
# --- 3. FLUJO DE LA APLICACIÓN ---

# PASO INICIAL: SUBIDA DE ARCHIVO
if st.session_state.paso == 'inicio':
    st.markdown("Sube el **Permiso de Circulación** para empezar.")
    archivo_pdf = st.file_uploader("Arrastra tu PDF aquí", type=["pdf"])

    if archivo_pdf:
        if st.button("🚀 Iniciar Análisis", type="primary"):
            ruta_temp = "temp_permiso.pdf"
            with open(ruta_temp, "wb") as f:
                f.write(archivo_pdf.getbuffer())

            try:
                # --- A. Leer con IA ---
                with st.status("🤖 Analizando PDF con Inteligencia Artificial...", expanded=True) as status:
                    status.write("Subiendo documento de forma segura...")
                    datos = extraer_datos_pdf(ruta_temp)
                    
                    if datos:
                        status.update(label="✅ PDF leído con éxito", state="complete", expanded=False)
                        st.success("📄 Datos extraídos del documento:")
                        st.json(datos) # Deja el JSON visible en la pantalla
                    else:
                        status.update(label="❌ Error al leer el PDF", state="error")
                        st.stop() # Detiene la ejecución aquí

                # --- B. Buscar en Allianz ---
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
                    # Creamos un mensajero que escribe directamente dentro de esta cajita de status
                    def mensajero_web(texto):
                        status.write(texto)
                    
                    # Le pasamos el mensajero a tu función
                    opciones = obtener_valoracion_gipuzkoa(datos, log_func=mensajero_web)
                    
                    status.update(label="✅ Tablas de Hacienda escaneadas", state="complete", expanded=False)
                    st.session_state.opciones = opciones
                    st.session_state.paso = 'seleccionar'
                    st.rerun()

            finally:
                if os.path.exists(ruta_temp):
                    os.remove(ruta_temp)

# PASO DE SELECCIÓN: EL USUARIO ELIGE EN LA WEB
elif st.session_state.paso == 'seleccionar':
    
    # --- NUEVO: Mostrar resumen de datos para que el usuario pueda comparar ---
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

    st.divider() # Una línea separadora para que quede elegante
    
    # --- CONTINÚA LA SELECCIÓN ---
    st.subheader("📍 Selecciona la versión exacta en Hacienda:")
    
    if st.session_state.opciones:
        # Añadimos un formato visual para que destaque más
        seleccion = st.radio("Coincidencias encontradas:", st.session_state.opciones)
        
        if st.button("⚖️ Obtener Valoración Final", type="primary"):
            
            # --- Hacienda Fase 2 ---
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

# PASO FINAL: RESULTADO
elif st.session_state.paso == 'finalizado':
    st.balloons()
    st.success("✅ ¡Proceso completado con éxito!")
    
    # --- 1. DIBUJAMOS LA FICHA RESUMEN PARA QUE NO DESAPAREZCA ---
    # Usamos st.container(border=True) para crear una caja que quede genial al imprimir
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
        
        # El precio en grande
        st.metric("💰 Base Liquidable (Hacienda Gipuzkoa)", f"{st.session_state.precio_final} €")

    # --- 2. GENERAMOS EL TEXTO PARA EL BOTÓN DE DESCARGA ---
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
    
    # --- 3. BOTONES DE ACCIÓN ---
    st.write("") # Un pequeño espacio en blanco
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Botón nativo de Streamlit para descargar archivos
        st.download_button(
            label="📥 Descargar Informe (TXT)",
            data=informe_texto,
            file_name=f"Valoracion_{st.session_state.datos_coche.get('id')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    with col_btn2:
        # Botón para reiniciar todo el proceso
        if st.button("🔄 Valorar otro coche", type="primary", use_container_width=True):
            st.session_state.paso = 'inicio'
            st.session_state.datos_coche = {}
            st.session_state.precio_final = None
            st.rerun()