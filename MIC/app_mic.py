# app_mock_appliances_gemini_project_v6.py
import os
import requests
import streamlit as st
import pandas as pd
from datetime import date, datetime, timezone
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
 
# -------------------- Carregar .env --------------------
load_dotenv()
CHAVE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=CHAVE_API_KEY)
 
# Firebase (defina no .env se quiser trocar)
FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL",
    "https://mic-9d88e-default-rtdb.firebaseio.com"
).rstrip("/")
FIREBASE_AUTH = os.getenv("FIREBASE_AUTH", "")  # opcional (idToken)
 
# -------------------- Configuração do modelo Gemini --------------------
MODELO_ESCOLHIDO = "gemini-1.5-flash"
prompt_sistema = """
Você é um assistente especializado em monitoramento de dispositivos elétricos domésticos.
Seu objetivo é analisar dados de consumo de energia e fornecer respostas precisas,
breves e confiáveis sobre os dispositivos, como potência, energia consumida, corrente, tensão, etc.
Forneça alertas e recomendações para economizar energia com base nos dados apresentados.
Se a pergunta não puder ser respondida apenas com os dados fornecidos, você pode fornecer informações
gerais baseadas em boas práticas ou conhecimento de mercado, indicando claramente quando a resposta é uma estimativa ou referência externa.
"""
llm = genai.GenerativeModel(model_name=MODELO_ESCOLHIDO, system_instruction=prompt_sistema)
 
# -------------------- Funções Firebase --------------------
def firebase_get(path: str):
    """GET simples na REST API do Firebase RTDB."""
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
 
def fetch_tomada1():
    """Busca o estado atual de /tomada1 e devolve dict com os campos esperados."""
    try:
        data = firebase_get("/tomada1")
        if not isinstance(data, dict):
            return None
 
        # Normaliza timestamp
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            t = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            t = datetime.now(timezone.utc)
 
        # Garante presença dos campos (com defaults seguros)
        return {
            "time": t.isoformat(),
            "Voltage": float(data.get("Voltage", 127.8)),
            "Current": float(data.get("Current", 0.0)),
            "Power": float(data.get("Power", 0.0)),
            "Energy": float(data.get("Energy", 0.0)),
            "Frequency": float(data.get("Frequency", 60.0)),
            "PF": float(data.get("PF", 1.0)),
        }
    except Exception as e:
        st.warning(f"Não foi possível ler /tomada1 do Firebase: {e}")
        return None
 
# -------------------- Mock de dados por dispositivo --------------------
mock_data = [
    {"time": "2025-09-11T08:00:00", "Dispositivo": "Secador de cabelo", "Voltage": 127.8, "Current": 6.0, "Power": 760, "Energy": 0.1, "Frequency": 60.0, "PF": 0.95},
    {"time": "2025-09-11T09:00:00", "Dispositivo": "Laptop", "Voltage": 127.7, "Current": 0.5, "Power": 60, "Energy": 0.05, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-11T10:00:00", "Dispositivo": "Geladeira", "Voltage": 127.9, "Current": 1.5, "Power": 190, "Energy": 0.12, "Frequency": 60.0, "PF": 0.85},
    {"time": "2025-09-11T11:00:00", "Dispositivo": "Micro-ondas", "Voltage": 127.8, "Current": 5.0, "Power": 600, "Energy": 0.08, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-11T12:00:00", "Dispositivo": "Ventilador", "Voltage": 127.6, "Current": 0.3, "Power": 35, "Energy": 0.02, "Frequency": 60.0, "PF": 0.95},
    {"time": "2025-09-11T13:00:00", "Dispositivo": "Televisão", "Voltage": 127.5, "Current": 0.8, "Power": 100, "Energy": 0.06, "Frequency": 60.0, "PF": 0.92},
    {"time": "2025-09-11T14:00:00", "Dispositivo": "Ar-condicionado", "Voltage": 127.8, "Current": 3.5, "Power": 450, "Energy": 0.25, "Frequency": 60.0, "PF": 0.88},
    {"time": "2025-09-11T15:00:00", "Dispositivo": "Cafeteira", "Voltage": 127.7, "Current": 2.0, "Power": 250, "Energy": 0.07, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-11T16:00:00", "Dispositivo": "Ferro de passar", "Voltage": 127.9, "Current": 4.0, "Power": 500, "Energy": 0.15, "Frequency": 60.0, "PF": 0.9},
]
 
# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant - Projeto de Aparelhos", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e recomendações de consumo de energia de dispositivos domésticos")
 
# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    st.info("O Gemini pode fornecer alertas, recomendações e responder perguntas sobre os dispositivos.")
    auto_refresh = st.checkbox("Atualizar automaticamente (5s)", value=True)
    if st.button("🔄 Atualizar agora"):
        st.experimental_rerun()  # botão manual
 
# -------------------- Auto-refresh --------------------
if auto_refresh:
    # Atualiza automaticamente a cada 5 segundos
    st_autorefresh(interval=5000, key="datarefresh")
 
# -------------------- Preparar DataFrame --------------------
tomada1 = fetch_tomada1()
df = pd.DataFrame(mock_data)
if tomada1:
    df.loc[df["Dispositivo"] == "Secador de cabelo", ["time","Voltage","Current","Power","Energy","Frequency","PF"]] = [
        pd.to_datetime(tomada1["time"]),
        tomada1["Voltage"],
        tomada1["Current"],
        tomada1["Power"],
        tomada1["Energy"],
        tomada1["Frequency"],
        tomada1["PF"],
    ]
else:
    df["time"] = pd.to_datetime(df["time"])
 
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
 
# -------------------- Alertas e recomendações do Gemini --------------------
st.markdown("---")
st.header("💬 Alertas e recomendações do Gemini")
if st.button("Gerar alertas e recomendações"):
    try:
        contexto = df.to_dict(orient="records")
        prompt = (
            "Analise os seguintes dispositivos e dados de consumo:\n"
            f"{contexto}\n\nForneça alertas e recomendações para economizar energia, "
            "indicando quais dispositivos podem ter consumo elevado ou desperdício."
        )
        resposta = llm.generate_content(prompt)
        st.markdown(f"**Alertas e recomendações:** {resposta.text}")
    except Exception as e:
        st.error(f"Erro ao gerar recomendações: {e}")
 
# -------------------- Perguntas do usuário ao Gemini --------------------
st.markdown("---")
st.header("💬 Pergunte ao Gemini sobre os dispositivos ou eficiência geral")
user_input = st.text_input("Digite sua pergunta:")
if st.button("Enviar pergunta") and user_input:
    try:
        contexto = df.to_dict(orient="records")
        prompt = (
            "Considere os seguintes dispositivos e dados:\n"
            f"{contexto}\n\nPergunta: {user_input}\n"
            "Forneça informações precisas, mas se necessário use conhecimento geral de mercado ou boas práticas, "
            "indicando claramente quando a resposta é uma estimativa."
        )
        resposta = llm.generate_content(prompt)
        st.markdown(f"**Resposta do Gemini:** {resposta.text}")
    except Exception as e:
        st.error(f"Erro ao processar a pergunta: {e}")
