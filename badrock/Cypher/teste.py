import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyCJSLfW6d_3nABSQxRLaed6CDZR8_PmIt0"))

for m in genai.list_models():
    print(m.name, "->", m.supported_generation_methods)

