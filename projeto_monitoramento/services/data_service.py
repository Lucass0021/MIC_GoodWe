import os
import numpy as np
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import logging

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.ref = self._initialize_firebase_safe()
    
    def _initialize_firebase_safe(self):
        """Inicializa Firebase com fallback seguro"""
        try:
            cred_path = os.path.join(os.path.dirname(__file__), '../assets/mic-9d88e-firebase-adminsdk-fbsvc-b5729e6f68.json')
            
            if not os.path.exists(cred_path):
                logger.warning("❌ Arquivo de credenciais do Firebase não encontrado")
                return None
            
            cred = credentials.Certificate(cred_path)
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://mic-9d88e-default-rtdb.firebaseio.com/'
                })
            
            logger.info("✅ Firebase inicializado com sucesso")
            return db.reference('consumo_dispositivos')
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Firebase: {e}")
            logger.info("🔶 Continuando em modo offline...")
            return None
    
    def tuya_mock_status(self, device_id, dispositivo, prioridade="Mínima"):
        now = datetime.now().isoformat(timespec="seconds")
        voltage = 220
        current = round(np.random.uniform(0.5, 7.5), 2)
        power = round(voltage * current, 2)
        energy = round(np.random.uniform(0.05, 0.5), 2)
        
        data = {
            "time": now,
            "Dispositivo": dispositivo,
            "Voltage": voltage,
            "Current": current,
            "Power": power,
            "Energy": energy,
            "Frequency": 60.0,
            "PF": 1,
            "Device_ID": device_id,
            "Prioridade": prioridade,
            "Nome_Conectado": "",
            "Modelo_Dispositivo": "",
        }
        return data
    
    def save_to_firebase(self, data):
        """Salva dados no Firebase (se disponível)"""
        if self.ref:
            try:
                self.ref.push(data)
                logger.info("✅ Dados salvos no Firebase")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar no Firebase: {e}")
        else:
            logger.info("🔶 Firebase não disponível - dados não salvos")
    
    def fetch_historico(self, limit=30):
        """Busca histórico com fallback para dados locais"""
        try:
            if self.ref:
                snapshot = self.ref.order_by_key().limit_to_last(limit).get()
                if snapshot:
                    historico = list(snapshot.values())
                    logger.info(f"✅ {len(historico)} registros carregados do Firebase")
                    return historico
            
            # Fallback para dados locais/mock
            logger.info("🔶 Usando dados mock para histórico")
            return self._generate_mock_historico(limit)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar histórico: {e}")
            return self._generate_mock_historico(limit)
    
    def _generate_mock_historico(self, limit=30):
        """Gera dados mock para o histórico"""
        dispositivos = self.get_dispositivos_mock()
        historico = []
        
        # Gerar dados históricos realistas
        for i in range(min(limit, 20)):  # Máximo 20 registros
            for dev in dispositivos:
                dados = self.tuya_mock_status(
                    dev["Device_ID"], 
                    dev["Dispositivo"], 
                    dev["Prioridade"]
                )
                # Ajustar timestamp para simular histórico
                import time
                dados["time"] = (datetime.now() - pd.Timedelta(hours=i*2)).isoformat()
                historico.append(dados)
        
        return historico[:limit]
    
    def get_dispositivos_mock(self):
        return [
            {"Device_ID": "mock_secador", "Dispositivo": "Secador de Cabelo", "Prioridade": "Alta"},
            {"Device_ID": "mock_laptop", "Dispositivo": "Laptop", "Prioridade": "Mínima"},
            {"Device_ID": "mock_geladeira", "Dispositivo": "Geladeira", "Prioridade": "Crítica"},
            {"Device_ID": "mock_televisao", "Dispositivo": "Televisão", "Prioridade": "Média"},
        ]