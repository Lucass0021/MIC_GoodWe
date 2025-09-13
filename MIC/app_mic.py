import os
import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
import tempfile
import speech_recognition as sr
from gtts import gTTS
import io

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
Forneça alertas e recomendações para economizar energia com base nos dados apresentados.
Se a pergunta não puder ser respondida apenas com os dados fornecidos, você pode fornecer informações gerais baseadas em boas práticas ou conhecimento de mercado,
indicando claramente quando a resposta é uma estimativa ou referência externa.
"""

llm = genai.GenerativeModel(
    model_name=MODELO_ESCOLHIDO,
    system_instruction=prompt_sistema
)

# -------------------- Mock de dados --------------------
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

df = pd.DataFrame(mock_data)
df["time"] = pd.to_datetime(df["time"])

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant - Projeto de Aparelhos", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e recomendações de consumo de energia de dispositivos domésticos")

with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    st.info("O Gemini pode fornecer alertas, recomendações e responder perguntas sobre os dispositivos.")

# -------------------- KPIs gerais --------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tensão média (V)", f"{df['Voltage'].mean():.2f}")
col2.metric("Corrente total (A)", f"{df['Current'].sum():.2f}")
col3.metric("Potência total (W)", f"{df['Power'].sum():.2f}")
col4.metric("Energia total (kWh)", f"{df['Energy'].sum():.3f}")

# -------------------- Gráficos --------------------
left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(df, x="Dispositivo", y="Power", color="Dispositivo",
                           title="Potência Instantânea por Aparelho (W)"), use_container_width=True)

with right:
    st.plotly_chart(px.bar(df, x="Dispositivo", y="Energy", color="Dispositivo",
                           title="Energia Consumida por Aparelho (kWh)"), use_container_width=True)

# -------------------- Tabela --------------------
with st.expander("Ver tabela completa"):
    st.dataframe(df, use_container_width=True, hide_index=True)

# -------------------- Alertas e recomendações --------------------
st.markdown("---")
st.header("💬 Alertas e recomendações do Gemini")

if st.button("Gerar alertas e recomendações"):
    contexto = df.to_dict(orient="records")
    prompt = f"Analise os seguintes dispositivos e dados de consumo:\n{contexto}\n\nForneça alertas e recomendações para economizar energia."
    resposta = llm.generate_content(prompt)

    # Mostra alertas e recomendações em texto
    # 🔊 Mostra áudio logo abaixo
    tts = gTTS(resposta.text, lang="pt")
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)

    st.markdown("**🔊 Resposta em áudio do Gemini:**")
    st.audio(audio_bytes, format="audio/mp3")

    st.markdown(f"**Alertas e recomendações:** {resposta.text}")


# -------------------- Pergunta por texto ou voz --------------------
st.markdown("---")
st.header("🎙️ Pergunte ao Gemini (Texto ou Voz)")

col_input, col_audio = st.columns([3, 1])

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
    prompt = f"Considere os seguintes dispositivos:\n{contexto}\n\nPergunta: {pergunta_usuario}"
    resposta = llm.generate_content(prompt)

    # 🔊 Resposta em áudio logo abaixo da fala/escrita
    tts = gTTS(resposta.text, lang="pt")
    audio_out = io.BytesIO()
    tts.write_to_fp(audio_out)

    st.markdown("**🔊 Resposta em áudio do Gemini:**")
    st.audio(audio_out, format="audio/mp3")

    # Mostra resposta em texto
    st.markdown(f"**Resposta do Gemini:** {resposta.text}")
