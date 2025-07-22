import os
import requests
from dotenv import load_dotenv

# Cargar claves del .env
load_dotenv()

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Texto del saludo
texto = "Hola, soy Bryan. ¿Cómo te puedo ayudar hoy?"

# Endpoint de ElevenLabs
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "text": texto,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

# Crear carpeta static si no existe
if not os.path.exists("static"):
    os.makedirs("static")

# Hacer la petición a ElevenLabs
response = requests.post(url, headers=headers, json=data)

# Guardar el audio
with open("static/greeting.mp3", "wb") as f:
    f.write(response.content)

print("✅ greeting.mp3 creado con éxito.")