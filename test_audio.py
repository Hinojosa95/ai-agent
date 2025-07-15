import os
import requests
from dotenv import load_dotenv

load_dotenv()

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
API_KEY = os.getenv("ELEVENLABS_API_KEY")
texto = "Hi, this i Bryan and I'm using elevenlabs voice cloned."

headers = {
    "xi-api-key": API_KEY,
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
response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    with open("static/prueba_clonada.mp3", "wb") as f:
        f.write(response.content)
    print("✅ Audio generado correctamente en static/prueba_clonada.mp3")
else:
    print("❌ Error:", response.status_code, response.text)