from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from collections import defaultdict
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.message import EmailMessage
import openai
import json

# --- Cargar variables de entorno ---
load_dotenv()

app = Flask(__name__, static_url_path='/static')
client_data = defaultdict(dict)

# --- Configuración de variables ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
FORWARD_NUMBER = os.getenv("FORWARD_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# --- Generar audio ElevenLabs ---
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
            print("✅ Audio guardado en:", os.path.abspath(path))

        try:
            base_url = request.url_root
        except RuntimeError:
            base_url = "http://localhost:5000/"
        return f"{base_url}static/{filename}"
    else:
        print("❌ Error generando audio:", response.status_code, response.text)
        return None

# --- Enviar correo ---
def enviar_correo(info_cliente):
    msg = EmailMessage()
    msg["Subject"] = "🚚 Nuevo lead calificado de seguro"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECEIVER

    contenido = "\n".join([f"{k}: {v}" for k, v in info_cliente.items()])
    msg.set_content(f"Datos recopilados del cliente:\n\n{contenido}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# --- Ruta de llamada principal ---
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    if request.method == "GET":
        return "👋 Hello! This endpoint is for Twilio POST requests only."

    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    rep_name = request.args.get("rep", "there")

    if from_number not in client_data:
        client_data[from_number] = {"step": 0, "responses": {}}

    data = client_data[from_number]

    preguntas = [
        "What kind of truck do you have or plan to get?",
        "What is the year make and model?",
        "What is your date of birth?",
        "Lastly what is your driver’s license number?"
    ]
    keys = ["truck", "model", "dob", "license"]

    response = VoiceResponse()

    # Guardar respuesta anterior
    if data["step"] > 0 and speech_result:
        if data["step"] - 1 < len(keys):
            key = keys[data["step"] - 1]
            data["responses"][key] = speech_result
        data["step"] += 1

    # Paso 0 - saludo
    if data["step"] == 0:
        saludo = (
            f"Hi {rep_name}, this is Bryan. I help trucks pay as low as $895 per month on truck insurance, "
            f"and secure distpaching to help, that will guarantee you will make $3,000 to $4,000 a week, "
            f"Do you have 2 minutes for a quick quote?"
        )
        filename = "saludo.mp3"
        if not os.path.exists(f"./static/{filename}"):
            generar_audio_elevenlabs(saludo, filename)
        audio_url = f"{request.url_root}static/{filename}"
        response.play(audio_url)
        data["step"] += 1
        gather = Gather(input="speech", action=request.url, method="POST", timeout=6)
        beep_path = "./static/beep_prompt.mp3"
        if not os.path.exists(beep_path):
            generar_audio_elevenlabs("Alright, go ahead and answer now.", "beep_prompt.mp3")
        beep_url = f"{request.url_root}static/beep_prompt.mp3"
        gather.play(beep_url)
        response.append(gather)
        return str(response)

    # Paso 1 a N - preguntas
    elif data["step"] <= len(preguntas):
        pregunta = preguntas[data["step"] - 1]
        filename = f"step{data['step']}.mp3"
        if not os.path.exists(f"./static/{filename}"):
            generar_audio_elevenlabs(pregunta, filename)
        audio_url = f"{request.url_root}static/{filename}"
        response.play(audio_url)

        gather = Gather(input="speech", action=request.url, method="POST", timeout=6)

        beep_path = "./static/beep_prompt.mp3"
        if not os.path.exists(beep_path):
            generar_audio_elevenlabs("Alright, go ahead and answer now.", "beep_prompt.mp3")
        beep_url = f"{request.url_root}static/beep_prompt.mp3"
        gather.play(beep_url)

        response.append(gather)
        return str(response)

    # Paso final - enviar correo y transferir
    else:
        enviar_correo(data["responses"])
        despedida = "Great, give me a quick second to get you to a licensed agent"
        filename = "despedida.mp3"
        if not os.path.exists(f"./static/{filename}"):
            generar_audio_elevenlabs(despedida, filename)
        audio_url = f"{request.url_root}static/{filename}"
        response.play(audio_url)

        dial = Dial(caller_id=request.values.get("To"))
        dial.number(FORWARD_NUMBER)
        response.append(dial)
        return str(response)


# --- Servir archivos estáticos ---
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# --- Ejecutar App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)