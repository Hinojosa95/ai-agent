import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")  # Asegúrate de que esté así en tu .env

print("🔍 API KEY:", ELEVENLABS_API_KEY)
print("🔍 VOICE_ID:", VOICE_ID)

texto = "Hola, esta es una prueba de mi voz clonada con ElevenLabs."
filename = "saludo.mp3"
output_path = f"./static/{filename}"

headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "text": texto,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.4,
        "similarity_boost": 0.85
    }
}

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Audio guardado en {output_path}")
else:
    print("❌ Error generando audio:")
    print(response.status_code)
    print(response.text)