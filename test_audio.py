import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def generar_audio_prueba():
    texto = "Hello, this is a test audio generated from ElevenLabs."
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.85
        }
    }

    os.makedirs("static", exist_ok=True)
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        with open("./static/test_voice.mp3", "wb") as f:
            f.write(response.content)
        print("✅ Audio generado como test_voice.mp3")
    else:
        print("❌ Error:", response.status_code, response.text)

generar_audio_prueba()