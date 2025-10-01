import os
import firebase_admin
from firebase_admin import credentials, db
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Carregar variáveis de ambiente --------------------
# ✅ CORREÇÃO: Carregar do .env na raiz
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

GEN_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ DEBUG: Verificar se carregou corretamente
print(f"🔍 DEBUG - GEMINI_API_KEY: {GEN_API_KEY}")
print(f"🔍 DEBUG - .env path: {env_path}")
print(f"🔍 DEBUG - Current dir: {os.getcwd()}")

if GEN_API_KEY and GEN_API_KEY.startswith("AIza"):
    try:
        genai.configure(api_key=GEN_API_KEY)
        logger.info("✅ Gemini configurado com sucesso!")
        GEMINI_ACTIVE = True
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Gemini: {e}")
        GEMINI_ACTIVE = False
else:
    logger.warning("🔶 Gemini não configurado - modo mock ativado")
    GEMINI_ACTIVE = False

# -------------------- Firebase com Admin SDK --------------------
def initialize_firebase():
    """Inicializa Firebase Admin SDK"""
    try:
        # ✅ USA O MESMO ARQUIVO QUE JÁ FUNCIONA
        cred_path = os.path.join(os.path.dirname(__file__), '../assets/mic-9d88e-firebase-adminsdk-fbsvc-b5729e6f68.json')
        
        if not os.path.exists(cred_path):
            logger.error(f"❌ Arquivo de credenciais não encontrado: {cred_path}")
            return None
            
        cred = credentials.Certificate(cred_path)
        
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://mic-9d88e-default-rtdb.firebaseio.com/'
            })
        
        logger.info("✅ Firebase Admin SDK inicializado!")
        return db.reference()
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Firebase: {e}")
        return None

def fetch_devices_data():
    """Busca todos os dispositivos e seus dados de consumo"""
    try:
        ref = initialize_firebase()
        if not ref:
            logger.warning("🔶 Firebase não disponível - usando dados mock")
            return gerar_dados_mock()
        
        # Buscar dados das tomadas
        snapshot = ref.child('tomadas').get()
        
        if not snapshot or not isinstance(snapshot, dict):
            logger.warning("⚠ Nenhum dado encontrado no Firebase")
            return gerar_dados_mock()
        
        devices = []
        for dev_id, values in snapshot.items():
            if not isinstance(values, dict):
                continue
                
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
        
        logger.info(f"✅ {len(devices)} dispositivos reais carregados")
        return devices
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dispositivos: {e}")
        return gerar_dados_mock()

def gerar_dados_mock():
    """Gera dados mock para teste"""
    return [
        {
            "Device_ID": "mock_secador",
            "time": datetime.now(timezone.utc).isoformat(),
            "Voltage": 220.0,
            "Current": 7.5,
            "Power": 1650.0,
            "Energy": 0.45,
            "Frequency": 60.0,
            "PF": 0.95
        },
        {
            "Device_ID": "mock_geladeira", 
            "time": datetime.now(timezone.utc).isoformat(),
            "Voltage": 220.0,
            "Current": 0.8,
            "Power": 176.0,
            "Energy": 2.3,
            "Frequency": 60.0,
            "PF": 0.98
        }
    ]

# -------------------- Agente Gemini --------------------
def carregar_prompt():
    """Lê o prompt do arquivo prompt.txt"""
    try:
        caminho_prompt = os.path.join(os.path.dirname(__file__), 'prompt.txt')
        with open(caminho_prompt, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("⚠ prompt.txt não encontrado, usando padrão")
        return "Você é um especialista em eficiência energética. Analise os dados e forneça recomendações práticas."

def gerar_recomendacoes(devices, use_mock=False):
    """Envia os dados dos dispositivos para o Gemini e retorna dicas"""
    
    # ✅ VERIFICAÇÃO MELHORADA
    if not GEMINI_ACTIVE:
        logger.warning("🔶 Gemini não disponível - usando modo mock")
        return gerar_recomendacoes_mock(devices)
    
    if not devices:
        return "📊 Nenhum dispositivo encontrado para análise."
    
    try:
        prompt_base = carregar_prompt()
        contexto = "\n".join([f"- {d['Device_ID']}: {d['Power']}W, {d['Energy']}kWh, FP:{d['PF']:.2f}" for d in devices])
        
        prompt = f"""{prompt_base}

DADOS DOS DISPOSITIVOS:
{contexto}

Total de dispositivos: {len(devices)}
Potência total: {sum(d['Power'] for d in devices):.1f}W
Energia total: {sum(d['Energy'] for d in devices):.3f}kWh

ANÁLISE E RECOMENDAÇÕES:"""
        
        logger.info("🔄 Consultando Gemini...")
        modelo = genai.GenerativeModel("gemini-2.5-flash")
        resposta = modelo.generate_content(prompt)
        
        logger.info("✅ Recomendações geradas com sucesso!")
        return resposta.text
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar recomendações com Gemini: {e}")
        return gerar_recomendacoes_mock(devices)

def gerar_recomendacoes_mock(devices):
    """Gera recomendações mock quando o Gemini não está disponível"""
    if not devices:
        return "💡 Conecte dispositivos para receber recomendações personalizadas de economia de energia."
    
    total_power = sum(d['Power'] for d in devices)
    
    if total_power > 2000:
        return "⚡ ALTO CONSUMO DETECTADO!\n\n• Evite usar múltiplos aparelhos de alto consumo simultaneamente\n• Considere usar aparelhos mais eficientes (classe A)\n• Desligue aparelhos em standby\n• Use horários fora de pico para equipamentos pesados"
    elif total_power > 1000:
        return "💡 CONSUMO MODERADO\n\n• Use iluminação LED\n• Configure horários para equipamentos\n• Verifique o modo standby dos eletrônicos\n• Mantenha a manutenção em dia"
    else:
        return "🌱 CONSUMO BAIXO\n\n• Continue com as boas práticas\n• Monitore regularmente o consumo\n• Considere energia solar para maior economia\n• Parabéns pela eficiência energética!"

# -------------------- Execução principal --------------------
if __name__ == "__main__":
    print("🔍 Buscando dados dos dispositivos...")
    dispositivos = fetch_devices_data()
    
    print(f"📡 Dispositivos encontrados: {len(dispositivos)}")
    for d in dispositivos:
        print(f"- {d['Device_ID']} | Potência: {d['Power']} W | Energia: {d['Energy']} kWh")

    print(f"\n🤖 Status Gemini: {'✅ ATIVO' if GEMINI_ACTIVE else '❌ MOCK'}")
    print("Gerando recomendações...")
    
    dicas = gerar_recomendacoes(dispositivos)
    print("\n⚡ RECOMENDAÇÕES DE ENERGIA:")
    print("=" * 50)
    print(dicas)
    print("=" * 50)
