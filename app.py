from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
from langdetect import detect
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)
client_data = {}

@app.route("/voice", methods=['POST', 'GET'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "").strip()
    rep_name = request.args.get("rep", "there")

    # Idiomas
    greeting_en = f"""<speak><prosody rate="85%">Hi {rep_name}, my name is Bryan. I help truckers save up to $500 a month on insurance, rent trucks for $500 a week, and get high-paying loads. Do you have 2 minutes for a quick quote?</prosody></speak>"""
    greeting_es = f"""<speak><prosody rate="85%">Hola {rep_name}, mi nombre es Bryan. Ayudo a los camioneros a ahorrar hasta 500 dólares al mes en seguros, rentar camiones por 500 a la semana y conseguir cargas bien pagadas. ¿Tienes 2 minutos para una cotización rápida?</prosody></speak>"""

    questions_en = [
        "What is the VIN number of your truck?",
        "What is the make, model, and type of your truck?",
        "What is your date of birth?",
        "What is your driver's license number?"
    ]

    questions_es = [
        "¿Cuál es el número de serie VIN de tu camión?",
        "¿Qué marca, modelo y tipo es tu camión?",
        "¿Cuál es tu fecha de nacimiento?",
        "¿Cuál es tu número de licencia?"
    ]

    if from_number not in client_data:
        lang = detect(speech_result) if speech_result else "en"
        is_spanish = lang.startswith("es")

        client_data[from_number] = {
            "step": 0,
            "responses": {},
            "lang": "es" if is_spanish else "en",
            "voice": "Polly.Miguel" if is_spanish else "Polly.Joanna"
        }

        # Greeting inicial
        response = VoiceResponse()
        gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
        greet_text = greeting_es if is_spanish else greeting_en
        gather.say(greet_text, voice=client_data[from_number]["voice"], language="es-MX" if is_spanish else "en-US")
        response.append(gather)
        return str(response)

    # Guardar respuesta anterior si existía
    step = client_data[from_number]["step"]
    if speech_result:
        if step == 0:
            client_data[from_number]["responses"]["vin"] = speech_result
        elif step == 1:
            client_data[from_number]["responses"]["truck"] = speech_result
        elif step == 2:
            client_data[from_number]["responses"]["dob"] = speech_result
        elif step == 3:
            client_data[from_number]["responses"]["license"] = speech_result

    # Avanzar al siguiente paso
    client_data[from_number]["step"] += 1
    step = client_data[from_number]["step"]
    lang = client_data[from_number]["lang"]
    voice = client_data[from_number]["voice"]

    if step < 4:
        question = questions_es[step] if lang == "es" else questions_en[step]
        response = VoiceResponse()
        gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
        gather.say(question, voice=voice, language="es-MX" if lang == "es" else "en-US")
        response.append(gather)
        return str(response)

    # Transferencia
    data = client_data[from_number]["responses"]
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    body = f"""
📞 Información del lead:

📱 Número: {from_number}
🆔 VIN: {data.get('vin', 'No proporcionado')}
🚚 Truck: {data.get('truck', 'No proporcionado')}
🎂 Fecha de nacimiento: {data.get('dob', 'No proporcionado')}
🪪 Licencia: {data.get('license', 'No proporcionado')}
"""

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_receiver
    msg['Subject'] = "🔁 Lead transferido a agente"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("❌ Error al enviar correo:", e)

    # Transferencia
    response = VoiceResponse()
    response.say("Thank you. Transferring you now.", voice=voice)
    response.dial(os.getenv("FORWARD_NUMBER"))
    return str(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
