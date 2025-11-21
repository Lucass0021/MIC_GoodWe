import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv('../.env')
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("🤖 MODELOS DISPONÍVEIS:")
print("=" * 50)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Métodos: {model.supported_generation_methods}")
        print()
