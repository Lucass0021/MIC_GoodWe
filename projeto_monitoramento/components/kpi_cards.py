import streamlit as st
import pandas as pd
from utils.style_utils import create_metric_card

def render_kpi_cards(historico):
    # Aplica a classe para os ícones vermelhos
    st.markdown('<div class="metrics-section">', unsafe_allow_html=True)
    st.markdown("### Métricas de Consumo")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if historico:
        df_historico_latest = pd.DataFrame(historico)
        
        # ✅ TRATAMENTO SEGURO - Verificar se as colunas existem
        voltage_col = next((col for col in ['Voltage', 'Voltagem', 'voltage'] if col in df_historico_latest.columns), None)
        current_col = next((col for col in ['Current', 'Corrente', 'current'] if col in df_historico_latest.columns), None)
        power_col = next((col for col in ['Power', 'Potência', 'power'] if col in df_historico_latest.columns), None)
        energy_col = next((col for col in ['Energy', 'Energia', 'energy'] if col in df_historico_latest.columns), None)
        
        tension_mean = df_historico_latest[voltage_col].mean() if voltage_col else 0.0
        current_sum = df_historico_latest[current_col].sum() if current_col else 0.0
        power_sum = df_historico_latest[power_col].sum() if power_col else 0.0
        energy_sum = df_historico_latest[energy_col].sum() if energy_col else 0.0
    else:
        tension_mean = current_sum = power_sum = energy_sum = 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            create_metric_card("TENSÃO MÉDIA", f"{tension_mean:.1f}", "V"),
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            create_metric_card("CORRENTE TOTAL", f"{current_sum:.1f}", "A"), 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            create_metric_card("POTÊNCIA TOTAL", f"{power_sum:.0f}", "W"),
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            create_metric_card("ENERGIA TOTAL", f"{energy_sum:.2f}", "kWh"),
            unsafe_allow_html=True
        )
