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
import socket
import time

# --- Cargar variables de entorno ---
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
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
    os.makedirs("static", exist_ok=True)

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
        path = f"./static/{filename}"
        with open(path, "wb") as f:
            f.write(response.content)

        print(f"✅ Audio guardado localmente en: {os.path.abspath(path)}")

        # ⬆️ Subir a file.io
        try:
            with open(path, "rb") as audio_file:
                upload = requests.post("https://file.io", files={"file": audio_file})

            if upload.status_code == 200:
                file_url = upload.json().get("link")
                print(f"🔗 Audio accesible en file.io: {file_url}")
                return file_url
            else:
                print("❌ Error al subir a file.io:", upload.text)
                return None
        except Exception as e:
            print("❌ Error subiendo a file.io:", str(e))
            return None
    else:
        print(f"❌ Error al generar audio: {response.status_code}")
        print(f"📄 Detalle del error: {response.text}")
        return None


# --- Generar respuesta con GPT ---
def responder_con_gpt(texto_cliente):
    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un agente de seguros amable y profesional que recopila información del cliente para cotizar un seguro de camión. Haz una pregunta a la vez. Si ya tienes toda la información, di que lo vas a transferir a un agente humano."},
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
            f"Hi {rep_name}, this is Bryan. I help trucks pay as low as $895 per month on truck insurance, "
            f"and secure dispatching to help, that will guarantee you will make $3,000 to $4,000 a week. "
            f"Do you have 2 minutes for a quick quote?"
        )
        filename = "saludo_nuevo.mp3"
        path = f"./static/{filename}"

        # Eliminar si ya existía
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

        print("⏳ Generando saludo con voz clonada...")
        audio_url = generar_audio_elevenlabs(saludo, filename)

        for _ in range(10):
            if os.path.exists(path):
                break
            time.sleep(0.5)

        if os.path.exists(path) and audio_url:
            print("✅ Saludo listo:", audio_url)
            response.play(audio_url)
        else:
            print("⚠️ No se pudo generar el audio, usando fallback.")
            response.say(saludo)

        data["step"] += 1
        return str(response)

    # --- Pasos siguientes: recolectar respuestas y avanzar ---
    elif data["step"] <= len(data["preguntas"]):
        key, pregunta = data["preguntas"][data["step"] - 1]

        if speech_result:
            data["responses"][key] = speech_result
            data["step"] += 1

        if data["step"] <= len(data["preguntas"]):
            key, pregunta = data["preguntas"][data["step"] - 1]
            filename = f"step{data['step']}.mp3"
            generar_audio_elevenlabs(pregunta, filename)
            audio_url = f"{request.url_root}static/{filename}"
            response.play(audio_url)
        else:
            despedida = "Great, give me a second to connect you with a licensed agent."
            generar_audio_elevenlabs(despedida, "despedida.mp3")
            audio_url = f"{request.url_root}static/despedida.mp3"
            response.play(audio_url)

            enviar_correo(data["responses"])
            dial = Dial(caller_id=request.values.get("To"))
            dial.number(FORWARD_NUMBER)
            response.append(dial)

    # --- Gather para capturar respuesta ---
    gather = Gather(input="speech", action=request.url, method="POST", timeout=6)
    beep_path = "./static/beep_prompt.mp3"
    if not os.path.exists(beep_path):
        generar_audio_elevenlabs("Alright, go ahead and answer now.", "beep_prompt.mp3")
    beep_url = f"{request.url_root}static/beep_prompt.mp3"
    gather.play(beep_url)
    response.append(gather)

    return str(response)

# --- Servir archivos estáticos ---
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# --- Ejecutar App ---
def encontrar_puerto_libre(puerto_inicial=5001, puerto_final=5010):
    for port in range(puerto_inicial, puerto_final + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("localhost", port)) != 0:
                return port
    raise RuntimeError("❌ No hay puertos disponibles entre 5001 y 5010.")

@app.route("/")
def home():
    return "🚀 AI Agent está corriendo correctamente."

if __name__ == "__main__":
    port = encontrar_puerto_libre()
    print(f"🚀 Ejecutando en puerto libre: {port}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)