from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
from langdetect import detect
import requests

load_dotenv()
app = Flask(__name__, static_url_path='/static')
client_data = {}

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def generar_audio_elevenlabs(texto, filename="audio.mp3"):
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
        with open(f"./static/{filename}", "wb") as f:
            f.write(response.content)
        return f"{request.url_root}static/{filename}"
    else:
        print("❌ Error generando audio:", response.text)
        return None

@app.route("/voice", methods=['POST', 'GET'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "")
    rep_name = request.args.get("rep", "there")

    if from_number not in client_data:
        lang = detect(speech_result) if speech_result else "en"

        greeting_en = f"""Hi {rep_name}, this is Bryan. I'm calling because I help truckers save up to $500 per month per truck on insurance,
get dispatching at just 4%, earn from $3,000 to $4,000 a week. 
Do you have two minutes for a quick quote? It's a non-obligation quote, sir.

I have your DOT number. Could you confirm the year, make, and model of your truck?

Also, I’ll need your VIN number, what you're hauling, how far you run (your radius), 
your date of birth, and your driver’s license number. That way I can give you an accurate quote.

At the end, I’ll bring a licensed agent on the line to go over the numbers.
Let's get started, what’s the make and model of your truck?"""

        greeting_es = f"""Hola {rep_name}, soy Bryan. Ayudo a camioneros a ahorrar hasta $500 al mes por camión en seguros,
a obtener despacho por solo 4%, ganar de $3,000 a $4,000 por semana,
acceso a tarjetas de gasolina con $2,500 de crédito,
y ayuda para el enganche de un camión nuevo.

¿Tienes 2 minutos para una cotización rápida?
Empecemos: ¿Cuál es la marca y modelo de tu camión?"""

        greeting = greeting_es if lang.startswith("es") else greeting_en
        client_data[from_number] = {
            "greeting": greeting,
            "lang": lang,
            "attempts": 1
        }

    response = VoiceResponse()
    audio_url = generar_audio_elevenlabs(client_data[from_number]["greeting"])
    
    if audio_url:
        response.play(audio_url)
    else:
        response.say("Sorry, I couldn't generate audio.", voice="Polly.Matthew")

    # RECOGER RESPUESTA DEL CLIENTE
    gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
    gather.say("Please tell me the make and model of your truck.", voice="Polly.Matthew")
    response.append(gather)

    # SI NO HAY RESPUESTA, REINTENTAR UNA VEZ
    if client_data[from_number]["attempts"] < 2:
        client_data[from_number]["attempts"] += 1
    else:
        response.say("Sorry, I couldn't hear you. We'll try again later.", voice="Polly.Matthew")

    return str(response)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)