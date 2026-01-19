import streamlit as st
from openai import OpenAI
import folium
from streamlit_folium import st_folium
import urllib.parse

# Configuración Inicial
st.set_page_config(page_title="Reportes Funes", page_icon="📢")
st.title("📢 Reporte Ciudadano Funes")
st.markdown("Reportá baches, luminarias rotas o restos de poda. La IA redactará el reclamo formal.")

# Intenta buscar la clave en Secrets, si no la encuentra, deja que se pueda poner a mano
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)

    # 1. MAPA DE FUNES
    st.subheader("1. Tocá el mapa en el lugar del problema")
    FUNES_LAT, FUNES_LNG = -32.9168, -60.8115
    m = folium.Map(location=[FUNES_LAT, FUNES_LNG], zoom_start=14)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=300, width=700)
    
    coords = ""
    if map_data['last_clicked']:
        coords = f"Lat: {map_data['last_clicked']['lat']}, Lng: {map_data['last_clicked']['lng']}"
        st.success(f"📍 Ubicación marcada")

    # 2. DETALLE
    tipo_problema = st.selectbox("Tipo de problema", ["Bache / Calle", "Luminaria rota", "Residuos verdes / Poda", "Otro"])
    detalle = st.text_area("Describí el problema brevemente:")

    if st.button("Generar Reclamo Formal ✨"):
        prompt = f"Convertí esta queja en una carta formal para la Municipalidad de Funes. Tipo: {tipo_problema}. Detalle: {detalle}. Ubicación: {coords}. Firmar como 'Vecino de Funes'."
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        st.session_state['carta'] = res.choices[0].message.content

    # 3. ENVÍO
    if 'carta' in st.session_state:
        carta_final = st.text_area("Carta redactada:", st.session_state['carta'], height=200)
        msg = urllib.parse.quote(carta_final)
        
        col1, col2 = st.columns(2)
        # Número de ejemplo (reemplazar por el de la Muni o Defensa Civil)
        # El número debe ser solo números, sin el +
        numero_muni = "5493412248414" 
        col1.link_button("Enviar por WhatsApp 🟢", f"https://wa.me/{numero_muni}?text={msg}")
        col2.link_button("Enviar por Email ✉️", f"mailto:atencionciudadana@funes.gob.ar?subject=Reclamo&body={msg}")
else:

    st.warning("Falta la API Key en la barra lateral.")


