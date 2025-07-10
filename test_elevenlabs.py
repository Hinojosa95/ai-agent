import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def probar_elevenlabs():
    texto = "Hola, esta es una prueba para verificar mi voz clonada de ElevenLabs."
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

    if response.status_code == 200:
        with open("prueba_elevenlabs.mp3", "wb") as f:
            f.write(response.content)
        print("✅ Audio generado correctamente. Archivo guardado como prueba_elevenlabs.mp3")
    else:
        print("❌ Error al generar el audio:")
        print("Status Code:", response.status_code)
        print("Respuesta:", response.text)

if __name__ == "__main__":
    probar_elevenlabs()