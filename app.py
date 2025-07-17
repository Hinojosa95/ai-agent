from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from collections import defaultdict
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.message import EmailMessage
import openai
import socket
import time

# --- Cargar variables de entorno ---
load_dotenv()

app = Flask(__name__)
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

# --- Generar audio ElevenLabs y subirlo a tmpfiles.org ---
def generar_audio_elevenlabs(texto, filename="audio.mp3"):
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

    print(f"🔁 Enviando solicitud a ElevenLabs con VOICE_ID: {VOICE_ID}")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "wb") as f:
            f.write(response.content)

        try:
            with open(temp_path, "rb") as audio_file:
                upload = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": audio_file})

            if upload.status_code == 200:
                result = upload.json()
                file_url = result.get("data", {}).get("url")
                if file_url:
                    file_url = file_url.replace("/", "https://tmpfiles.org/")
                    print(f"✅ Audio disponible en: {file_url}")
                    return file_url
        except Exception as e:
            print("❌ Error al subir archivo:", str(e))

    print(f"❌ Error al generar audio: {response.status_code}")
    return None

# --- Generar respuesta con GPT ---
def responder_con_gpt(texto_cliente):
    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un agente de seguros amable y profesional..."},
            {"role": "user", "content": texto_cliente}
        ],
        temperature=0.7,
        max_tokens=100
    )
    return respuesta.choices[0].message["content"]

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
        client_data[from_number] = {
            "step": 0,
            "responses": {},
            "preguntas": [
                ("truck", "What kind of truck do you have or plan to get?"),
                ("model", "What is the year, make, and model of your truck?"),
                ("dob", "What is your date of birth?"),
                ("license", "What is your driver's license number?")
            ]
        }

    data = client_data[from_number]
    response = VoiceResponse()

    # --- Paso inicial: saludo ---
    if data["step"] == 0:
        saludo = (
            f"Hi {rep_name}, this is Bryan. I help trucks pay as low as $895 per month on truck insurance..."
        )
        audio_url = generar_audio_elevenlabs(saludo, "saludo.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(saludo)
        data["step"] += 1
        return str(response)

    # --- Pasos siguientes ---
    elif data["step"] <= len(data["preguntas"]):
        key, pregunta = data["preguntas"][data["step"] - 1]

        if speech_result:
            data["responses"][key] = speech_result
            data["step"] += 1

        if data["step"] <= len(data["preguntas"]):
            _, siguiente = data["preguntas"][data["step"] - 1]
            audio_url = generar_audio_elevenlabs(siguiente, f"step{data['step']}.mp3")
            if audio_url:
                response.play(audio_url)
            else:
                response.say(siguiente)
        else:
            despedida = "Great, give me a second to connect you with a licensed agent."
            audio_url = generar_audio_elevenlabs(despedida, "despedida.mp3")
            if audio_url:
                response.play(audio_url)
            else:
                response.say(despedida)
            enviar_correo(data["responses"])
            dial = Dial(caller_id=request.values.get("To"))
            dial.number(FORWARD_NUMBER)
            response.append(dial)

    gather = Gather(input="speech", action=request.url, method="POST", timeout=6)
    beep = generar_audio_elevenlabs("Alright, go ahead and answer now.", "beep_prompt.mp3")
    if beep:
        gather.play(beep)
    else:
        gather.say("Alright, go ahead and answer now.")
    response.append(gather)
    return str(response)

@app.route("/")
def home():
    return "🚀 AI Agent is running!"

if __name__ == "__main__":
    port = 5001
    print(f"🚀 Running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)