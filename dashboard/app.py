import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(
    page_title="Sistema de Predicción de Lesividad",
    layout="wide",
    page_icon="🏥"
)

# CSS
st.markdown("""
<style>
    /* Variables de color */
    :root {
        --primary-color: #2E86C1;
        --success-color: #28B463;
        --warning-color: #F39C12;
        --danger-color: #E74C3C;
        --neutral-dark: #34495E;
        --neutral-light: #ECF0F1;
        --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Header principal */
    .main-header {
        background: var(--background-gradient);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Secciones */
    .section-card2 {
        background: grey;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1.5rem;
    }
    
    .section-title {
        color: white;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .section-icon {
        width: 24px;
        height: 24px;
        margin-right: 10px;
        opacity: 0.8;
    }
    
    /* Botones modernos */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(46, 134, 193, 0.3);
    }
    
    .stButton > button:hover {
        background: #2874A6;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(46, 134, 193, 0.4);
    }
    
    /* Alertas personalizadas */
    .alert-success {
        background: #D5F4E6;
        border: 1px solid var(--success-color);
        border-radius: 8px;
        padding: 1rem;
        color: #196F3D;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: #FEF5E7;
        border: 1px solid var(--warning-color);
        border-radius: 8px;
        padding: 1rem;
        color: #B7950B;
        margin: 1rem 0;
    }
    
    .alert-danger {
        background: #FADBD8;
        border: 1px solid var(--danger-color);
        border-radius: 8px;
        padding: 1rem;
        color: #C0392B;
        margin: 1rem 0;
    }
    
    /* Resultado de predicción - Transparente con bordes */
    .prediction-result {
        text-align: center;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        background-color: transparent !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .prediction-safe {
        border: 3px solid #28A745 !important; /* Borde verde */
    }

    .prediction-danger {
        border: 3px solid #DC3545 !important; /* Borde rojo */
    }

    .prediction-title {
        color: white !important; /* Texto blanco */
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }

    .prediction-probability {
        color: white !important; /* Texto blanco */
        font-size: 1.4rem;
        font-weight: 600;
        opacity: 0.95;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }

    .prediction-description {
        color: white !important; /* Texto blanco */
        font-size: 1.1rem;
        margin-top: 1rem;
        opacity: 0.9;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }
    
    /* Footer moderno */
    .modern-footer {
        background: var(--neutral-dark);
        color: white;
        text-align: center;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 3rem;
    }
    
    /* Ocultar elementos default de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Sistema de Predicción de Lesividad</h1>
    <p>Análisis Inteligente para Accidentes de Tráfico en Madrid</p>
</div>
""", unsafe_allow_html=True)

# Constantes
TIPOS_VEHICULO = [
    "Turismo", "Motocicleta > 125cc", "Furgoneta", "Motocicleta hasta 125cc", 
    "Bicicleta", "Ciclomotor", "Todo terreno", "Autobús", "Camión rígido", 
    "Maquinaria de obras", "Tractocamión", "Se desconoce", "Cuadriciclo no ligero", 
    "Vehículo articulado", "Autobús articulado", "Otros vehículos con motor", 
    "Autocaravana", "Patinete", "Ciclo", "Cuadriciclo ligero", "Vmu eléctrico",
    "Semiremolque", "Microbús <= 17 plazas", "Sin especificar", "Autobus emt", 
    "Remolque", "Tranvía", "Caravana", "Camión de bomberos", 
    "Otros vehículos sin motor", "Bicicleta epac (pedaleo asistido)",
    "Moto de tres ruedas > 125cc", "Tren/metro", "Ambulancia samur", 
    "Moto de tres ruedas hasta 125cc", "Ciclomotor de dos ruedas l1e-b", 
    "Maquinaria agrícola", "Autobús articulado emt", "Ciclomotor de tres ruedas", 
    "Ciclo de motor l1e-a", "Patinete no eléctrico"
]

TIPOS_ACCIDENTE = [
    "Colisión lateral", "Alcance", "Choque contra obstáculo fijo", 
    "Colisión fronto-lateral", "Caída", "Colisión frontal", "Otro", 
    "Atropello a persona", "Colisión múltiple", "Vuelco", "Atropello a animal",
    "Solo salida de la vía", "Despeñamiento"
]

RANGOS_EDAD = [
    "Menor de 5 años", "De 6 a 9 años", "De 10 a 14 años", "De 15 a 17 años", 
    "De 18 a 20 años", "De 21 a 24 años", "De 25 a 29 años", "De 30 a 34 años", 
    "De 35 a 39 años", "De 40 a 44 años", "De 45 a 49 años", "De 50 a 54 años", 
    "De 55 a 59 años", "De 60 a 64 años", "De 65 a 69 años", "De 70 a 74 años", 
    "Más de 74 años", "Desconocido"
]

ESTADOS_METEOROLOGICOS = [
    "Despejado", "Se desconoce", "Lluvia débil", "Nublado", 
    "Lluvia intensa", "Granizando", "Nevando"
]

features = {}

st.markdown("---")

# Sección de datos del accidente
st.markdown("""
<div class="section-card">
    <div class="section-title">
        <svg class="section-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
        </svg>
        Datos del Accidente
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Información Personal")
    features["tipo_persona"] = st.selectbox(
        "Tipo de persona",
        ["Conductor", "Pasajero", "Peatón"],
        help="Rol de la persona en el accidente"
    )
    
    features["rango_edad"] = st.selectbox(
        "Rango de edad",
        RANGOS_EDAD,
        help="Grupo etario de la persona involucrada"
    )
    
    features["sexo"] = st.selectbox(
        "Sexo",
        ["Hombre", "Mujer", "Desconocido"],
        help="Sexo de la persona involucrada"
    )

with col2:
    st.subheader("Información del Siniestro")
    features["tipo_vehiculo"] = st.selectbox(
        "Tipo de vehículo",
        TIPOS_VEHICULO,
        help="Vehículo involucrado en el accidente"
    )
    
    features["tipo_accidente"] = st.selectbox(
        "Tipo de accidente",
        TIPOS_ACCIDENTE,
        help="Clasificación del siniestro"
    )
    
    features["estado_meteorológico"] = st.selectbox(
        "Condiciones meteorológicas",
        ESTADOS_METEOROLOGICOS,
        help="Estado del tiempo durante el accidente"
    )

st.markdown("---")

# Sección de ubicación
st.markdown("""
<div class="section-card">
    <div class="section-title">
        <svg class="section-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z" />
        </svg>
        Ubicación del Accidente
    </div>
</div>
""", unsafe_allow_html=True)

modo = st.selectbox(
    "Método de selección de ubicación",
    ["Distrito", "Coordenadas GPS"],
    help="Selecciona cómo especificar la ubicación"
)

if modo == "Distrito":
    distrito_map = {
        "Centro": 1, "Arganzuela": 2, "Retiro": 3, "Salamanca": 4, "Chamartín": 5,
        "Tetuán": 6, "Chamberí": 7, "Fuencarral-El Pardo": 8, "Moncloa-Aravaca": 9,
        "Latina": 10, "Carabanchel": 11, "Usera": 12, "Puente de Vallecas": 13,
        "Moratalaz": 14, "Ciudad Lineal": 15, "Hortaleza": 16, "Villaverde": 17,
        "Villa de Vallecas": 18, "Vicálvaro": 19, "San Blas-Canillejas": 20, "Barajas": 21
    }
    
    distrito_nombre = st.selectbox(
        "Distrito de Madrid",
        list(distrito_map.keys()),
        help="Distrito donde ocurrió el accidente"
    )
    
    features["cod_distrito"] = distrito_map[distrito_nombre]
    features["coordenada_x_utm"] = None
    features["coordenada_y_utm"] = None
    
    st.markdown(f"""
    <div class="alert-success">
        <strong>Distrito seleccionado:</strong> {distrito_nombre}
    </div>
    """, unsafe_allow_html=True)

    with st.empty():
        dummy_map = folium.Map(location=[40.4168, -3.7038], zoom_start=12)
        st_folium(dummy_map, width=None, height=0, key="hidden_map")

else:
    # Inicialización del estado
    if "map_click" not in st.session_state:
        st.session_state["map_click"] = None

    # Crear mapa
    map_madrid = folium.Map(location=[40.4168, -3.7038], zoom_start=12)

    # Agregar marcador solo si hay ubicación seleccionada
    if st.session_state["map_click"]:
        folium.Marker(
            st.session_state["map_click"],
            icon=folium.Icon(color="red", icon="map-marker"),
            popup="📍 Ubicación seleccionada"
        ).add_to(map_madrid)

    mapa = st_folium(
        map_madrid, 
        width=None, 
        height=500,
        key="madrid_map",
        returned_objects=["last_clicked"]
    )

    if mapa and mapa.get("last_clicked"):
        clicked_point = mapa["last_clicked"]
        # Guardar como lista [lat, lng]
        st.session_state["map_click"] = [
            clicked_point["lat"], 
            clicked_point["lng"]
        ]
        # Forzar recarga para mostrar marcador
        st.rerun()

    # Configurar features según selección
    if st.session_state["map_click"]:
        features["coordenada_y_utm"] = st.session_state["map_click"][0]
        features["coordenada_x_utm"] = st.session_state["map_click"][1] 
        features["cod_distrito"] = None
        
        st.markdown(f"""
        <div class="alert-success">
            <strong>Coordenadas:</strong> {features['coordenada_y_utm']:.4f}, {features['coordenada_x_utm']:.4f}
        </div>
        """, unsafe_allow_html=True)
    else:
        features["coordenada_y_utm"] = None
        features["coordenada_x_utm"] = None  
        features["cod_distrito"] = None
        
        st.markdown("""
        <div class="alert-warning">
            Haz clic en el mapa para seleccionar una ubicación
        </div>
        """, unsafe_allow_html=True)

# Validación y predicción
can_predict = True
if modo == "Coordenadas GPS" and not st.session_state.get("map_click"):
    can_predict = False

st.markdown("---")

st.markdown("""
<div class="section-card">
    <div class="section-title">
        <svg class="section-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9,11H7L8.5,6.5L10,11M15,11H13L14.5,6.5L16,11M12,3A19,19 0 0,0 3,6A19,19 0 0,0 12,21A19,19 0 0,0 21,6A19,19 0 0,0 12,3Z" />
        </svg>
        Análisis Predictivo
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("Analizar Caso", disabled=not can_predict):
    with st.spinner("Procesando análisis..."):
        try:
            response = requests.post(
                "http://localhost:8000/predict",
                json=features,
                timeout=10
            )
            
            if response.status_code == 200:
                resultado = response.json()
                pred = resultado.get("prediction")
                prob = resultado.get("probability", 0)

                if pred == 1:
                    st.markdown(f"""
                    <div class="prediction-result prediction-safe">
                        <div class="prediction-title">Sin Asistencia Sanitaria</div>
                        <div class="prediction-probability">Probabilidad: {prob*100:.1f}%</div>
                        <div class="prediction-description">
                            El modelo predice que este accidente probablemente no requerirá 
                            asistencia sanitaria inmediata.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="prediction-result prediction-danger">
                        <div class="prediction-title">Asistencia Sanitaria Requerida</div>
                        <div class="prediction-probability">Probabilidad: {prob*100:.1f}%</div>
                        <div class="prediction-description">
                            El modelo predice que este accidente probablemente requerirá 
                            asistencia sanitaria. Se recomienda activar protocolos de emergencia.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except requests.exceptions.ConnectionError:
            st.markdown("""
            <div class="alert-danger">
                <strong>Error de conexión:</strong> No se pudo conectar con el sistema de análisis.
                Verifica que el servidor esté ejecutándose.
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Información del modelo
with st.expander("Información Técnica del Modelo"):
    st.markdown("""
    ### Características Técnicas
    
    **Algoritmo**: XGBoost (Extreme Gradient Boosting)
    
    **Variables de Entrada**:
    - Información personal y demográfica
    - Características del vehículo involucrado  
    - Tipo y circunstancias del accidente
    - Condiciones meteorológicas
    - Ubicación geográfica
    
    ### Métricas de Rendimiento
    - **Precisión global**: 84%
    - **Sensibilidad**: 84%
    - **Especificidad**: 84%
    
    ### Interpretación
    - **Sin Asistencia**: Lesiones leves sin necesidad de atención médica
    - **Con Asistencia**: Lesiones que requieren intervención sanitaria
    
    **Nota**: Esta herramienta es de apoyo para la toma de decisiones y no reemplaza 
    el criterio profesional de los equipos de emergencia.
    """)

# Footer
st.markdown("""
<div class="modern-footer">
    <h3>Sistema de Predicción de Lesividad en Accidentes de Tráfico</h3>
    <p>Desarrollado para mejorar la respuesta de emergencias y la seguridad vial urbana en Madrid</p>
    <p style="opacity: 0.7;">Tecnologías: Python • XGBoost • Streamlit • FastAPI</p>
</div>
""", unsafe_allow_html=True)
