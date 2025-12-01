# test_gemini.py  -- works with Gemini v1beta API keys

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("GEMINI_API_KEY present?:", bool(api_key))

if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY not found in .env")

genai.configure(api_key=api_key)

try:
    # Use a model your account ALWAYS supports
    model = genai.GenerativeModel("gemini-pro")

    response = model.generate_content("Say hello in one word.")

    print("Raw response:", response)
    print("Reply:", response.text)

except Exception as e:
    print("Gemini test error:", e)
