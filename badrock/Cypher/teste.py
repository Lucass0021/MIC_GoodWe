import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyDNBtOsHQ8S8sL3J_I8vinhNOH_g2qwuMg"))

for m in genai.list_models():
    print(m.name, "->", m.supported_generation_methods)

