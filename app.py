from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
import os
from dotenv import load_dotenv
from langdetect import detect
import requests
import smtplib
from email.message import EmailMessage

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
    if os.path.exists(f"./static/{filename}"):
        os.remove(f"./static/{filename}")

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
        "step": 0,
        "responses": {}
    })

    pasos = [
        ("greeting", f"Hi {rep_name}, this is Bryan. I help truckers save up to $500 per month per truck on insurance, get dispatching at just 4%, earn $3,000–$4,000 a week, access gas cards with $2,500 credit, and get help financing your down payment. Do you have 2 minutes for a quick quote?"),
        ("truck", "What year, make and model is your truck?"),
        ("vin", "Can you provide the VIN number?"),
        ("dob", "What is your date of birth?"),
        ("license", "And your driver’s license number?")
    ]

    if speech_result and data['step'] > 0:
        key, _ = pasos[data['step'] - 1]
        data['responses'][key] = speech_result

    response = VoiceResponse()

    if data['step'] < len(pasos):
        key, texto = pasos[data['step']]
        audio_url = generar_audio_elevenlabs(texto, f"step_{key}.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(texto, voice="Polly.Matthew")

        if key != "greeting":
            gather = Gather(input="speech", action="/voice", method="POST", timeout=6)
            gather.say(texto, voice="Polly.Matthew")
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