import streamlit as st

def apply_custom_style():
    """Aplica o tema escuro personalizado com as cores ajustadas"""
    
    st.markdown("""
        <style>
        /* ===== CORES PRINCIPAIS ===== */
        :root {
            --brand-red: #E60012;
            --background-dark: #121212;
            --sidebar-dark: #1A1A1A;
            --card-dark: #1E1E1E;
            --text-primary: #FFFFFF;
            --text-secondary: #B0B0B0;
        }
        
        /* ===== FUNDO PRINCIPAL ===== */
        .main {
            background-color: var(--background-dark) !important;
            color: var(--text-primary) !important;
        }
        
        .stApp {
            background-color: var(--background-dark) !important;
        }
        
        /* ===== SIDEBAR - COR SIMILAR AO FUNDO ===== */
        .css-1d391kg {
            background-color: var(--sidebar-dark) !important;
        }
        
        .css-1d391kg p, .css-1d391kg label, .css-1d391kg div, .css-1d391kg span {
            color: var(--text-primary) !important;
        }
        
        .sidebar .sidebar-content {
            background-color: var(--sidebar-dark) !important;
        }
        
        /* ===== HEADER PRINCIPAL ===== */
        .custom-header {
            background: linear-gradient(135deg, var(--brand-red) 0%, #CC0010 100%) !important;
            padding: 2rem 1rem !important;
            border-radius: 15px !important;
            margin-bottom: 2rem !important;
            text-align: center !important;
            box-shadow: 0 4px 12px rgba(230, 0, 18, 0.3) !important;
        }
        
        .custom-header h1 {
            color: white !important;
            margin: 0 !important;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
        }
        
        .custom-header p {
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0 !important;
            font-size: 1.2rem !important;
        }
        
        /* ===== ÍCONES DOS DISPOSITIVOS - VERMELHO ===== */
        .device-section h3 {
            color: var(--brand-red) !important;
        }
        
        .device-section h3::before {
            content: "🔌 ";
            color: var(--brand-red) !important;
        }
        
        /* ===== ÍCONES DAS MÉTRICAS - VERMELHO ===== */
        .metrics-section h3 {
            color: var(--brand-red) !important;
        }
        
        .metrics-section h3::before {
            content: "📊 ";
            color: var(--brand-red) !important;
        }
        
        /* ===== CARDS DE DISPOSITIVOS ===== */
        .device-card {
            background: var(--card-dark) !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            border-left: 4px solid var(--brand-red) !important;
            margin: 0.5rem 0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            border: 1px solid #333333 !important;
        }
        
        .device-card h4 {
            color: var(--text-primary) !important;
            margin: 0 !important;
        }
        
        .device-card p {
            color: var(--text-secondary) !important;
            margin: 0 !important;
        }
        
        /* ===== CARDS DE MÉTRICAS ===== */
        .metric-card {
            background: var(--card-dark) !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            border-left: 4px solid var(--brand-red) !important;
            text-align: center !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            border: 1px solid #333333 !important;
        }
        
        .metric-card h4 {
            color: var(--text-secondary) !important;
            margin: 0 0 8px 0 !important;
            font-size: 0.9rem !important;
            text-transform: uppercase !important;
        }
        
        .metric-card h2 {
            color: var(--brand-red) !important;
            margin: 0 !important;
            font-size: 1.8rem !important;
        }
        
        .metric-card p {
            color: var(--text-secondary) !important;
            margin: 0 !important;
            font-size: 0.9rem !important;
        }
        
        /* ===== BOTÕES ===== */
        .stButton > button {
            background-color: var(--brand-red) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600 !important;
        }
        
        .stButton > button:hover {
            background-color: #CC0010 !important;
            border-color: #CC0010 !important;
        }
        
        /* ===== TÍTULOS E TEXTOS ===== */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
        }
        
        p, div, span, label {
            color: var(--text-primary) !important;
        }
        
        /* ===== CHECKBOXES E SLIDERS ===== */
        .stCheckbox > label, .stSlider > label {
            color: var(--text-primary) !important;
        }
        
        /* ===== GRÁFICOS ===== */
        .js-plotly-plot .plotly {
            background: transparent !important;
        }
        
        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 8px !important;
        }
        
        ::-webkit-scrollbar-track {
            background: #2a2a2a !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--brand-red) !important;
            border-radius: 4px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def create_metric_card(title, value, unit, color="#E60012"):
    """Cria um card de métrica estilizado"""
    return f"""
        <div class="metric-card">
            <h4>{title}</h4>
            <h2>{value}</h2>
            <p>{unit}</p>
        </div>
    """

def create_device_card(device_name, power, energy, priority, color="#E60012"):
    """Cria um card de dispositivo estilizado"""
    priority_color = {
        "Crítica": "#E60012",
        "Alta": "#E60012", 
        "Média": "#FFA502",
        "Moderada": "#FFA502",
        "Mínima": "#2ED573",
        "Baixa": "#2ED573"
    }.get(priority, "#E60012")
    
    return f"""
        <div class="device-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; font-size: 1.1rem;">{device_name}</h4>
                <span style="background: {priority_color}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: 600;">
                    ⚡ {priority}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 0.8rem;">Potência</p>
                    <p style="margin: 0; color: {color}; font-size: 1.1rem; font-weight: 600;">{power} W</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 0.8rem;">Energia</p>
                    <p style="margin: 0; color: {color}; font-size: 1.1rem; font-weight: 600;">{energy} kWh</p>
                </div>
            </div>
        </div>
    """
