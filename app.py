from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
import os
from dotenv import load_dotenv
from langdetect import detect
import requests
import smtplib
from email.message import EmailMessage
import json

load_dotenv()
app = Flask(__name__, static_url_path='/static')
client_data = {}

# --- Config ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
FORWARD_NUMBER = os.getenv("FORWARD_NUMBER")

# --- Helper: Generate Audio with ElevenLabs ---
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
        path = f"./static/{filename}"
        with open(path, "wb") as f:
            f.write(response.content)
        return f"{request.url_root}static/{filename}"
    else:
        print("❌ Error generando audio:", response.text)
        return None

# --- Helper: Enviar correo ---
def enviar_correo(datos):
    msg = EmailMessage()
    msg['Subject'] = f"Nuevo lead: {datos.get('name', 'Sin nombre')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    cuerpo = "".join([f"{k}: {v}\n" for k, v in datos.items()])
    msg.set_content(f"Se ha recolectado la siguiente información:\n\n{cuerpo}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("✅ Correo enviado correctamente")
    except Exception as e:
        print("❌ Error al enviar el correo:", e)

# --- Ruta Principal ---
@app.route("/voice", methods=['POST'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    rep_name = request.args.get("rep", "there")

    data = client_data.setdefault(from_number, {
        "lang": "es" if detect(speech_result or "hola") == "es" else "en",
        "step": -1,
        "responses": {}
    })

    response = VoiceResponse()

    # --- Mensaje de bienvenida ---
    if data['step'] == -1:
        saludo_en = f"""Hi {rep_name}, this is Bryan. I'm calling because I help truckers save up to $500 per month per truck on insurance,
get dispatching at just 4%, earn from $3,000 to $4,000 a week,
access gas cards with $2,500 credit, and get help financing your down payment.
Do you have two minutes for a quick quote?"""

        saludo_es = f"""Hola {rep_name}, soy Bryan. Ayudo a camioneros a ahorrar hasta $500 al mes por camión en seguros,
a obtener despacho por solo 4%, ganar de $3,000 a $4,000 por semana,
acceso a tarjetas de gasolina con $2,500 de crédito,
y ayuda para el enganche de un camión nuevo.
¿Tienes 2 minutos para una cotización rápida?"""

        saludo = saludo_es if data['lang'] == 'es' else saludo_en
        audio_url = generar_audio_elevenlabs(saludo, "intro.mp3")

        if audio_url:
            response.play(audio_url)
        else:
            response.say(saludo, voice="Polly.Matthew")

        # Después del saludo, avanzamos al paso 0
        data['step'] = 0
        return str(response)

    # --- Flujo de preguntas ---
    pasos = [
        ("truck", "What year, make and model is your truck?" if data['lang'] == 'en' else "¿Cuál es el año, marca y modelo de tu camión?"),
        ("vin", "Can you provide the VIN number?" if data['lang'] == 'en' else "¿Cuál es el número VIN del camión?"),
        ("dob", "What is your date of birth?" if data['lang'] == 'en' else "¿Cuál es tu fecha de nacimiento?"),
        ("license", "And your driver’s license number?" if data['lang'] == 'en' else "¿Cuál es tu número de licencia de conducir?")
    ]

    if speech_result and data['step'] > 0:
        key, _ = pasos[data['step'] - 1]
        data['responses'][key] = speech_result

    if data['step'] < len(pasos):
        key, pregunta = pasos[data['step']]
        audio_url = generar_audio_elevenlabs(pregunta, f"step_{key}.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(pregunta, voice="Polly.Matthew")

        gather = Gather(input="speech", action="/voice", method="POST", timeout=6)
        gather.say(pregunta, voice="Polly.Matthew")
        response.append(gather)
        data['step'] += 1

    else:
        response.say("Thank you. Connecting you with a licensed agent now...", voice="Polly.Matthew")
        enviar_correo(data['responses'])
        dial = Dial(caller_id=request.values.get("To"))
        dial.number(FORWARD_NUMBER)
        response.append(dial)

    return str(response)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)