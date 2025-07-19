from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Crear app Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ruta de test de llamada
@app.route("/voice", methods=["POST"])
def voice():
    saludo = "Hi Thomas, this is Bryan. I help trucks pay as low as $895 per month on truck insurance."
    filename = "saludo.mp3"
    path = os.path.join("static", filename)

    # Crear carpeta static si no existe
    os.makedirs("static", exist_ok=True)

    # Generar audio si no existe
    if not os.path.exists(path):
        print("🎤 Generando saludo con ElevenLabs...")
        audio_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": saludo,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.85}
        }

        r = requests.post(audio_url, json=payload, headers=headers)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            print("✅ Audio guardado en static/saludo.mp3")
        else:
            print("❌ Error al generar audio:", r.status_code, r.text)

    # Preparar respuesta TwiML
    response = VoiceResponse()
    full_url = request.url_root.rstrip("/") + "/static/" + filename
    print("📢 Reproduciendo:", full_url)
    response.play(full_url)

    return str(response)

# Servir archivos estáticos (mp3)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Ejecutar la app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)