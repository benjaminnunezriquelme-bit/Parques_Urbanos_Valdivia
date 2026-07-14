# Crearemos el script.py solicitado incluyendo la información de Introducción, Objetivos, Funciones y Conclusión de manera ordenada y elegante usando componentes de Streamlit (st.tabs, st.info, st.expander, etc.) para que se vea sumamente profesional.

codigo_modificado = """import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as cm
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
import rasterio
from rasterio.warp import transform_bounds
import numpy as np
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Geovisualizador Valdivia", layout="wide")

# --- BANNER / ENCABEZADO ---
st.title("🌲 Accesibilidad a Parques Urbanos en Valdivia")
st.markdown("### Exploración espacial interactiva de áreas verdes, infraestructura y métricas territoriales")

# --- NUEVA SECCIÓN: INTRODUCCIÓN, OBJETIVOS Y METODOLOGÍA (Pestañas informativas) ---
tab_contexto, tab_visualizador = st.tabs(["📋 Información del Proyecto", "🗺️ Mapa Interactivo y Visualizador"])

with tab_contexto:
    st.markdown("#### 📘 Introducción")
    st.write(
        "Los Parques urbanos en Valdivia son de suma importancia para el bienestar de sus habitantes, "
        "conocidos por su infraestructura y tipos de bosques. Debido a esto, es de gran relevancia contar con una "
        "aplicación donde los visitantes puedan acceder de mejor forma a ellos y comprender su distribución espacial, "
        "especialmente visualizando cómo interactúan con la red vial de la ciudad."
    )
    
    col_obj, col_fun = st.columns(2)
    with col_obj:
        st.markdown("#### 🎯 Objetivos")
        st.markdown(
            \"\"\"
            * **Visualización Digital:** Obtener una plataforma digital para visualizar los distintos parques urbanos con su respectiva información de servicios e infraestructura.
            * **Democratización de la Información:** Ofrecer una plataforma abierta a toda persona, sin necesidad de que posea mayores conocimientos geográficos o en Sistemas de Información Geográfica (SIG).
            \"\"\"
        )
    with col_fun:
        st.markdown("#### 🛠️ Funciones Implementadas")
        st.markdown(
            \"\"\"
            * **Representatividad Territorial:** App interactiva basada en datos espaciales y oficiales.
            * **Sidebar Interactivo:** Panel lateral para el control de capas y filtros en tiempo real.
            * **Tooltips Informativos:** Consulta rápida de atributos clave de los parques al pasar el cursor.
            * **Panel de Estadísticas y Filtros:** Dinámicas aplicadas según el parque seleccionado.
            * **Modo Pantalla Completa:** Experiencia inmersiva en la visualización cartográfica.
            \"\"\"
        )
    
    st.markdown("---")
    st.markdown("#### 🧭 Mapas Base Disponibles")
    st.markdown("- **OpenStreetMap**: Cartografía clásica de referencia mundial.")
    st.markdown("- **Carto DB Claro**: Diseño minimalista ideal para resaltar información temática.")
    st.markdown("- **Imagen DEM Valdivia**: Modelo Digital de Elevación para comprender el relieve de la comuna.")

# Carga de datos dentro del flujo común o caché
@st.cache_data
def cargar_parques():
    gdf = gpd.read_file(r"C:\\Users\\esteb\\OneDrive - Universidad Austral de Chile\\USB_respaldo\\Geografia 2019\\Semestres\\2026\\I_semestre\\SIG\\Contenidos\\Semana_15_1\\TRABAJO FINAL\\Parques Valdivia.gpkg")
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_vial():
    gdf = gpd.read_file(r"C:\\Users\\esteb\\OneDrive - Universidad Austral de Chile\\USB_respaldo\\Geografia 2019\\Semestres\\2026\\I_semestre\\SIG\\Contenidos\\Semana_15_1\\TRABAJO FINAL\\red_vial_reproyectada_cortado_union.gpkg") 
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_limite():
    gdf = gpd.read_file(r"C:\\Users\\esteb\\OneDrive - Universidad Austral de Chile\\USB_respaldo\\Geografia 2019\\Semestres\\2026\\I_semestre\\SIG\\Contenidos\\Semana_15_1\\TRABAJO FINAL\\limite_urbano_Valdivia_reproy.gpkg")
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_y_procesar_raster():
    with rasterio.open(r"C:\\Users\\esteb\\OneDrive - Universidad Austral de Chile\\USB_respaldo\\Geografia 2019\\Semestres\\2026\\I_semestre\\SIG\\Contenidos\\Semana_15_1\\TRABAJO FINAL\\DEM_RECORTADO_COMUNA_VALDIVIA.tif") as src:
        factor_reduccion = 10
        out_shape = (src.count, int(src.height / factor_reduccion), int(src.width / factor_reduccion))
        data = src.read(1, out_shape=out_shape, resampling=rasterio.enums.Resampling.bilinear)
        
        if src.nodata is not None:
            data = np.where(data == src.nodata, np.nan, data)
            
        bounds = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
        folium_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
        
        min_real = float(np.nanmin(data))
        max_real = float(np.nanmax(data))
        
        data_norm = (data - min_real) / (max_real - min_real)
        cmap = plt.get_cmap('terrain')
        rgba_img = cmap(data_norm)
        rgba_img[..., 3] = np.where(np.isnan(data), 0, 0.6)
        
        return rgba_img, folium_bounds, min_real, max_real

# Cargar insumos (pueden requerirse en ambas pestañas, se cargan globalmente)
try:
    parques_valdivia = cargar_parques()
    raster_img, raster_bounds, r_min, r_max = cargar_y_procesar_raster()
    red_vial = cargar_vial()
    limite_urbano = cargar_limite()
except Exception as e:
    st.error(f"Error al cargar las capas geográficas: {e}. Por favor, verifica que las rutas locales existan.")
    # Datos de respaldo mínimos para evitar caídas si no existen las rutas locales durante la ejecución fuera del entorno local
    parques_valdivia = gpd.GeoDataFrame()

# --- PANEL DE CONTROL (SIDEBAR) ---
st.sidebar.title("🛠️ Panel de Control")

st.sidebar.markdown("### 🗺️ Mapa Base")
mapa_base = st.sidebar.radio(
    "Selecciona el fondo del mapa:",
    ("OpenStreetMap", "CartoDB Claro (Positron)", "Satélite (Esri)")
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Capas de Información")
mostrar_raster = st.sidebar.checkbox("⛰️ Mostrar DEM (Elevación)", value=True)
mostrar_limite = st.sidebar.checkbox("🛑 Mostrar Límite Urbano", value=True)
mostrar_vial = st.sidebar.checkbox("🛣️ Mostrar Red Vial", value=True)
mostrar_parques = st.sidebar.checkbox("🌳 Mostrar Parques Urbanos", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtro Avanzado")
if not parques_valdivia.empty:
    lista_parques = ["Todos"] + parques_valdivia['NOMBRE'].dropna().unique().tolist()
    parque_seleccionado = st.sidebar.selectbox("Selecciona un parque específico:", lista_parques)
else:
    parque_seleccionado = "Todos"

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estadísticas")

if not parques_valdivia.empty:
    if parque_seleccionado != "Todos":
        parques_mapa = parques_valdivia[parques_valdivia['NOMBRE'] == parque_seleccionado]
        sup_parque = parques_mapa['SUPERFICIE'].values[0]
        dir_parque = parques_mapa['DIRECCION'].values[0]
        st.sidebar.metric(label="Superficie del Parque", value=f"{sup_parque:,.0f} m²")
        st.sidebar.info(f"📍 **Dirección:** {dir_parque}")
    else:
        parques_mapa = parques_valdivia
        total_parques = len(parques_mapa)
        area_total = parques_mapa['SUPERFICIE'].sum()
        col1, col2 = st.sidebar.columns(2)
        col1.metric(label="Nº Parques", value=total_parques)
        col2.metric(label="Área Total", value=f"{area_total:,.0f} m²")
else:
    st.sidebar.warning("Datos de parques no cargados.")

# --- RENDERING DE LA PESTAÑA DEL MAPA ---
with tab_visualizador:
    if parques_valdivia.empty:
        st.warning("⚠️ Esperando conexión con los archivos de datos geográficos locales (rutas en Disco C:). Asegúrate de correr la app en tu máquina local donde están los archivos .gpkg y .tif.")
    else:
        # --- LÓGICA DE ESTILOS CARTOGRÁFICOS ---
        min_sup = parques_valdivia['SUPERFICIE'].min()
        max_sup = parques_valdivia['SUPERFICIE'].max()
        colormap_superficie = cm.LinearColormap(
            colors=['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494'], 
            vmin=min_sup,
            vmax=max_sup,
            caption='Superficie del Parque (m²)'
        )

        def estilo_parques(feature):
            superficie = feature['properties']['SUPERFICIE']
            color = '#ffffff' if pd.isna(superficie) or superficie is None else colormap_superficie(superficie)
            return {'fillColor': color, 'color': '#333333', 'weight': 1, 'fillOpacity': 0.8}

        # --- CREACIÓN DEL MAPA ---
        mapa = folium.Map(location=[-39.8142, -73.2459], zoom_start=13, tiles=None)

        if mapa_base == "OpenStreetMap":
            folium.TileLayer(tiles="OpenStreetMap", control=False).add_to(mapa)
        elif mapa_base == "CartoDB Claro (Positron)":
            folium.TileLayer(tiles="CartoDB positron", control=False).add_to(mapa)
        elif mapa_base == "Satélite (Esri)":
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri",
                control=False
            ).add_to(mapa)

        # Capa: Ráster
        if mostrar_raster:
            folium.raster_layers.ImageOverlay(
                image=raster_img,
                bounds=raster_bounds,
                name="Elevación (Ráster DEM)",
                opacity=0.8
            ).add_to(mapa)

        # Capa: Límite Urbano
        if mostrar_limite:
            folium.GeoJson(
                limite_urbano,
                name="Límite Urbano",
                style_function=lambda x: {
                    'fillColor': 'transparent', 
                    'color': '#d73027', 
                    'weight': 2.5,
                    'dashArray': '5, 5'
                }
            ).add_to(mapa)

        # Capa: Red Vial
        if mostrar_vial:
            folium.GeoJson(
                red_vial,
                name="Red Vial",
                style_function=lambda x: {
                    'color': '#878787', 
                    'weight': 1,
                    'opacity': 0.7
                }
            ).add_to(mapa)

        # Capa: Parques Urbanos
        if mostrar_parques:
            folium.GeoJson(
                parques_mapa,
                name="Parques Urbanos",
                style_function=estilo_parques,
                tooltip=folium.GeoJsonTooltip(
                    fields=['NOMBRE', 'SUPERFICIE', 'DIRECCION', 'BAÑOS_ASI'],
                    aliases=['Parque:', 'Superficie (m²):', 'Dirección:', 'Baños Asistidos:'],
                    localize=True,
                    style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
                )
            ).add_to(mapa)
            colormap_superficie.add_to(mapa)

        # Controles del mapa
        folium.LayerControl(collapsed=False).add_to(mapa)

        Fullscreen(
            position='topleft',
            title='Expandir a pantalla completa',
            title_cancel='Salir de pantalla completa',
            force_separate_button=True
        ).add_to(mapa)

        # Mostrar mapa en Streamlit
        st_folium(mapa, width=1100, height=650)

    # --- SECCIÓN: CONCLUSIÓN (Integrada estéticamente en la pestaña visualizadora) ---
    st.markdown("---")
    st.markdown("#### 📝 Conclusión del Análisis Espacial")
    st.info(
        "Una App como esta puede resolver de manera interactiva y simple para distintos grupos etarios donde logren "
        "visualizar los distintos parques que existen en Valdivia, siendo una ciudad con gran cantidad de estos dentro de "
        "sus límites urbanos. Al ser abierta a cualquier persona que tenga el link, puede ver e ir cambiando capas "
        "añadidas en el proyecto.\\n\\n"
        "La Geografía responde en gran medida a mejorar la planificación territorial, lo cual esta aplicación puede al menos "
        "dar una pequeña pincelada a lo que aqueja en cuanto a la espacialidad de los parques existentes en Valdivia y con "
        "qué servicios cuentan."
    )
"""

# Guardar en un archivo
with open("app_valdivia_corregido.py", "w", encoding="utf-8") as f:
    f.write(codigo_modificado)

print("Archivo generado exitosamente.")
