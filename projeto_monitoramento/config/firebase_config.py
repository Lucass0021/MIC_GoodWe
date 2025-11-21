import firebase_admin
from firebase_admin import credentials, db
import os

def initialize_firebase():
    """Inicializa e retorna a referência do Firebase"""
    cred_path = os.path.join(os.path.dirname(__file__), '../assets/mic-9d88e-firebase-adminsdk-fbsvc-b5729e6f68.json')
    
    cred = credentials.Certificate(cred_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://mic-9d88e-default-rtdb.firebaseio.com/'
        })
    
    return db.reference('consumo_dispositivos')
