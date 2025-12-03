from openai import OpenAI
import os
from dotenv import load_dotenv  # <-- IMPORTANTE

# Carga el .env desde la raíz del proyecto
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("API KEY DETECTADA:", "sí" if api_key else "no")

client = OpenAI(api_key=api_key)

try:
    r = client.chat.completions.create(
        model=os.getenv("OPENAI_TIPS_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "user", "content": "Dime un tip breve para probar la API"}],
        max_tokens=50,
    )
    print("OK:", r.choices[0].message.content)
except Exception as e:
    print("ERROR:", e)
