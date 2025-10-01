import numpy as np
import pandas as pd
from datetime import datetime
from config.firebase_config import initialize_firebase

class DataService:
    def __init__(self):
        self.ref = initialize_firebase()
    
    def tuya_mock_status(self, device_id, dispositivo, prioridade="Mínima"):
        now = datetime.now().isoformat(timespec="seconds")
        voltage = 220
        current = round(np.random.uniform(0.5, 7.5), 2)
        power = round(voltage * current, 2)
        energy = round(np.random.uniform(0.05, 0.5), 2)
        
        return {
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
    
    def save_to_firebase(self, data):
        self.ref.push(data)
    
    def fetch_historico(self, limit=30):
        snapshot = self.ref.order_by_key().limit_to_last(limit).get()
        return list(snapshot.values()) if snapshot else []
    
    def get_dispositivos_mock(self):
        return [
            {"Device_ID": "mock_secador", "Dispositivo": "Secador de Cabelo", "Prioridade": "Alta"},
            {"Device_ID": "mock_laptop", "Dispositivo": "Laptop", "Prioridade": "Mínima"},
            {"Device_ID": "mock_geladeira", "Dispositivo": "Geladeira", "Prioridade": "Crítica"},
            {"Device_ID": "mock_televisao", "Dispositivo": "Televisão", "Prioridade": "Média"},
        ]
