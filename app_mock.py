# app_mock_appliances_gemini_project.py
import os
import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv

# -------------------- Carregar chave da API --------------------
load_dotenv()
CHAVE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=CHAVE_API_KEY)

# -------------------- Configuração do modelo Gemini --------------------
MODELO_ESCOLHIDO = "gemini-1.5-flash"
prompt_sistema = """
Você é um assistente especializado em monitoramento de dispositivos elétricos domésticos.
Seu objetivo é analisar dados de consumo de energia e fornecer respostas precisas, 
breves e confiáveis sobre os dispositivos, como potência, energia consumida, corrente, tensão, etc.
Sempre que possível, explique os cálculos ou critérios utilizados.
"""

llm = genai.GenerativeModel(
    model_name=MODELO_ESCOLHIDO,
    system_instruction=prompt_sistema
)

# -------------------- Mock de dados por dispositivo --------------------
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
st.set_page_config(page_title="GoodWe Assistant - Projeto de Aparelhos", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e análise de consumo de energia de dispositivos comuns")

with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    st.info("Os registros exibidos são simulados, mas representam dispositivos domésticos típicos.")

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
with st.expander("Ver tabela completa"):
    st.dataframe(df, use_container_width=True, hide_index=True)

# -------------------- Download CSV --------------------
st.download_button(
    "Baixar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"goodwe_mock_appliances_{date.today()}.csv",
    mime="text/csv"
)

# -------------------- Chat com Gemini --------------------
st.markdown("---")
st.header("💬 Pergunte ao Gemini sobre os dispositivos")

user_input = st.text_input("Digite sua pergunta sobre os dispositivos:")

if st.button("Enviar pergunta") and user_input:
    try:
        # Converte dados para contexto
        contexto = df.to_dict(orient="records")
        prompt = f"Considere os seguintes dispositivos e dados:\n{contexto}\n\nPergunta: {user_input}"
        
        resposta = llm.generate_content(prompt)
        st.markdown(f"**Resposta do Gemini:** {resposta.text}")
    except Exception as e:
        st.error(f"Erro ao processar a pergunta: {e}")
