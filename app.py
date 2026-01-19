import streamlit as st
from openai import OpenAI
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import urllib.parse

# Configuración de página y Estilo
st.set_page_config(page_title="Reclamo Funes", page_icon="📢", layout="centered")

# Inicializar Geocodificador (para obtener la dirección)
geolocator = Nominatim(user_agent="noris_funes_app")

# Título Principal
st.title("📢 Reclamo Funes")

# --- SISTEMA DE PASOS (STEPPER) ---
paso = st.radio("Progreso del reporte:", ["1. Ubicación", "2. Detalle y Foto", "3. Generar y Enviar"], horizontal=True)

# Inicializar variables en la sesión para que no se borren al cambiar de paso
if 'direccion' not in st.session_state: st.session_state.direccion = ""
if 'coords' not in st.session_state: st.session_state.coords = ""

# --- PASO 1: UBICACIÓN ---
if paso == "1. Ubicación":
    st.subheader("📍 Paso 1: Tocá el mapa donde está el problema")
    
    FUNES_LAT, FUNES_LNG = -32.9168, -60.8115
    m = folium.Map(location=[FUNES_LAT, FUNES_LNG], zoom_start=14)
    m.add_child(folium.LatLngPopup())
    
    map_data = st_folium(m, height=400, width=700)
    
    if map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lng = map_data['last_clicked']['lng']
        st.session_state.coords = f"{lat}, {lng}"
        
        # OBTENER DIRECCIÓN AUTOMÁTICA
        try:
            location = geolocator.reverse(f"{lat}, {lng}")
            st.session_state.direccion = location.address.split(",")[0] + ", Funes"
            st.success(f"✅ Ubicación detectada: {st.session_state.direccion}")
        except:
            st.session_state.direccion = "Dirección en Funes"

    st.info("Una vez marcada la ubicación, pasá al punto '2. Detalle y Foto' arriba.")

# --- PASO 2: DETALLE Y FOTO ---
elif paso == "2. Detalle y Foto":
    st.subheader("📝 Paso 2: Contanos qué pasó")
    
    if not st.session_state.direccion:
        st.warning("⚠️ Primero marcá el lugar en el mapa (Paso 1).")
    
    tipo_problema = st.selectbox("Categoría:", ["🕳️ Bache / Calle", "💡 Luminaria rota", "🌿 Poda / Residuos", "🚨 Seguridad / Otro"])
    detalle = st.text_area("Descripción breve:", placeholder="Ej: La lámpara parpadea hace dos días...")
    
    # SUBIDA DE FOTO
    foto = st.file_uploader("📸 Subí una foto del problema (opcional)", type=['jpg', 'png', 'jpeg'])
    if foto:
        st.image(foto, caption="Vista previa de la evidencia", width=300)

    st.session_state.datos_reporte = {"tipo": tipo_problema, "detalle": detalle, "tiene_foto": "SÍ" if foto else "NO"}

# --- PASO 3: GENERAR Y ENVIAR ---
elif paso == "3. Enviar":
    st.subheader("✨ Paso 3: Revisar y Enviar")
    
    if 'datos_reporte' not in st.session_state or not st.session_state.direccion:
        st.error("Faltan datos de los pasos anteriores.")
    else:
        # Recuperar API KEY de Secrets
        api_key = st.secrets.get("OPENAI_API_KEY")
        
        if api_key and st.button("🚀 Generar Reclamo con IA"):
            client = OpenAI(api_key=api_key)
            
            prompt = f"""
            Escribí un reclamo formal para la Municipalidad de Funes.
            Tipo: {st.session_state.datos_reporte['tipo']}
            Detalle: {st.session_state.datos_reporte['detalle']}
            Ubicación exacta: {st.session_state.direccion} (Coordenadas: {st.session_state.coords})
            Adjunta foto: {st.session_state.datos_reporte['tiene_foto']}
            Firmar como: Vecino de Funes mediante la plataforma Noris IA.
            """
            
            with st.spinner("La IA está redactando..."):
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.session_state.carta = res.choices[0].message.content

        if 'carta' in st.session_state:
            st.text_area("Texto listo para enviar:", st.session_state.carta, height=250)
            
            msg_codificado = urllib.parse.quote(st.session_state.carta)
            numero_muni = "5493412248414"
            
            st.link_button("🟢 Enviar reporte por WhatsApp", f"https://wa.me/{numero_muni}?text={msg_codificado}")
