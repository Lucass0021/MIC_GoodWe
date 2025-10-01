import streamlit as st

def render_header():
    st.markdown("""
        <div class="custom-header">
            <h1>⚡ SMART ENERGY MONITOR</h1>
            <p>Monitoramento Inteligente de Consumo Elétrico</p>
        </div>
    """, unsafe_allow_html=True)
