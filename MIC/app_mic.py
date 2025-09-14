import os
import requests
import streamlit as st
import pandas as pd
from datetime import date, datetime, timezone
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
from audio_recorder_streamlit import audio_recorder
import tempfile
import speech_recognition as sr
from gtts import gTTS
import io
import numpy as np

# -------------------- Carregar .env --------------------
load_dotenv()
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEN_API_KEY)

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://mic-9d88e-default-rtdb.firebaseio.com").rstrip("/")
FIREBASE_AUTH = os.getenv("FIREBASE_AUTH", "")

# -------------------- Firebase --------------------
def firebase_get(path: str):
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_tomada(tomada: str):
    try:
        data = firebase_get(f"/tomadas/{tomada}")
        if not isinstance(data, dict):
            return None
        ts = data.get("ts")
        if isinstance(ts, (int, float)):
            t = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            t = datetime.now(timezone.utc)
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
        st.warning(f"Não foi possível ler /tomadas/{tomada} do Firebase: {e}")
        return None

# -------------------- Configuração do Gemini --------------------
MODELO_ESCOLHIDO = "gemini-1.5-flash"
prompt_sistema = """
Você é um assistente especializado em monitoramento de dispositivos elétricos domésticos.
Seu objetivo é analisar dados de consumo de energia e fornecer respostas precisas,
breves e confiáveis sobre os dispositivos, como potência, energia consumida, corrente, tensão, etc.
Forneça alertas e recomendações para economizar energia com base nos dados apresentados.
Se a pergunta não puder ser respondida apenas com os dados fornecidos, você pode fornecer informações gerais baseadas em boas práticas ou conhecimento de mercado,
indicando claramente quando a resposta é uma estimativa ou referência externa.
"""
llm = genai.GenerativeModel(model_name=MODELO_ESCOLHIDO, system_instruction=prompt_sistema)

# -------------------- Mock inicial --------------------
mock_data = [
    {"time": "2025-09-14T08:00:00", "Dispositivo": "Secador de cabelo", "Voltage": 220, "Current": 7.6, "Power": 1674, "Energy": 0.47, "Frequency": 60.0, "PF": 1},
    {"time": "2025-09-14T09:00:00", "Dispositivo": "Laptop", "Voltage": 220, "Current": 2.2, "Power": 502, "Energy": 0.14, "Frequency": 60.0, "PF": 1},
    {"time": "2025-09-14T10:00:00", "Dispositivo": "Geladeira", "Voltage": 220, "Current": 0.8, "Power": 176, "Energy": 0.23, "Frequency": 60.0, "PF": 1},
    {"time": "2025-09-14T11:00:00", "Dispositivo": "Televisão", "Voltage": 220, "Current": 1.1, "Power": 251, "Energy": 0.42, "Frequency": 60.0, "PF": 1},
    {"time": "2025-09-14T12:00:00", "Dispositivo": "Micro-ondas", "Voltage": 220, "Current": 5.0, "Power": 1000, "Energy": 0.20, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-14T13:00:00", "Dispositivo": "Ventilador", "Voltage": 220, "Current": 0.3, "Power": 35, "Energy": 0.02, "Frequency": 60.0, "PF": 0.95},
    {"time": "2025-09-14T14:00:00", "Dispositivo": "Ar-condicionado", "Voltage": 220, "Current": 3.5, "Power": 770, "Energy": 0.25, "Frequency": 60.0, "PF": 0.88},
    {"time": "2025-09-14T15:00:00", "Dispositivo": "Cafeteira", "Voltage": 220, "Current": 2.0, "Power": 250, "Energy": 0.07, "Frequency": 60.0, "PF": 0.9},
    {"time": "2025-09-14T16:00:00", "Dispositivo": "Ferro de passar", "Voltage": 220, "Current": 4.0, "Power": 500, "Energy": 0.15, "Frequency": 60.0, "PF": 0.9},
]
df = pd.DataFrame(mock_data)
df["time"] = pd.to_datetime(df["time"], errors="coerce")

# -------------------- Atualiza com Firebase --------------------
tomadas = ["tomada1", "tomada2", "tomada3", "tomada4"]
nomes_dispositivos = ["Secador de cabelo", "Laptop", "Geladeira", "Televisão"]

for tomada, nome in zip(tomadas, nomes_dispositivos):
    data = fetch_tomada(tomada)
    if data:
        mask = df["Dispositivo"].str.lower() == nome.lower()
        df.loc[mask, ["time","Voltage","Current","Power","Energy","Frequency","PF"]] = [
            pd.to_datetime(data["time"]),
            float(data["Voltage"]),
            float(data["Current"]),
            float(data["Power"]),
            float(data["Energy"]),
            float(data["Frequency"]),
            float(data["PF"]),
        ]

# -------------------- Histórico em Excel --------------------
EXCEL_FILE_NAME = "dados_consumo_mic.xlsx"
if os.path.exists(EXCEL_FILE_NAME):
    try:
        df_existing = pd.read_excel(EXCEL_FILE_NAME)
        df_existing["time"] = pd.to_datetime(df_existing["time"], errors="coerce")
        df = pd.concat([df_existing, df]).drop_duplicates(subset=["time", "Dispositivo"]).reset_index(drop=True)
        st.sidebar.success(f"Dados carregados de {EXCEL_FILE_NAME}")
    except Exception as e:
        st.sidebar.warning(f"Erro ao carregar histórico: {e}")
else:
    st.sidebar.info("Arquivo histórico não encontrado. Um novo será criado.")

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant - Projeto de Aparelhos", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e recomendações de consumo de energia de dispositivos domésticos")

with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    auto_refresh = st.checkbox("Atualizar automaticamente (5s)", value=True)
    if auto_refresh:
        st_autorefresh(interval=5000, key="datarefresh")
    if st.button("💾 Salvar no Excel"):
        try:
            df.to_excel(EXCEL_FILE_NAME, index=False)
            st.sidebar.success(f"Dados salvos em {EXCEL_FILE_NAME}")
        except Exception as e:
            st.sidebar.error(f"Erro ao salvar: {e}")
    st.download_button("⬇ Baixar CSV", df.to_csv(index=False).encode("utf-8"), f"goodwe_{date.today()}.csv", "text/csv")

# -------------------- KPIs --------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tensão média (V)", f"{df['Voltage'].mean():.2f}")
col2.metric("Corrente total (A)", f"{df['Current'].sum():.2f}")
col3.metric("Potência total (W)", f"{df['Power'].sum():.2f}")
col4.metric("Energia total (kWh)", f"{df['Energy'].sum():.3f}")

# -------------------- Gráficos por dispositivo --------------------
left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(df, x="Dispositivo", y="Power", color="Dispositivo", title="Potência (W)"), width="stretch")
with right:
    st.plotly_chart(px.bar(df, x="Dispositivo", y="Energy", color="Dispositivo", title="Energia (kWh)"), width="stretch")

# -------------------- Tabela --------------------
with st.expander("📊 Ver tabela completa"):
    df_display = df.copy()
    df_display["time"] = pd.to_datetime(df_display["time"], errors="coerce")
    df_display["time"] = df_display["time"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(df_display, width="stretch", hide_index=True)

# -------------------- Gemini: Alertas --------------------
st.markdown("---")
st.header("💬 Alertas e recomendações do Gemini")
if st.button("Gerar alertas e recomendações"):
    contexto = df.to_dict(orient="records")
    prompt = f"Analise os dispositivos:\n{contexto}\n\nForneça alertas e recomendações para economizar energia."
    resposta = llm.generate_content(prompt)

    tts = gTTS(resposta.text, lang="pt")
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)

    st.audio(audio_bytes, format="audio/mp3")
    st.markdown(f"**Alertas e recomendações:** {resposta.text}")

# -------------------- Gemini: Perguntas Texto/Voz --------------------
st.markdown("---")
st.header("🎙️ Pergunte ao Gemini")

col_input, col_audio = st.columns([3,1])
with col_input:
    pergunta_texto = st.text_input("Digite sua pergunta:")
with col_audio:
    audio_bytes = audio_recorder()

pergunta_usuario = None
if audio_bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        audio_path = temp_audio.name
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        pergunta_usuario = recognizer.recognize_google(audio_data, language="pt-BR")
    st.write(f"**Você disse:** {pergunta_usuario}")
elif pergunta_texto:
    pergunta_usuario = pergunta_texto
    st.write(f"**Você escreveu:** {pergunta_usuario}")

if pergunta_usuario:
    contexto = df.to_dict(orient="records")
    prompt = f"Considere os dispositivos:\n{contexto}\n\nPergunta: {pergunta_usuario}"
    resposta = llm.generate_content(prompt)

    tts = gTTS(resposta.text, lang="pt")
    audio_out = io.BytesIO()
    tts.write_to_fp(audio_out)

    st.audio(audio_out, format="audio/mp3")
    st.markdown(f"**Resposta do Gemini:** {resposta.text}")

# -------------------- Gráfico histórico geral com mock (30 dias) --------------------
st.markdown("---")
st.header("📈 Histórico geral de energia consumida (últimos 30 dias)")

dispositivos = df['Dispositivo'].unique()
dias = pd.date_range(start=date.today().replace(day=1), periods=30)

# Criar DataFrame histórico mockado
df_historico = pd.DataFrame()
for disp in dispositivos:
    energia_mock = np.random.uniform(low=0.05, high=0.5, size=len(dias))
    df_temp = pd.DataFrame({
        "time": dias,
        "Dispositivo": disp,
        "Energy": energia_mock
    })
    df_historico = pd.concat([df_historico, df_temp], ignore_index=True)

fig_hist = px.line(
    df_historico,
    x="time",
    y="Energy",
    color="Dispositivo",
    markers=True,
    title="Energia consumida por dispositivo nos últimos 30 dias"
)
fig_hist.update_layout(
    xaxis_title="Data",
    yaxis_title="Energia consumida (kWh)"
)
st.plotly_chart(fig_hist, use_container_width=True)

# -------------------- Explicação das métricas (FINAL) --------------------
st.markdown("---")
with st.expander("ℹ️ O que são estas informações?"):
    st.markdown("""
O GoodWe Assistant monitora os seguintes parâmetros de consumo elétrico para cada dispositivo:

- **Tensão (Voltage - V):** A diferença de potencial aplicada ao dispositivo.
- **Corrente (Current - A):** Quantidade de elétrons circulando pelo dispositivo.
- **Potência (Power - W):** Energia consumida por unidade de tempo (W = V x A).
- **Energia (Energy - kWh):** Quantidade total de energia consumida pelo dispositivo.
- **Frequência (Frequency - Hz):** Frequência da rede elétrica.
- **Fator de Potência (PF):** Eficiência com que a energia elétrica está sendo usada.  
  Valores próximos de 1 indicam uso eficiente; valores baixos indicam desperdício.

💡 **Dica:** Dispositivos com alto consumo de potência ou energia acumulada podem impactar significativamente a conta de luz.
Use os gráficos e alertas do Gemini para identificar picos de consumo e otimizar seu uso de energia.
""")
