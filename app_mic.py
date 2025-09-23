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

def firebase_put(path: str, data: dict):
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    r = requests.put(url, json=data, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_tomada(device_id: str):
    try:
        data = firebase_get(f"/tomadas/{device_id}")
        if not isinstance(data, dict):
            return None
        ts = data.get("ts")
        t = datetime.fromtimestamp(ts, tz=timezone.utc) if isinstance(ts, (int,float)) else datetime.now(timezone.utc)
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
        st.warning(f"Não foi possível ler /tomadas/{device_id} do Firebase: {e}")
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

# -------------------- Funções auxiliares --------------------
def get_pending_device_calls():
    """Busca chamados de dispositivos pendentes no Firebase."""
    try:
        calls = firebase_get("/device_calls")
        if calls:
            registered_devices = st.session_state.df_devices['Device_ID'].tolist() if 'df_devices' in st.session_state and not st.session_state.df_devices.empty else []
            pending_ids = [dev_id for dev_id in calls.keys() if calls[dev_id] and calls[dev_id].get('status') == 'pending_registration' and dev_id not in registered_devices]
            return pending_ids
        return []
    except Exception as e:
        st.warning(f"Não foi possível buscar chamados de dispositivos: {e}")
        return []

def register_new_device(device_id, nome_aparelho, prioridade, nome_conectado, modelo_dispositivo):
    """Adiciona um novo dispositivo ao DataFrame e ao Excel."""
    new_device_data = {
        "Device_ID": device_id,
        "Dispositivo": nome_aparelho,
        "Prioridade": prioridade,
        "Nome_Conectado": nome_conectado,
        "Modelo_Dispositivo": modelo_dispositivo,
        "time": datetime.now(timezone.utc).isoformat(), # Timestamp de registro
        "Voltage": 0.0, # Valores iniciais, serão atualizados pelo Firebase
        "Current": 0.0,
        "Power": 0.0,
        "Energy": 0.0,
        "Frequency": 0.0,
        "PF": 0.0,
    }

    # Carrega o DataFrame atual (ou cria um novo se não existir)
    if 'df_devices' not in st.session_state or st.session_state.df_devices.empty:
        st.session_state.df_devices = pd.DataFrame(columns=[
            "Device_ID", "Dispositivo", "Prioridade", "Nome_Conectado", "Modelo_Dispositivo",
            "time", "Voltage", "Current", "Power", "Energy", "Frequency", "PF"
        ])

    # Adiciona o novo dispositivo
    # Verifica se o dispositivo já existe para evitar duplicatas
    if device_id not in st.session_state.df_devices['Device_ID'].values:
        st.session_state.df_devices = pd.concat([st.session_state.df_devices, pd.DataFrame([new_device_data])], ignore_index=True)
    else:
        st.warning(f"Dispositivo com ID {device_id} já está registrado. Atualizando informações.")
        # Atualiza as informações do dispositivo existente
        idx = st.session_state.df_devices[st.session_state.df_devices['Device_ID'] == device_id].index[0]
        for key, value in new_device_data.items():
            if key != "Device_ID": # Não atualiza o ID
                st.session_state.df_devices.loc[idx, key] = value

    # Salva no Excel
    try:
        st.session_state.df_devices.to_excel("dados_consumo_mic.xlsx", index=False)
        st.success(f"Dispositivo '{nome_aparelho}' (ID: {device_id}) registrado/atualizado e salvo no Excel!")
        # Opcional: Remover o chamado do Firebase após o registro
        firebase_put(f"/device_calls/{device_id}", None) # Define como null para remover
    except Exception as e:
        st.error(f"Erro ao salvar o novo dispositivo no Excel: {e}")

def atualizar_dados():
    df_local = pd.DataFrame()
    EXCEL_FILE_NAME = "dados_consumo_mic.xlsx"

    # 1. Carregar dispositivos registrados do Excel (base de todos os dispositivos conhecidos)
    if os.path.exists(EXCEL_FILE_NAME):
        try:
            df_registered = pd.read_excel(EXCEL_FILE_NAME)
            # Garante que as colunas de dados numéricos sejam float
            for col in ["Voltage", "Current", "Power", "Energy", "Frequency", "PF"]:
                if col in df_registered.columns:
                    df_registered[col] = pd.to_numeric(df_registered[col], errors='coerce').fillna(0.0)
            df_registered["time"] = pd.to_datetime(df_registered["time"], errors="coerce")
            df_local = df_registered.copy()
        except Exception as e:
            st.warning(f"Erro ao carregar dados do Excel: {e}. Iniciando com DataFrame vazio.")
            df_local = pd.DataFrame(columns=[
                "Device_ID", "Dispositivo", "Prioridade", "Nome_Conectado", "Modelo_Dispositivo",
                "time", "Voltage", "Current", "Power", "Energy", "Frequency", "PF"
            ])
    else:
        # Se o Excel não existe, cria um DataFrame vazio com as colunas esperadas
        df_local = pd.DataFrame(columns=[
            "Device_ID", "Dispositivo", "Prioridade", "Nome_Conectado", "Modelo_Dispositivo",
            "time", "Voltage", "Current", "Power", "Energy", "Frequency", "PF"
        ])

    # 2. Atualizar os dados de monitoramento para cada dispositivo registrado a partir do Firebase
    updated_rows = []
    for index, row in df_local.iterrows():
        device_id = row.get("Device_ID")
        if device_id:
            firebase_data = fetch_tomada(device_id) # fetch_tomada já usa Device_ID
            if firebase_data:
                # Atualiza apenas as colunas de monitoramento
                row["time"] = pd.to_datetime(firebase_data["time"])
                row["Voltage"] = float(firebase_data["Voltage"])
                row["Current"] = float(firebase_data["Current"])
                row["Power"] = float(firebase_data["Power"])
                row["Energy"] = float(firebase_data["Energy"])
                row["Frequency"] = float(firebase_data["Frequency"])
                row["PF"] = float(firebase_data["PF"])
        updated_rows.append(row)

    df_local = pd.DataFrame(updated_rows)

    # 3. Adicionar mock_data se não houver dispositivos registrados (para demonstração inicial)
    if df_local.empty:
        mock_data = [
            {"time": "2025-09-14T08:00:00", "Dispositivo": "Secador de cabelo", "Voltage": 220, "Current": 7.6, "Power": 1674, "Energy": 0.47, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_secador", "Prioridade": "Moderada", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T09:00:00", "Dispositivo": "Laptop", "Voltage": 220, "Current": 2.2, "Power": 502, "Energy": 0.14, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_laptop", "Prioridade": "Mínima", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T10:00:00", "Dispositivo": "Geladeira", "Voltage": 220, "Current": 0.8, "Power": 176, "Energy": 0.23, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_geladeira", "Prioridade": "Máxima", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T11:00:00", "Dispositivo": "Televisão", "Voltage": 220, "Current": 1.1, "Power": 251, "Energy": 0.42, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_televisao", "Prioridade": "Moderada", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
        ]
        df_local = pd.concat([df_local, pd.DataFrame(mock_data)], ignore_index=True)
        df_local["time"] = pd.to_datetime(df_local["time"], errors="coerce")

    # Garante que o DataFrame esteja na session_state para ser acessível globalmente
    st.session_state.df_devices = df_local.copy()
    return df_local

def gerar_contexto_resumido(df_input):
    # Apenas seleciona colunas essenciais para enviar ao LLM
    # Adicione as novas colunas se o Gemini precisar delas
    return df_input[["Dispositivo","Voltage","Current","Power","Energy","PF", "Prioridade", "Nome_Conectado", "Modelo_Dispositivo"]].to_dict(orient="records")

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e recomendações de consumo de energia de dispositivos domésticos")

# Inicializa session_state se necessário
if 'df_devices' not in st.session_state:
    st.session_state.df_devices = pd.DataFrame()

# Atualiza dados a cada refresh
df = atualizar_dados()

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    auto_refresh = st.checkbox("Atualizar automaticamente (5s)", value=True)
    if auto_refresh:
        st_autorefresh(interval=5000, key="datarefresh")
    if st.button("💾 Salvar no Excel"):
        try:
            st.session_state.df_devices.to_excel("dados_consumo_mic.xlsx", index=False)
            st.sidebar.success("Dados salvos com sucesso!")
        except Exception as e:
            st.sidebar.error(f"Erro ao salvar: {e}")
    st.download_button(
        "⬇ Baixar CSV",
        st.session_state.df_devices.to_csv(index=False).encode("utf-8"),
        f"goodwe_{date.today()}.csv",
        "text/csv"
    )

    st.markdown("---")
    st.header("Gerenciamento de Dispositivos")

    pending_calls = get_pending_device_calls()

    if pending_calls:
        st.subheader("Chamados Pendentes")
        selected_device_id = st.selectbox("Selecione um dispositivo para registrar:", pending_calls)

        with st.form("form_register_device"):
            st.write(f"Registrando dispositivo com ID: **{selected_device_id}**")
            nome_aparelho = st.text_input("Nome do Aparelho (obrigatório)", key=f"nome_aparelho_{selected_device_id}")
            prioridade = st.selectbox("Ordem de Prioridade", ["Máxima", "Moderada", "Mínima"], key=f"prioridade_{selected_device_id}")
            nome_conectado = st.text_input("Nome do Dispositivo Conectado (opcional)", key=f"nome_conectado_{selected_device_id}")
            modelo_dispositivo = st.text_input("Modelo do Dispositivo (opcional)", key=f"modelo_dispositivo_{selected_device_id}")

            submitted = st.form_submit_button("Registrar Dispositivo")
            if submitted:
                if nome_aparelho:
                    register_new_device(selected_device_id, nome_aparelho, prioridade, nome_conectado, modelo_dispositivo)
                    st.experimental_rerun() # Recarrega para atualizar a lista de chamados e dispositivos
                else:
                    st.error("O nome do aparelho é obrigatório.")
    else:
        st.info("Nenhum chamado de dispositivo pendente.")

# -------------------- KPIs --------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tensão média (V)", f"{st.session_state.df_devices['Voltage'].mean():.2f}")
col2.metric("Corrente total (A)", f"{st.session_state.df_devices['Current'].sum():.2f}")
col3.metric("Potência total (W)", f"{st.session_state.df_devices['Power'].sum():.2f}")
col4.metric("Energia total (kWh)", f"{st.session_state.df_devices['Energy'].sum():.3f}")

# -------------------- Gráficos --------------------
left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(st.session_state.df_devices, x="Dispositivo", y="Power", color="Dispositivo", title="Potência (W)"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(st.session_state.df_devices, x="Dispositivo", y="Energy", color="Dispositivo", title="Energia (kWh)"), use_container_width=True)

# -------------------- Tabela --------------------
with st.expander("📊 Ver tabela completa"):
    df_display = st.session_state.df_devices.copy()
    df_display["time"] = pd.to_datetime(df_display["time"], errors="coerce")
    df_display["time"] = df_display["time"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(df_display, width="stretch", hide_index=True)

# -------------------- Gemini: Alertas --------------------
st.markdown("---")
st.header("💬 Alertas e recomendações do Gemini")
if st.button("Gerar alertas e recomendações"):
    contexto = gerar_contexto_resumido(st.session_state.df_devices)
    prompt = f"Analise os dispositivos:\n{contexto}\n\nForneça alertas e recomendações para economizar energia."
    resposta = llm.generate_content(prompt)
    
    tts = gTTS(resposta.text, lang="pt")
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    st.audio(audio_buffer, format="audio/mp3")
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
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_bytes)
            audio_path = temp_audio.name
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            pergunta_usuario = recognizer.recognize_google(audio_data, language="pt-BR")
        st.write(f"**Você disse:** {pergunta_usuario}")
    except Exception as e:
        st.warning(f"Não foi possível reconhecer o áudio: {e}")
elif pergunta_texto:
    pergunta_usuario = pergunta_texto
    st.write(f"**Você escreveu:** {pergunta_usuario}")

if pergunta_usuario:
    contexto = gerar_contexto_resumido(st.session_state.df_devices)
    prompt = f"Considere os dispositivos:\n{contexto}\n\nPergunta: {pergunta_usuario}"
    resposta = llm.generate_content(prompt)

    tts = gTTS(resposta.text, lang="pt")
    audio_out = io.BytesIO()
    tts
