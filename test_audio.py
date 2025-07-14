# test_audio.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

texto = "Alright, go ahead and answer now."
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
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

response = requests.post(url, json=payload, headers=headers)
print("Status:", response.status_code)
if response.status_code == 200:
    with open("prueba_beep.mp3", "wb") as f:
        f.write(response.content)
    print("✅ Audio guardado como prueba_beep.mp3")
else:
    print("❌ Error:", response.text)