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

# --- Audio Helper ---
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
        try:
            base_url = request.url_root
        except RuntimeError:
            base_url = "http://localhost:5000/"
        return f"{base_url}static/{filename}"
    else:
        print("❌ Error generando audio:", response.text)
        return None

# --- Email Helper ---
def enviar_correo(datos):
    msg = EmailMessage()
    msg['Subject'] = f"Nuevo lead: {datos.get('truck', 'Sin nombre')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    cuerpo = "\n".join([f"{k}: {v}" for k, v in datos.items()])
    msg.set_content(f"Se ha recolectado la siguiente información:\n\n{cuerpo}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("✅ Correo enviado correctamente")
    except Exception as e:
        print("❌ Error al enviar el correo:", e)

# --- Twilio Voice Webhook ---
@app.route("/voice", methods=['POST'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    rep_name = request.args.get("rep", "there")

    if from_number not in client_data:
        lang = "en"
        try:
            lang = detect(speech_result or "hola")
        except:
            pass

        greeting_en = f"""
Hi {rep_name}, this is Bryan. I'm calling because I help truckers save up to $500 per month per truck on insurance,
get dispatching at just 4%, earn from $3,000 to $4,000 a week.
Do you have two minutes for a quick quote?
I have your DOT number. Could you confirm the year, make, and model of your truck?
Then, I’ll need your VIN number, your date of birth, and your driver’s license number.
At the end, I’ll bring a licensed agent on the line to go over the numbers.
What’s the make and model of your truck?
"""

        greeting_es = f"""
Hola {rep_name}, soy Bryan. Ayudo a camioneros a ahorrar hasta $500 al mes por camión en seguros,
a obtener despacho por solo 4%, ganar de $3,000 a $4,000 por semana.
¿Tienes 2 minutos para una cotización rápida?
Empecemos: ¿Cuál es la marca y modelo de tu camión?
"""

        greeting = greeting_es if lang.startswith("es") else greeting_en
        client_data[from_number] = {
            "lang": lang,
            "step": 0,
            "responses": {},
            "greeting": greeting
        }

    data = client_data[from_number]
    pasos = [
        ("truck", "What year, make and model is your truck?" if data['lang'] == 'en' else "¿Cuál es el año, marca y modelo de tu camión?"),
        ("vin", "Can you provide the VIN number?" if data['lang'] == 'en' else "¿Cuál es el número VIN del camión?"),
        ("dob", "What is your date of birth?" if data['lang'] == 'en' else "¿Cuál es tu fecha de nacimiento?"),
        ("license", "And your driver’s license number?" if data['lang'] == 'en' else "¿Cuál es tu número de licencia de conducir?")
    ]

    if speech_result and data['step'] > 0:
        key, _ = pasos[data['step'] - 1]
        data['responses'][key] = speech_result

    response = VoiceResponse()

    if data['step'] == 0:
        audio_url = generar_audio_elevenlabs(data['greeting'], "greeting.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(data['greeting'], voice="Polly.Matthew")

        gather = Gather(input="speech", action="/voice", method="POST", timeout=6)
        gather.say(pasos[0][1], voice="Polly.Matthew")
        response.append(gather)
        data['step'] += 1

    elif data['step'] < len(pasos):
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
        response.say("Thank you. Connecting you now with a licensed agent.", voice="Polly.Matthew")
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