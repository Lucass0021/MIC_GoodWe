# -*- coding: utf-8 -*-

import logging
import ask_sdk_core.utils as ask_utils
import requests
import os
from dotenv import load_dotenv
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Carrega variáveis do .env
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Chave da API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A chave GOOGLE_API_KEY não foi encontrada no .env")

# Endpoint do Gemini - modelo rápido para Alexa
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GOOGLE_API_KEY}"

headers = {
    "Content-Type": "application/json"
}

# Função para chamar o Gemini
def call_gemini(user_text: str) -> str:
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_text}]}
        ]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=7)
        if response.status_code == 200:
            response_data = response.json()
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = parts[0].get("text", "") if parts else "Texto não encontrado"
            else:
                text = "Texto não encontrado"
            return text
        else:
            logger.error(f"Erro na API Gemini: {response.status_code} {response.text}")
            return "Erro na requisição"
    except Exception as e:
        logger.error(f"Exceção ao chamar Gemini: {e}", exc_info=True)
        return "Erro ao acessar o modelo"

# Função para ler o prompt inicial do arquivo
def get_initial_prompt() -> str:
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning("prompt.txt não encontrado. Usando prompt padrão.")
        return "Você será minha assistente de I.A. Vamos interagir conforme eu orientar."

# Handlers da Alexa
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        intro_text = get_initial_prompt()
        resposta_modelo = call_gemini(intro_text)
        speak_output = resposta_modelo + " Como posso te ajudar?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("O que você gostaria de saber?")
                .response
        )

class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ChatIntent")(handler_input)

    def handle(self, handler_input):
        query = handler_input.request_envelope.request.intent.slots["query"].value
        resposta_modelo = call_gemini(query)
        speak_output = resposta_modelo
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Quer perguntar mais alguma coisa?")
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
            ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Até logo!").response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = "Desculpe, tive um problema ao processar sua solicitação. Tente novamente."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Pode repetir sua pergunta?")
                .response
        )

# SkillBuilder
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
