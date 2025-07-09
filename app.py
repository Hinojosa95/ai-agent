# app.py
from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from dotenv import load_dotenv
import os
import requests
from langdetect import detect
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__, static_url_path='/static')

# Configuración global
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
FORWARD_NUMBER = os.getenv("FORWARD_NUMBER")

# Estado de la llamada por número
call_state = {}

# Función para generar audio
def generar_audio(texto, filename):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": texto,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.85}
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        path = f"./static/{filename}"
        with open(path, "wb") as f:
            f.write(response.content)
        return f"{request.url_root}static/{filename}"
    else:
        print("Error generando audio:", response.text)
        return None

# Función para enviar correo

def enviar_correo(datos):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = "📞 Lead listo para cotización - AI Agent"

    body = "".join([f"{k}: {v}\n" for k, v in datos.items()])
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ Correo enviado")
    except Exception as e:
        print("❌ Error enviando correo:", e)

@app.route("/voice", methods=['POST'])
def voice():
    from_number = request.values.get("From")
    speech = request.values.get("SpeechResult", "")

    if from_number not in call_state:
        lang = detect(speech) if speech else "en"
        saludo = ("Hola, soy Bryan..." if lang == "es" else "Hi, this is Bryan...")
        call_state[from_number] = {"step": 1, "lang": lang, "data": {}, "last": saludo}

    state = call_state[from_number]
    step = state["step"]
    lang = state["lang"]
    response = VoiceResponse()

    # Guardamos la respuesta previa
    if speech:
        preguntas = ["Truck Info", "VIN", "Date of Birth", "License"]
        if 2 <= step <= 5:
            state["data"][preguntas[step - 2]] = speech

    state["step"] += 1
    next_step = state["step"]

    if next_step == 2:
        prompt = "What is the year, make, and model of your truck?"
    elif next_step == 3:
        prompt = "Please tell me the VIN number."
    elif next_step == 4:
        prompt = "What is your date of birth?"
    elif next_step == 5:
        prompt = "What is your driver license number?"
    elif next_step == 6:
        # Terminamos, enviamos correo y transferimos
        enviar_correo(state["data"])
        response.say("Thank you. Connecting you now to a live agent.", voice="Polly.Matthew")
        response.dial(FORWARD_NUMBER)
        call_state.pop(from_number, None)
        return str(response)
    else:
        prompt = state["last"]

    audio_url = generar_audio(prompt, f"{from_number}_{next_step}.mp3")
    if audio_url:
        gather = Gather(input="speech", timeout=6, action="/voice")
        gather.play(audio_url)
        response.append(gather)
    else:
        response.say("Sorry, could not generate the prompt.", voice="Polly.Matthew")

    state["last"] = prompt
    return str(response)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))