import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone

# -------------------- Carregar variáveis de ambiente --------------------
load_dotenv()
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "").rstrip("/")
FIREBASE_AUTH = os.getenv("FIREBASE_AUTH", "")

if not GEN_API_KEY:
    raise ValueError("❌ Chave GEMINI_API_KEY não encontrada no .env")

genai.configure(api_key=GEN_API_KEY)

# -------------------- Firebase --------------------
def firebase_get(path: str):
    """Busca dados do Firebase no caminho especificado"""
    url = f"{FIREBASE_DB_URL}/{path.lstrip('/')}.json"
    params = {}
    if FIREBASE_AUTH:
        params["auth"] = FIREBASE_AUTH
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_devices_data():
    """Busca todos os dispositivos e seus dados de consumo"""
    try:
        data = firebase_get("/tomadas")
        if not isinstance(data, dict):
            return []
        devices = []
        for dev_id, values in data.items():
            ts = values.get("ts")
            t = datetime.fromtimestamp(ts, tz=timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
            devices.append({
                "Device_ID": dev_id,
                "time": t.isoformat(),
                "Voltage": float(values.get("Voltage", 0.0)),
                "Current": float(values.get("Current", 0.0)),
                "Power": float(values.get("Power", 0.0)),
                "Energy": float(values.get("Energy", 0.0)),
                "Frequency": float(values.get("Frequency", 60.0)),
                "PF": float(values.get("PF", 1.0)),
            })
        return devices
    except Exception as e:
        print(f"⚠ Erro ao buscar dados no Firebase: {e}")
        return []

# -------------------- Agente Gemini --------------------
def carregar_prompt():
    """Lê o prompt do arquivo prompt.txt"""
    with open("prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

def gerar_recomendacoes(devices):
    """Envia os dados dos dispositivos para o Gemini e retorna dicas"""
    if not devices:
        return "Nenhum dispositivo encontrado no Firebase."

    prompt_base = carregar_prompt()
    contexto = str(devices)
    prompt = f"{prompt_base}\n\nDados coletados:\n{contexto}"
    modelo = genai.GenerativeModel("models/gemini-2.5-pro")
    resposta = modelo.generate_content(prompt)
    return resposta.text

# -------------------- Execução principal --------------------
if __name__ == "__main__":
    dispositivos = fetch_devices_data()
    print("📡 Dispositivos encontrados:", len(dispositivos))
    for d in dispositivos:
        print(f"- {d['Device_ID']} | Potência: {d['Power']} W | Energia: {d['Energy']} kWh")

    dicas = gerar_recomendacoes(dispositivos)
    print("\n⚡ Recomendações de Energia:")
    print(dicas)
