# list_gemini_models.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY present?:", bool(api_key))
if not api_key:
    raise SystemExit("No GEMINI_API_KEY in .env")

genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    print("=== Models available for this key ===")
    for m in models:
        # print useful info: id/name and supported generation methods (if present)
        name = getattr(m, "name", None) or getattr(m, "model", None) or str(m)
        display = getattr(m, "displayName", None)
        # some SDK return supportedGenerationMethods or capabilities fields
        supported = getattr(m, "supportedGenerationMethods", None) or getattr(m, "capabilities", None)
        print("-", name, "|", display, "| supported:", supported)
except Exception as e:
    print("Error listing models:", repr(e))
