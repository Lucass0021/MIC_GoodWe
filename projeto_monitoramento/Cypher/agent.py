import os
import firebase_admin
from firebase_admin import credentials, db
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Carregar variáveis de ambiente --------------------
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

GEN_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurar Gemini se disponível
if GEN_API_KEY and GEN_API_KEY.startswith("AIza"):
    try:
        genai.configure(api_key=GEN_API_KEY)
        logger.info("✅ Gemini configurado com sucesso!")
        GEMINI_ACTIVE = True
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Gemini: {e}")
        GEMINI_ACTIVE = False
else:
    logger.warning("🔶 Gemini não configurado")
    GEMINI_ACTIVE = False

# -------------------- Firebase com Fallback --------------------
def initialize_firebase_safe():
    """Inicializa Firebase com tratamento de erro"""
    try:
        if firebase_admin._apps:
            return db.reference()
            
        cred_path = os.path.join(os.path.dirname(__file__), '../assets/mic-9d88e-firebase-adminsdk-fbsvc-b5729e6f68.json')
        
        if not os.path.exists(cred_path):
            logger.warning("❌ Arquivo de credenciais não encontrado")
            return None
            
        cred = credentials.Certificate(cred_path)
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://mic-9d88e-default-rtdb.firebaseio.com/'
        })
        
        logger.info("✅ Firebase Admin SDK inicializado!")
        return db.reference()
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Firebase: {e}")
        return None

def fetch_devices_data():
    """Busca dados com fallback seguro"""
    try:
        ref = initialize_firebase_safe()
        if not ref:
            return generate_mock_devices_data()
        
        snapshot = ref.child('tomadas').get()
        
        if not snapshot or not isinstance(snapshot, dict):
            return generate_mock_devices_data()
        
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
        return generate_mock_devices_data()

def generate_mock_devices_data():
    """Gera dados mock"""
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

# -------------------- Histórico de Perguntas e Respostas --------------------
def salvar_conversa(pergunta, resposta, dispositivos_analisados=None):
    """Salva a conversa no Firebase"""
    try:
        ref = initialize_firebase_safe()
        if not ref:
            return False
            
        conversa = {
            "pergunta": pergunta,
            "resposta": resposta,
            "dispositivos_analisados": dispositivos_analisados or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gemini_utilizado": GEMINI_ACTIVE
        }
        
        ref.child('conversas_cypher').push(conversa)
        logger.info("✅ Conversa salva no histórico")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar conversa: {e}")
        return False

def carregar_historico_conversas(limite=10):
    """Carrega o histórico de conversas"""
    try:
        ref = initialize_firebase_safe()
        if not ref:
            return []
        
        snapshot = ref.child('conversas_cypher').order_by_key().limit_to_last(limite).get()
        
        conversas = []
        if snapshot and isinstance(snapshot, dict):
            for key, value in snapshot.items():
                if isinstance(value, dict):
                    conversas.append({
                        "id": key,
                        "pergunta": value.get("pergunta", ""),
                        "resposta": value.get("resposta", ""),
                        "timestamp": value.get("timestamp", ""),
                        "gemini_utilizado": value.get("gemini_utilizado", False)
                    })
        
        # Ordenar por timestamp (mais recente primeiro)
        conversas.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return conversas
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar histórico: {e}")
        return []

def limpar_historico_conversas():
    """Limpa todo o histórico de conversas"""
    try:
        ref = initialize_firebase_safe()
        if not ref:
            return False
            
        ref.child('conversas_cypher').delete()
        logger.info("✅ Histórico de conversas limpo")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar histórico: {e}")
        return False

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

def gerar_recomendacoes(devices, pergunta_personalizada=None, use_mock=False):
    """Envia os dados dos dispositivos para o Gemini e retorna dicas"""
    
    # ✅ VERIFICAÇÃO MELHORADA
    if not GEMINI_ACTIVE or use_mock:
        logger.warning("🔶 Gemini não disponível - usando modo mock")
        resposta = gerar_recomendacoes_mock(devices, pergunta_personalizada)
    else:
        if not devices:
            resposta = "📊 Nenhum dispositivo encontrado para análise."
        else:
            try:
                prompt_base = carregar_prompt()
                
                # Preparar contexto dos dispositivos
                contexto_dispositivos = "\n".join([f"- {d['Device_ID']}: {d['Power']}W, {d['Energy']}kWh, FP:{d['PF']:.2f}" for d in devices])
                
                # Construir prompt
                if pergunta_personalizada:
                    prompt = f"""{prompt_base}

PERGUNTA DO USUÁRIO: {pergunta_personalizada}

DADOS DOS DISPOSITIVOS:
{contexto_dispositivos}

Total de dispositivos: {len(devices)}
Potência total: {sum(d['Power'] for d in devices):.1f}W
Energia total: {sum(d['Energy'] for d in devices):.3f}kWh

RESPOSTA:"""
                else:
                    prompt = f"""{prompt_base}

DADOS DOS DISPOSITIVOS:
{contexto_dispositivos}

Total de dispositivos: {len(devices)}
Potência total: {sum(d['Power'] for d in devices):.1f}W
Energia total: {sum(d['Energy'] for d in devices):.3f}kWh

ANÁLISE E RECOMENDAÇÕES:"""
                
                logger.info("🔄 Consultando Gemini...")
                modelo = genai.GenerativeModel("gemini-2.5-flash")
                resposta_gemini = modelo.generate_content(prompt)
                resposta = resposta_gemini.text
                logger.info("✅ Recomendações geradas com sucesso!")
                
            except Exception as e:
                logger.error(f"❌ Erro ao gerar recomendações com Gemini: {e}")
                resposta = gerar_recomendacoes_mock(devices, pergunta_personalizada)
    
    # Salvar no histórico
    pergunta_salvar = pergunta_personalizada if pergunta_personalizada else "Análise geral de eficiência energética"
    dispositivos_info = [{"Device_ID": d["Device_ID"], "Power": d["Power"], "Energy": d["Energy"]} for d in devices]
    salvar_conversa(pergunta_salvar, resposta, dispositivos_info)
    
    return resposta

def gerar_recomendacoes_mock(devices, pergunta=None):
    """Gera recomendações mock quando o Gemini não está disponível"""
    if not devices:
        return "💡 Conecte dispositivos para receber recomendações personalizadas de economia de energia."
    
    # Ordenar dispositivos por consumo
    dispositivos_ordenados = sorted(devices, key=lambda x: x['Power'], reverse=True)
    total_power = sum(d['Power'] for d in devices)
    total_energy = sum(d['Energy'] for d in devices)
    
    # Análise detalhada dos dispositivos
    analise_dispositivos = "\n".join([
        f"• {d['Device_ID']}: {d['Power']}W ({d['Energy']}kWh) - {'⚡ ALTO' if d['Power'] > 1000 else '💡 MÉDIO' if d['Power'] > 200 else '🌱 BAIXO'} consumo"
        for d in dispositivos_ordenados
    ])
    
    # Respostas específicas baseadas na pergunta
    if pergunta:
        pergunta_lower = pergunta.lower()
        
        # Dispositivos que mais consomem
        if any(palavra in pergunta_lower for palavra in ['qual consome mais', 'maior consumo', 'dispositivos consomem mais', 'mais energia']):
            maior_consumidor = dispositivos_ordenados[0]
            return f"""🔍 **ANÁLISE DE CONSUMO POR DISPOSITIVO**

📊 **Ranking de Consumo (Potência):**
{analise_dispositivos}

⚡ **Maior Consumidor:** {maior_consumidor['Device_ID']}
   - Potência: {maior_consumidor['Power']}W
   - Energia: {maior_consumidor['Energy']}kWh
   - Recomendações:
     • Use com moderação
     • Evite horário de pico (18h-21h)
     • Considere alternativas mais eficientes

💡 **Dica:** O secador consome {maior_consumidor['Power']}W - equivalente a {maior_consumidor['Power']//10} lâmpadas LED!"""
        
        # Economia de energia
        elif any(palavra in pergunta_lower for palavra in ['economizar', 'economia', 'poupar', 'reduzir', 'gasto']):
            return f"""💰 **ESTRATÉGIAS DE ECONOMIA ENERGÉTICA**

📈 **Situação Atual:**
- Consumo total: {total_power}W
- Energia total: {total_energy:.2f}kWh
- {len([d for d in devices if d['Power'] > 500])} dispositivos de alto consumo

🎯 **Ações Imediatas:**
1. **Desligar standby**: Economia estimada de 5-10%
2. **Horário fora pico**: Use secador antes das 18h
3. **Geladeira eficiente**: Mantenha portas fechadas
4. **Iluminação LED**: Troque lâmpadas antigas

💡 **Economia Potencial:** Até 30% na conta de energia"""
        
        # Segurança elétrica
        elif any(palavra in pergunta_lower for palavra in ['segurança', 'seguro', 'perigo', 'risco', 'incêndio']):
            dispositivos_alto_risco = [d for d in devices if d['Power'] > 1500]
            return f"""🔒 **ANÁLISE DE SEGURANÇA ENERGÉTICA**

⚠️ **Dispositivos de Alto Consumo ({len(dispositivos_alto_risco)}):**
{chr(10).join([f'• {d["Device_ID"]}: {d["Power"]}W' for d in dispositivos_alto_risco]) if dispositivos_alto_risco else '• Nenhum dispositivo crítico'}

🚨 **Recomendações de Segurança:**
1. **Evite sobrecarga**: Não use múltiplos dispositivos de alto consumo juntos
2. **Verifique fiação**: Instalação adequada para {total_power}W total
3. **Protetor contra surtos**: Use filtro de linha qualificado
4. **Ventilação**: Mantenha áreas bem ventiladas

📞 **Emergência**: Desligue imediatamente em caso de: cheiro de queimado, faíscas ou aquecimento excessivo"""
        
        # Otimização geral
        elif any(palavra in pergunta_lower for palavra in ['otimizar', 'melhorar', 'eficiencia', 'eficiência']):
            return f"""🎯 **PLANO DE OTIMIZAÇÃO ENERGÉTICA**

📊 **Diagnóstico:**
{analise_dispositivos}

🚀 **Estratégias de Otimização:**

1. **Gestão de Horários**
   - Secador: Use antes das 18h
   - Geladeira: Mantenha termostato em 4°C

2. **Substituições Inteligentes**
   - Considere secador de baixo consumo
   - Verifique selo Procel dos equipamentos

3. **Monitoramento Contínuo**
   - Acompanhe picos de consumo
   - Identifique desperdícios

📈 **Resultado Esperado:** Redução de 15-25% no consumo"""
        
        # Dicas gerais
        elif any(palavra in pergunta_lower for palavra in ['dica', 'sugestão', 'como usar', 'recomendação']):
            return f"""💡 **DICAS PRÁTICAS PERSONALIZADAS**

Baseado nos seus {len(devices)} dispositivos:

🔧 **Para {dispositivos_ordenados[0]['Device_ID']}** ({dispositivos_ordenados[0]['Power']}W):
   - Use por períodos curtos
   - Prefira temperaturas mais baixas

🔧 **Para {dispositivos_ordenados[1]['Device_ID']}** ({dispositivos_ordenados[1]['Power']}W):
   - Mantenha limpo e ventilado
   - Verifique vedação regularmente

🌱 **Hábitos Sustentáveis:**
   - Desligue da tomada quando não usar
   - Agende uso fora do horário de pico
   - Faça manutenção preventiva

💎 **Benefício:** Economia mensal estimada de R$ {total_power * 0.0005:.2f}"""
        
        # Resposta padrão para perguntas não reconhecidas
        else:
            return f"""🤖 **RESPOSTA PERSONALIZADA**

💭 **Sua pergunta:** "{pergunta}"

📊 **Contexto dos Dispositivos:**
{analise_dispositivos}

💡 **Recomendações Específicas:**
• **Monitoramento**: Acompanhe o consumo do {dispositivos_ordenados[0]['Device_ID']}
• **Otimização**: Reduza tempo de uso em 20% para economizar
• **Manutenção**: Verifique estado dos equipamentos regularmente

🔍 **Dica Extra:** Para análise mais detalhada, conecte-se à API Gemini"""
    
    # Resposta padrão (sem pergunta específica)
    if total_power > 2000:
        return f"""⚡ **ALTO CONSUMO DETECTADO!**

📊 **Situação:**
{analise_dispositivos}

🚨 **Ações Recomendadas:**
• Evite usar {dispositivos_ordenados[0]['Device_ID']} e {dispositivos_ordenados[1]['Device_ID']} simultaneamente
• Considere aparelhos classe A (economia de 30%)
• Desligue aparelhos em standby
• Use horários fora de pico (6h-18h)

💰 **Economia Potencial:** Até R$ {total_power * 0.001:.2f}/mês"""
    elif total_power > 1000:
        return f"""💡 **CONSUMO MODERADO**

📊 **Análise:**
{analise_dispositivos}

🎯 **Otimizações:**
• Use iluminação LED
• Configure horários inteligentes
• Verifique modo standby
• Mantenha manutenção em dia

🌱 **Próximos Passos:** Continue monitorando para identificar oportunidades"""
    else:
        return f"""🌱 **CONSUMO BAIXO - PARABÉNS!**

📊 **Desempenho:**
{analise_dispositivos}

⭐ **Melhores Práticas:**
• Continue com as boas práticas
• Monitore regularmente
• Considere energia solar
• Compartilhe suas estratégias

🏆 **Resultado:** Eficiência energética exemplar!"""

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