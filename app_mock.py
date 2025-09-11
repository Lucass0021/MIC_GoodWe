# app_mock_appliances.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px

# -------------------- Mock de dados por aparelho --------------------
mock_data = [
    {"time": "2025-09-11T08:00:00", "Dispositivo": "Secador de cabelo", "Voltage": 127.8, "Current": 6.0, "Power": 760, "Energy": 0.1, "Frequency": 60.0, "PF": 0.95},
    {"time": "2025-09-11T09:00:00", "Dispositivo": "Laptop", "Voltage": 127.7, "Current": 0.5, "Power": 60, "Energy": 0.05, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-11T10:00:00", "Dispositivo": "Geladeira", "Voltage": 127.9, "Current": 1.5, "Power": 190, "Energy": 0.12, "Frequency": 60.0, "PF": 0.85},
    {"time": "2025-09-11T11:00:00", "Dispositivo": "Micro-ondas", "Voltage": 127.8, "Current": 5.0, "Power": 600, "Energy": 0.08, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-11T12:00:00", "Dispositivo": "Ventilador", "Voltage": 127.6, "Current": 0.3, "Power": 35, "Energy": 0.02, "Frequency": 60.0, "PF": 0.95},
]

df = pd.DataFrame(mock_data)
df["time"] = pd.to_datetime(df["time"])

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant - Mock Aparelhos", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Simulação de Aparelhos")
st.caption("Simulação de consumo de dispositivos comuns conectados à tomada")

with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today(), key="data_ref_appliances")
    st.info("Todos os registros aparecem independentemente da data selecionada.")

# -------------------- KPIs gerais --------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Tensão média (V)", f"{df['Voltage'].mean():.2f}")
col2.metric("Corrente total (A)", f"{df['Current'].sum():.2f}")
col3.metric("Potência total (W)", f"{df['Power'].sum():.2f}")
col4.metric("Energia total (kWh)", f"{df['Energy'].sum():.3f}")

# -------------------- Gráficos --------------------
left, right = st.columns(2)

with left:
    fig_power = px.bar(df, x="Dispositivo", y="Power", color="Dispositivo", title="Potência Instantânea por Aparelho (W)")
    fig_power.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_power, use_container_width=True)

with right:
    fig_energy = px.bar(df, x="Dispositivo", y="Energy", color="Dispositivo", title="Energia Consumida por Aparelho (kWh)")
    fig_energy.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_energy, use_container_width=True)

# -------------------- Tabela --------------------
with st.expander("Ver tabela de dados"):
    st.dataframe(df, use_container_width=True, hide_index=True)

# -------------------- Download CSV --------------------
st.download_button(
    "Baixar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"goodwe_mock_appliances_{date.today()}.csv",
    mime="text/csv"
)
