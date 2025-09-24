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
import json

# -------------------- Carregar .env --------------------
load_dotenv()
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
if GEN_API_KEY:
    genai.configure(api_key=GEN_API_KEY)

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://mic-9d88e-default-rtdb.firebaseio.com").rstrip("/")
FIREBASE_AUTH = os.getenv("FIREBASE_AUTH", "")

# -------------------- Inicialização da sessão --------------------
if 'df_devices' not in st.session_state:
    st.session_state.df_devices = pd.DataFrame()

# -------------------- Firebase --------------------
def firebase_get(path: str):
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    r = requests.get(url, params=params, timeout=10)
    if r.status_code == 200:
        try:
            return r.json()
        except Exception:
            return None
    else:
        r.raise_for_status()

def firebase_put(path: str, data: dict):
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    try:
        if data is None:
            r = requests.delete(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        else:
            headers = {"Content-Type": "application/json"}
            payload = json.dumps(data, default=str)
            r = requests.put(url, data=payload, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise

def firebase_post(path: str, data: dict):
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    try:
        headers = {"Content-Type": "application/json"}
        payload = json.dumps(data, default=str)
        r = requests.post(url, data=payload, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise

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
if GEN_API_KEY:
    llm = genai.GenerativeModel(model_name=MODELO_ESCOLHIDO, system_instruction=prompt_sistema)
else:
    llm = None

# -------------------- Funções auxiliares --------------------
def get_pending_device_calls():
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

# -------------------- Registro e atualização de dispositivos --------------------
def register_new_device(device_id, nome_aparelho, prioridade, nome_conectado, modelo_dispositivo):
    new_device_data = {
        "Device_ID": device_id,
        "Dispositivo": nome_aparelho,
        "Prioridade": prioridade,
        "Nome_Conectado": nome_conectado,
        "Modelo_Dispositivo": modelo_dispositivo,
        "time": datetime.now(timezone.utc).isoformat(),
        "Voltage": 0.0,
        "Current": 0.0,
        "Power": 0.0,
        "Energy": 0.0,
        "Frequency": 0.0,
        "PF": 0.0,
    }

    if st.session_state.df_devices.empty:
        st.session_state.df_devices = pd.DataFrame(columns=list(new_device_data.keys()))

    if device_id not in st.session_state.df_devices['Device_ID'].values:
        st.session_state.df_devices = pd.concat([st.session_state.df_devices, pd.DataFrame([new_device_data])], ignore_index=True)
    else:
        idx = st.session_state.df_devices[st.session_state.df_devices['Device_ID']==device_id].index[0]
        for key, value in new_device_data.items():
            if key != "Device_ID":
                st.session_state.df_devices.loc[idx, key] = value

    # Salvar Excel
    try:
        st.session_state.df_devices.to_excel("dados_consumo_mic.xlsx", index=False)
        st.success(f"✅ Dispositivo '{nome_aparelho}' registrado/atualizado e salvo no Excel!")
        try:
            firebase_put(f"/device_calls/{device_id}", None)
        except Exception as e:
            st.warning(f"Não foi possível remover o chamado no Firebase: {e}")
        try:
            firebase_post(f"/historico/{device_id}", new_device_data)
        except Exception as e:
            st.warning(f"Não foi possível salvar no histórico do Firebase: {e}")
        
        # Atualizar dados imediatamente
        st.session_state.df_devices = atualizar_dados()
        st.rerun()
        
    except Exception as e:
        st.error(f"Erro ao salvar dispositivo no Excel: {e}")

def atualizar_dados():
    df_local = pd.DataFrame()
    EXCEL_FILE_NAME = "dados_consumo_mic.xlsx"

    if os.path.exists(EXCEL_FILE_NAME):
        try:
            df_registered = pd.read_excel(EXCEL_FILE_NAME)
            for col in ["Voltage","Current","Power","Energy","Frequency","PF"]:
                if col in df_registered.columns:
                    df_registered[col] = pd.to_numeric(df_registered[col], errors='coerce').fillna(0.0)
            df_registered["time"] = pd.to_datetime(df_registered["time"], errors="coerce")
            df_local = df_registered.copy()
        except Exception as e:
            st.warning(f"Erro ao carregar dados do Excel: {e}")
            df_local = pd.DataFrame(columns=[
                "Device_ID","Dispositivo","Prioridade","Nome_Conectado","Modelo_Dispositivo",
                "time","Voltage","Current","Power","Energy","Frequency","PF"
            ])
    else:
        df_local = pd.DataFrame(columns=[
            "Device_ID","Dispositivo","Prioridade","Nome_Conectado","Modelo_Dispositivo",
            "time","Voltage","Current","Power","Energy","Frequency","PF"
        ])

    updated_rows = []
    for index, row in df_local.iterrows():
        device_id = row.get("Device_ID")
        if device_id:
            firebase_data = fetch_tomada(device_id)
            if firebase_data:
                row["time"] = pd.to_datetime(firebase_data["time"])
                row["Voltage"] = float(firebase_data["Voltage"])
                row["Current"] = float(firebase_data["Current"])
                row["Power"] = float(firebase_data["Power"])
                row["Energy"] = float(firebase_data["Energy"])
                row["Frequency"] = float(firebase_data["Frequency"])
                row["PF"] = float(firebase_data["PF"])
        updated_rows.append(row)

    df_local = pd.DataFrame(updated_rows)

    if df_local.empty:
        mock_data = [
            {"time": "2025-09-14T08:00:00", "Dispositivo": "Secador de cabelo", "Voltage": 220, "Current": 7.6, "Power": 1674, "Energy": 0.47, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_secador", "Prioridade": "Moderada", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T09:00:00", "Dispositivo": "Laptop", "Voltage": 220, "Current": 2.2, "Power": 502, "Energy": 0.14, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_laptop", "Prioridade": "Mínima", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T10:00:00", "Dispositivo": "Geladeira", "Voltage": 220, "Current": 0.8, "Power": 176, "Energy": 0.23, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_geladeira", "Prioridade": "Máxima", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
            {"time": "2025-09-14T11:00:00", "Dispositivo": "Televisão", "Voltage": 220, "Current": 1.1, "Power": 251, "Energy": 0.42, "Frequency": 60.0, "PF": 1, "Device_ID": "mock_televisao", "Prioridade": "Moderada", "Nome_Conectado": "", "Modelo_Dispositivo": ""},
        ]
        df_local = pd.DataFrame(mock_data)
        df_local["time"] = pd.to_datetime(df_local["time"], errors="coerce")

    return df_local

def gerar_contexto_resumido(df_input):
    cols = ["Dispositivo","Voltage","Current","Power","Energy","PF","Prioridade","Nome_Conectado","Modelo_Dispositivo"]
    existing_cols = [c for c in cols if c in df_input.columns]
    return df_input[existing_cols].to_dict(orient="records")

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="GoodWe Assistant", layout="wide", page_icon="⚡")
st.title("⚡ GoodWe Assistant — Projeto de Monitoramento de Aparelhos")
st.caption("Visualização e recomendações de consumo de energia de dispositivos domésticos")

# Atualiza dados apenas se necessário
if st.session_state.df_devices.empty:
    st.session_state.df_devices = atualizar_dados()

df = st.session_state.df_devices.copy()

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("Configurações")
    data_ref = st.date_input("Data de referência", value=date.today())
    auto_refresh = st.checkbox("Atualizar automaticamente (5s)", value=True)
    if auto_refresh:
        st_autorefresh(interval=5000, key="datarefresh")
    
    # Botão de salvar - com verificação de segurança
    if st.button("💾 Salvar no Excel"):
        if not st.session_state.df_devices.empty:
            try:
                st.session_state.df_devices.to_excel("dados_consumo_mic.xlsx", index=False)
                st.sidebar.success("Dados salvos com sucesso!")
            except Exception as e:
                st.sidebar.error(f"Erro ao salvar: {e}")
        else:
            st.sidebar.warning("Nenhum dado para salvar.")
    
    # Botão de download - com verificação de segurança
    if not st.session_state.df_devices.empty:
        csv_data = st.session_state.df_devices.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Baixar CSV",
            csv_data,
            f"goodwe_{date.today()}.csv",
            "text/csv"
        )
    else:
        st.sidebar.info("Nenhum dado disponível para download")

    st.markdown("---")
    st.header("Gerenciamento de Dispositivos")

    # Registro manual
    with st.expander("🛠️ Registrar dispositivo manualmente"):
        device_id_manual = st.text_input("ID do dispositivo (manual)")
        nome_aparelho_manual = st.text_input("Nome do Aparelho (manual)")
        prioridade_manual = st.selectbox("Ordem de Prioridade (manual)", ["Máxima","Moderada","Mínima"], key="prioridade_manual")
        nome_conectado_manual = st.text_input("Nome do Dispositivo Conectado (manual)")
        modelo_dispositivo_manual = st.text_input("Modelo do Dispositivo (manual)")

        if st.button("Registrar Manualmente"):
            if device_id_manual and nome_aparelho_manual:
                try:
                    register_new_device(
                        device_id=device_id_manual,
                        nome_aparelho=nome_aparelho_manual,
                        prioridade=prioridade_manual,
                        nome_conectado=nome_conectado_manual,
                        modelo_dispositivo=modelo_dispositivo_manual
                    )
                except Exception as e:
                    st.error(f"Erro ao registrar dispositivo manualmente: {e}")
            else:
                st.error("ID e Nome do aparelho são obrigatórios para registro manual.")

# -------------------- Chamados pendentes --------------------
pending_calls = get_pending_device_calls()
if pending_calls:
    st.subheader("Chamados Pendentes")
    selected_device_id = st.selectbox("Selecione um dispositivo para registrar:", pending_calls)
    with st.form("form_register_device"):
        st.write(f"Registrando dispositivo com ID: **{selected_device_id}**")
        nome_aparelho = st.text_input("Nome do Aparelho (obrigatório)", key=f"nome_aparelho_{selected_device_id}")
        prioridade = st.selectbox("Ordem de Prioridade", ["Máxima","Moderada","Mínima"], key=f"prioridade_{selected_device_id}")
        nome_conectado = st.text_input("Nome do Dispositivo Conectado (opcional)", key=f"nome_conectado_{selected_device_id}")
        modelo_dispositivo = st.text_input("Modelo do Dispositivo (opcional)", key=f"modelo_dispositivo_{selected_device_id}")

        submitted = st.form_submit_button("Registrar Dispositivo")
        if submitted:
            if nome_aparelho:
                try:
                    register_new_device(selected_device_id, nome_aparelho, prioridade, nome_conectado, modelo_dispositivo)
                except Exception as e:
                    st.error(f"Erro ao registrar dispositivo: {e}")
            else:
                st.error("O nome do aparelho é obrigatório.")
else:
    st.info("Nenhum chamado de dispositivo pendente.")

# -------------------- KPIs --------------------
col1,col2,col3,col4 = st.columns(4)
try:
    tension_mean = st.session_state.df_devices['Voltage'].mean() if not st.session_state.df_devices.empty else 0.0
    current_sum = st.session_state.df_devices['Current'].sum() if not st.session_state.df_devices.empty else 0.0
    power_sum = st.session_state.df_devices['Power'].sum() if not st.session_state.df_devices.empty else 0.0
    energy_sum = st.session_state.df_devices['Energy'].sum() if not st.session_state.df_devices.empty else 0.0
except Exception:
    tension_mean=current_sum=power_sum=energy_sum=0.0

col1.metric("Tensão média (V)", f"{tension_mean:.2f}")
col2.metric("Corrente total (A)", f"{current_sum:.2f}")
col3.metric("Potência total (W)", f"{power_sum:.2f}")
col4.metric("Energia total (kWh)", f"{energy_sum:.3f}")

# -------------------- Gráficos --------------------
left,right = st.columns(2)
with left:
    try:
        if not st.session_state.df_devices.empty:
            st.plotly_chart(px.bar(st.session_state.df_devices, x="Dispositivo", y="Power", color="Dispositivo", title="Potência (W)"), use_container_width=True)
        else:
            st.info("Nenhum dado disponível para gráfico de potência.")
    except Exception:
        st.info("Gráfico de potência indisponível.")
with right:
    try:
        if not st.session_state.df_devices.empty:
            st.plotly_chart(px.bar(st.session_state.df_devices, x="Dispositivo", y="Energy", color="Dispositivo", title="Energia (kWh)"), use_container_width=True)
        else:
            st.info("Nenhum dado disponível para gráfico de energia.")
    except Exception:
        st.info("Gráfico de energia indisponível.")

# -------------------- Tabela --------------------
with st.expander("📊 Ver tabela completa"):
    if not st.session_state.df_devices.empty:
        df_display = st.session_state.df_devices.copy()
        df_display["time"] = pd.to_datetime(df_display["time"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info("Nenhum dado disponível para exibição.")

# -------------------- Gemini: Alertas --------------------
st.markdown("---")
st.header("💬 Alertas e recomendações do Gemini")
if st.button("Gerar alertas e recomendações"):
    if not st.session_state.df_devices.empty:
        contexto = gerar_contexto_resumido(st.session_state.df_devices)
        prompt = f"Analise os dispositivos:\n{contexto}\n\nForneça alertas e recomendações para economizar energia."
        try:
            if llm:
                resposta = llm.generate_content(prompt)
                texto_resposta = resposta.text
            else:
                texto_resposta = "Gemini não está configurado (GEMINI_API_KEY ausente)."
        except Exception as e:
            texto_resposta = f"Erro ao gerar resposta do Gemini: {e}"

        # Geração de áudio (TTS)
        try:
            tts = gTTS(texto_resposta, lang="pt")
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            st.audio(audio_buffer, format="audio/mp3")
        except Exception as e:
            st.warning(f"Não foi possível gerar áudio: {e}")

        st.markdown(f"**Alertas e recomendações:** {texto_resposta}")
    else:
        st.warning("Nenhum dado disponível para análise.")

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
    if not st.session_state.df_devices.empty:
        contexto = gerar_contexto_resumido(st.session_state.df_devices)
        prompt = f"Considere os dispositivos:\n{contexto}\n\nPergunta: {pergunta_usuario}"
        try:
            if llm:
                resposta = llm.generate_content(prompt)
                texto_resposta = resposta.text
            else:
                texto_resposta = "Gemini não está configurado (GEMINI_API_KEY ausente)."
        except Exception as e:
            texto_resposta = f"Erro ao consultar Gemini: {e}"

        # TTS e saída de áudio
        try:
            tts = gTTS(texto_resposta, lang="pt")
            audio_out = io.BytesIO()
            tts.write_to_fp(audio_out)
            audio_out.seek(0)
            st.audio(audio_out, format="audio/mp3")
        except Exception as e:
            st.warning(f"Não foi possível gerar áudio: {e}")

        st.markdown(f"**Resposta do Gemini:** {texto_resposta}")
    else:
        st.warning("Nenhum dado disponível para consulta.")

# -------------------- Gráfico histórico (agora real) --------------------
st.markdown("---")
st.header("📈 Histórico geral de energia consumida (últimos registros)")

try:
    dispositivos = st.session_state.df_devices['Device_ID'].unique() if not st.session_state.df_devices.empty else []
except Exception:
    dispositivos = []

df_historico = pd.DataFrame()
for dev in dispositivos:
    try:
        dados_hist = firebase_get(f"/historico/{dev}")
        if dados_hist and isinstance(dados_hist, dict):
            temp_df = pd.DataFrame(dados_hist).T.reset_index(drop=True)
            # normalizar colunas
            if 'time' in temp_df.columns:
                temp_df['time'] = pd.to_datetime(temp_df['time'], errors='coerce')
            else:
                temp_df['time'] = pd.NaT
            if 'Energy' in temp_df.columns:
                temp_df['Energy'] = pd.to_numeric(temp_df['Energy'], errors='coerce')
            else:
                temp_df['Energy'] = np.nan
            if 'Power' in temp_df.columns:
                temp_df['Power'] = pd.to_numeric(temp_df['Power'], errors='coerce')
            else:
                temp_df['Power'] = np.nan
            # garantir Dispositivo
            if 'Dispositivo' not in temp_df.columns:
                nome = st.session_state.df_devices.loc[st.session_state.df_devices['Device_ID']==dev, 'Dispositivo']
                temp_df['Dispositivo'] = nome.iloc[0] if len(nome)>0 else dev
            temp_df['Device_ID'] = dev
            df_historico = pd.concat([df_historico, temp_df], ignore_index=True)
    except Exception as e:
        st.warning(f"Erro ao buscar histórico do dispositivo {dev}: {e}")

# Se não houver histórico real, fallback para mock (30 dias)
if df_historico.empty:
    dias = pd.date_range(start=date.today().replace(day=1), periods=30)
    df_historico = pd.DataFrame()
    try:
        dispositivos_nomes = st.session_state.df_devices['Dispositivo'].unique() if not st.session_state.df_devices.empty else []
    except Exception:
        dispositivos_nomes = []
    for disp in dispositivos_nomes:
        energia_mock = np.random.uniform(low=0.05, high=0.5, size=len(dias))
        df_temp = pd.DataFrame({
            "time": dias,
            "Dispositivo": disp,
            "Energy": energia_mock
        })
        df_historico = pd.concat([df_historico, df_temp], ignore_index=True)

if not df_historico.empty:
    # limpando/ordenando
    if 'time' in df_historico.columns:
        df_historico = df_historico.sort_values('time')
    fig_hist = px.line(
        df_historico,
        x="time",
        y="Energy",
        color="Dispositivo",
        markers=True,
        title="Energia consumida por dispositivo (histórico)"
    )
    fig_hist.update_layout(
        xaxis_title="Data",
        yaxis_title="Energia consumida (kWh)"
    )
    st.plotly_chart(fig_hist, use_container_width=True)
else:
    st.info("Histórico indisponível.")

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
