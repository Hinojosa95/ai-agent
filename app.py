from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Play
import os
from dotenv import load_dotenv
from langdetect import detect
import requests

load_dotenv()
app = Flask(__name__, static_url_path='/static')
client_data = {}

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "yUjL5K6CCuYZWlyF0yYI"  # Voz clonada

def generar_audio_elevenlabs(texto, filename):
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
        filepath = f"./static/{filename}"
        with open(filepath, "wb") as f:
            f.write(response.content)
        return f"{request.url_root}static/{filename}"
    else:
        print("❌ Error generando audio:", response.text)
        return None

@app.route("/voice", methods=["POST", "GET"])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "")
    rep_name = request.args.get("rep", "there")

    # Crear perfil si no existe
    if from_number not in client_data:
        lang = detect(speech_result) if speech_result else "en"
        greeting_en = f"""Hi {rep_name}, this is Bryan. I help truckers save up to $500 per month per truck on insurance,
get dispatching at just 4%, earn $3,000–$4,000 a week,
access gas cards with $2,500 credit,
and get help financing your down payment.

Do you have 2 minutes for a quick quote?"""

        greeting_es = f"""Hola {rep_name}, soy Bryan. Ayudo a camioneros a ahorrar hasta $500 al mes por camión en seguros,
a obtener despacho por solo 4%, ganar de $3,000 a $4,000 por semana,
acceso a tarjetas de gasolina con $2,500 de crédito,
y ayuda para el enganche de un camión nuevo.

¿Tienes 2 minutos para una cotización rápida?"""

        greeting = greeting_es if lang.startswith("es") else greeting_en
        filename = f"{from_number}.mp3"
        audio_url = generar_audio_elevenlabs(greeting, filename)

        client_data[from_number] = {
            "lang": lang,
            "step": 1,
            "audio_url": audio_url
        }

    response = VoiceResponse()

    # Reproducir saludo si es la primera interacción
    if client_data[from_number]["step"] == 1:
        if client_data[from_number]["audio_url"]:
            response.play(client_data[from_number]["audio_url"])
        else:
            response.say("Sorry, I couldn't generate audio.", voice="Polly.Matthew")

    # Definir siguiente pregunta
    step = client_data[from_number]["step"]
    preguntas = {
        2: "Please tell me the year, make and model of your truck.",
        3: "Can you tell me the VIN number?",
        4: "What is your date of birth?",
        5: "Finally, your driver's license number please.",
        6: "Thanks. Give me a second to transfer you to an agent."
    }
    pregunta = preguntas.get(step, "Thanks. One moment please.")

    gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
    gather.say(pregunta, voice="Polly.Matthew")
    response.append(gather)

    # Avanzar paso
    client_data[from_number]["step"] += 1

    return str(response)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)