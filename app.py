from flask import Flask, request, Response
import os
from dotenv import load_dotenv
from chat_agent import get_response
from langdetect import detect
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.twiml.voice_response import VoiceResponse, Gather

load_dotenv()
app = Flask(__name__)
client_data = {}

@app.route("/voice", methods=['POST', 'GET'])
def voice():
    from_number = request.values.get("From")
    speech_result = request.values.get("SpeechResult", "")
    rep_name = request.args.get("rep", "there")

    if from_number not in client_data:
        lang = detect(speech_result) if speech_result else "en"
        voice = "Polly.Miguel" if lang.startswith("es") else "Polly.Joanna"
        greeting = f"""Hola {rep_name}, soy Bryan. Ayudo a los camioneros a ahorrar hasta $500 al mes en seguros, rentar un camión por $500 a la semana y conseguir cargas bien pagadas. ¿Tienes 2 minutos para una cotización rápida?""" if lang.startswith("es") else f"""Hi {rep_name}, this is Bryan. I help truckers save up to $500/month on insurance, get rentals for $500/week, and secure high-paying loads. Do you have 2 minutes for a quick quote?"""

        client_data[from_number] = {
            "messages": [{"role": "system", "content": greeting}],
            "responses": {},
            "voice": voice
        }

        response = VoiceResponse()
        gather = Gather(input="speech", action="/voice", method="POST", timeout=3)
        gather.say(greeting, voice=voice)
        response.append(gather)
        return str(response)

    if speech_result:
        client_data[from_number]["messages"].append({"role": "user", "content": speech_result})
        reply = get_response(client_data[from_number]["messages"])
        client_data[from_number]["messages"].append({"role": "assistant", "content": reply})

        # Detectar información
        if "vin" in speech_result.lower() or len(speech_result.strip()) == 17:
            client_data[from_number]["responses"]["VIN"] = speech_result
        elif any(word in speech_result.lower() for word in ["freightliner", "kenworth", "peterbilt", "mack", "volvo"]):
            client_data[from_number]["responses"]["truck_info"] = speech_result
        elif any(char.isdigit() for char in speech_result) and "/" in speech_result:
            client_data[from_number]["responses"]["dob"] = speech_result
        elif len(speech_result) >= 6 and any(x in speech_result.lower() for x in ["licens", "número", "numero"]):
            client_data[from_number]["responses"]["license"] = speech_result

        # Transferencia
        if any(word in speech_result.lower() for word in ["agent", "cotizar", "quote", "transfer", "speak", "hablar"]):
            send_email_with_info(from_number)
            response = VoiceResponse()
            response.say("Gracias. Transfiriendo la llamada.", voice=client_data[from_number]["voice"])
            response.dial(os.getenv("FORWARD_NUMBER"))
            return str(response)

        # Respuesta regular
        response = VoiceResponse()
        gather = Gather(input="speech", action="/voice", method="POST", timeout=3)
        gather.say(reply, voice=client_data[from_number]["voice"])
        response.append(gather)
        return str(response)

    # Si no hay respuesta
    response = VoiceResponse()
    response.say("¿Hola? ¿Sigues ahí?", voice=client_data[from_number]["voice"])
    return str(response)

def send_email_with_info(phone):
    data = client_data.get(phone, {})
    info = data.get("responses", {})
    vin = info.get("VIN", "No proporcionado")
    truck = info.get("truck_info", "No proporcionado")
    dob = info.get("dob", "No proporcionado")
    license_num = info.get("license", "No proporcionado")

    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_receiver
    msg['Subject'] = "📞 Lead transferido a agente"
    body = f"""
📱 Teléfono: {phone}
🆔 VIN: {vin}
🚛 Camión: {truck}
🎂 Nacimiento: {dob}
🪪 Licencia: {license_num}
"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("❌ Error enviando correo:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
