from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.message import EmailMessage
import openai

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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
        try:
            base_url = request.url_root
        except RuntimeError:
            base_url = "http://localhost:5000/"
        return f"{base_url}static/{filename}"
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

# --- Helper: GPT respuesta ---
def obtener_respuesta_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un agente de seguros amable y profesional que hace preguntas para cotizar un seguro de camión."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Error GPT:", e)
        return "Lo siento, hubo un error."

# --- Ruta Principal ---
@app.route("/voice", methods=['POST'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    rep_name = request.args.get("rep", "there")

    data = client_data.setdefault(from_number, {
        "step": 0,
        "responses": {},
        "lang": "en"
    })

    preguntas = [
        "What year, make and model is your truck?",
        "Can you provide the VIN number?",
        "What is your date of birth?",
        "What is your driver’s license number?"
    ]

    keys = ["truck", "vin", "dob", "license"]

    if data['step'] > 0 and speech_result:
        clave = keys[data['step'] - 1]
        data['responses'][clave] = speech_result

    response = VoiceResponse()

    if data['step'] == 0:
        saludo = obtener_respuesta_gpt(f"Saluda como Bryan y explica brevemente que necesitas información para cotizar el seguro del camión del cliente. Dilo en inglés.")
        audio_url = generar_audio_elevenlabs(saludo, "saludo.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(saludo)

    elif data['step'] < len(preguntas):
        pregunta = preguntas[data['step']]
        audio_url = generar_audio_elevenlabs(pregunta, f"step{data['step']}.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(pregunta)

    else:
        resumen = "Here is the client's information: " + json.dumps(data['responses'])
        despedida = obtener_respuesta_gpt(f"Gracias por la información. Ahora te transferiré con un agente humano. Este es el resumen: {resumen}. Despídete brevemente y amablemente.")
        audio_url = generar_audio_elevenlabs(despedida, "despedida.mp3")
        if audio_url:
            response.play(audio_url)
        else:
            response.say(despedida)

        enviar_correo(data['responses'])
        dial = Dial(caller_id=request.values.get("To"))
        dial.number(FORWARD_NUMBER)
        response.append(dial)

    gather = Gather(input="speech", action="/voice", method="POST", timeout=6)
    gather.say("Please say your answer after the beep.", voice="Polly.Matthew")
    response.append(gather)

    data['step'] += 1
    return str(response)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)