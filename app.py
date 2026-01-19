import streamlit as st
from openai import OpenAI
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import urllib.parse

# Configuración
st.set_page_config(page_title="Reclamo Funes", page_icon="🌳")
geolocator = Nominatim(user_agent="noris_funes_final")

st.title("🌳 Reclamo Funes")
st.markdown("Reportá problemas en la vía pública de forma rápida.")

# --- SECCIÓN GPS AUTOMÁTICO ---
st.subheader("1. Tu Ubicación")
col_gps, col_txt = st.columns([1, 2])

with col_gps:
    if st.button("📍 Usar mi ubicación actual"):
        loc = get_geolocation()
        if loc:
            st.session_state.lat_gps = loc['coords']['latitude']
            st.session_state.lon_gps = loc['coords']['longitude']
            st.success("¡Ubicación capturada!")

# --- MAPA ---
# Coordenadas por defecto (Funes) o las del GPS si existen
default_lat = st.session_state.get('lat_gps', -32.9168)
default_lon = st.session_state.get('lon_gps', -60.8115)

m = folium.Map(location=[default_lat, default_lon], zoom_start=16)
folium.Marker([default_lat, default_lon], tooltip="Tu ubicación").add_to(m)
m.add_child(folium.LatLngPopup())

map_data = st_folium(m, height=350, width=700)

# Lógica de Dirección
lat_click = None
lon_click = None

if map_data['last_clicked']:
    lat_click = map_data['last_clicked']['lat']
    lon_click = map_data['last_clicked']['lng']
elif 'lat_gps' in st.session_state:
    lat_click = st.session_state.lat_gps
    lon_click = st.session_state.lon_gps

direccion_final = "No seleccionada"
if lat_click and lon_click:
    try:
        location = geolocator.reverse(f"{lat_click}, {lon_click}", language="es", addressdetails=True)
        raw = location.raw['address']
        calle = raw.get('road', 'Calle desconocida')
        altura = raw.get('house_number', '')
        direccion_final = f"{calle} {altura}, Funes".strip(", ")
        st.info(f"📍 Dirección: {direccion_final}")
    except:
        direccion_final = "Ubicación en Funes"

# --- FORMULARIO TODO EN UNO ---
st.subheader("2. Detalle del Problema")
tipo = st.selectbox("¿Qué sucede?", ["🕳️ Bache", "💡 Luminaria", "🌿 Poda/Residuos", "🚨 Seguridad"])
detalle = st.text_area("Más información:", placeholder="Contanos un poco más...")
foto = st.file_uploader("📸 Foto (opcional)", type=['jpg', 'jpeg', 'png'])

# --- GENERACIÓN ---
if st.button("🚀 Generar y Enviar Reclamo"):
    if direccion_final == "No seleccionada":
        st.error("Por favor, marcá el lugar en el mapa o usá el GPS.")
    else:
        api_key = st.secrets.get("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        
        prompt = f"Escribí un reclamo municipal formal para Funes. Tipo: {tipo}. Detalle: {detalle}. Ubicación: {direccion_final}. Coordenadas: {lat_click}, {lon_click}. Firmar como Noris IA."
        
        with st.spinner("Redactando..."):
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
            carta = res.choices[0].message.content
            st.text_area("Resultado:", carta, height=200)
            
            # Botón WhatsApp
            msg_wa = urllib.parse.quote(carta)
            st.link_button("🟢 Enviar a la Municipalidad", f"https://wa.me/5493412248414?text={msg_wa}")
