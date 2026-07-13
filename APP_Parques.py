import streamlit as st
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
st.title("Accesibilidad a Parques Urbanos en Valdivia")
st.markdown("Exploración espacial de áreas verdes, infraestructura y métricas territoriales.")

# --- 1. CARGA Y PROCESAMIENTO DE DATOS ---

@st.cache_data
def cargar_parques():
    gdf = gpd.read_file(r"/home/nunez93/Escritorio/APLICACIONES SIG/Trabajo Final/Parques Valdivia.gpkg")
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_vial():
    # REEMPLAZA POR EL NOMBRE EXACTO DE TU ARCHIVO DE RED VIAL
    gdf = gpd.read_file(r"/home/nunez93/Escritorio/APLICACIONES SIG/Semana_15/TRABAJO FINAL/red_vial_reproyectada_cortado_union.gpkg") 
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_limite():
    # REEMPLAZA POR EL NOMBRE EXACTO DE TU ARCHIVO DE LÍMITE URBANO
    gdf = gpd.read_file(r"/home/nunez93/Escritorio/APLICACIONES SIG/Trabajo Final/limite_urbano_Valdivia_reproy.gpkg")
    return gdf.to_crs(epsg=4326)

@st.cache_data
def cargar_y_procesar_raster():
    with rasterio.open(r"/home/nunez93/Escritorio/APLICACIONES SIG/Trabajo Final/DEM_RECORTADO_COMUNA_VALDIVIA.tif") as src:
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

# Cargar insumos
parques_valdivia = cargar_parques()
raster_img, raster_bounds, r_min, r_max = cargar_y_procesar_raster()

# NUEVO: Cargar capas adicionales (asegúrate de que los archivos estén en tu carpeta data)
red_vial = cargar_vial()
limite_urbano = cargar_limite()


# --- 2. PANEL DE CONTROL (SIDEBAR) ---

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
lista_parques = ["Todos"] + parques_valdivia['NOMBRE'].dropna().unique().tolist()
parque_seleccionado = st.sidebar.selectbox("Selecciona un parque específico:", lista_parques)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estadísticas")

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


# --- 3. LÓGICA DE ESTILOS CARTOGRÁFICOS ---

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


# --- 4. CREACIÓN DEL MAPA ---

mapa = folium.Map(location=[-39.8142, -73.2459], zoom_start=13, tiles=None)

# NUEVO: control=False elimina el mapa base del LayerControl flotante
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

# NUEVO Capa: Límite Urbano (Polígono vacío con borde rojo segmentado)
if mostrar_limite:
    folium.GeoJson(
        limite_urbano,
        name="Límite Urbano",
        style_function=lambda x: {
            'fillColor': 'transparent', 
            'color': '#d73027', 
            'weight': 2.5,
            'dashArray': '5, 5'  # Hace que la línea sea punteada
        }
    ).add_to(mapa)

# NUEVO Capa: Red Vial (Líneas delgadas grises)
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

# Control de capas flotante (Ahora solo mostrará Ráster, Límite, Vial y Parques)
folium.LayerControl(collapsed=False).add_to(mapa)

# NUEVO: Botón de Pantalla Completa movido a la izquierda para evitar conflictos visuales
Fullscreen(
    position='topleft',
    title='Expandir a pantalla completa',
    title_cancel='Salir de pantalla completa',
    force_separate_button=True
).add_to(mapa)

st_folium(mapa, width=1100, height=650)