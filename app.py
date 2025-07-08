from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
from chat_agent import get_response
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
    speech_result = request.values.get("SpeechResult", "")
    rep_name = request.args.get("rep", "there")

    greeting_en = f"""You are a helpful sales agent for truck insurance. Start the call by saying:
    'Hi {rep_name}, my name is Bryan, and I help truckers save up to 500 dollars a month on truck insurance, pick up a rental for 500 dollars a week, and secure them with high-paying loads. Do you have 2 minutes for a quick quote?'

    Then ask for the following, one by one, and wait for answers in between:

    1. What is the VIN number of your truck?
    2. What is the make, model, and type of your truck?
    3. What is your date of birth?
    4. What is your driver's license number?

    End by saying: 'Thank you. I’ll transfer you now to one of our agents.'
    """

    greeting_es = f"""Eres un agente de ventas de seguros para camiones. Comienza la llamada diciendo:
    'Hola {rep_name}, mi nombre es Bryan. Ayudo a los camioneros a ahorrar hasta 500 dólares al mes en seguros, rentar un camión por 500 a la semana y conseguir cargas bien pagadas. ¿Tienes 2 minutos para una cotización rápida?'

    Luego pregunta, una por una:

    1. ¿Cuál es el número de serie (VIN) de tu camión?
    2. ¿Qué marca, modelo y tipo es tu camión?
    3. ¿Cuál es tu fecha de nacimiento?
    4. ¿Cuál es tu número de licencia?

    Termina diciendo: 'Gracias. Ahora te transfiero con uno de nuestros agentes.'
    """

    # Inicializar cliente si no está registrado
    if from_number not in client_data:
        lang = "en"
        if speech_result:
            try:
                lang = detect(speech_result)
            except:
                lang = "en"

        voice = "Polly.Miguel" if lang.startswith("es") else "Polly.Joanna"
        greeting = greeting_es if lang.startswith("es") else greeting_en

        client_data[from_number] = {
            "messages": [{"role": "system", "content": greeting}],
            "responses": {},
            "voice": voice
        }

        # Enviar saludo inicial
        reply = greeting.split("Then ask")[0].split("Luego pregunta")[0].strip()

    else:
        reply = "Hi, thank you for calling. How can I help you today?"

    # Procesar lo que dijo el usuario
    if speech_result:
        client_data[from_number]["messages"].append({"role": "user", "content": speech_result})
        reply = get_response(client_data[from_number]["messages"])
        client_data[from_number]["messages"].append({"role": "assistant", "content": reply})

        # Guardar respuestas
        if "vin" in speech_result.lower() or len(speech_result.strip()) == 17:
            client_data[from_number]["responses"]["VIN"] = speech_result
        elif any(word in speech_result.lower() for word in ["freightliner", "kenworth", "peterbilt", "mack", "volvo"]):
            client_data[from_number]["responses"]["truck_info"] = speech_result
        elif any(char.isdigit() for char in speech_result) and "/" in speech_result:
            client_data[from_number]["responses"]["dob"] = speech_result
        elif len(speech_result) >= 6 and any(x in speech_result.lower() for x in ["licens", "número", "numero"]):
            client_data[from_number]["responses"]["license"] = speech_result

    # Verificar si se debe transferir
    if any(word in speech_result.lower() for word in ["agent", "cotizar", "quote", "transfer", "speak", "hablar"]):
        responses = client_data[from_number].get("responses", {})
        vin = responses.get("VIN", "No proporcionado")
        truck = responses.get("truck_info", "No proporcionado")
        dob = responses.get("dob", "No proporcionado")
        license_num = responses.get("license", "No proporcionado")

        # Enviar correo con los datos
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        email_receiver = os.getenv("EMAIL_RECEIVER")

        subject = "Lead transferido a agente"
        body = f"""
📞 Información del lead:

📱 Número de teléfono: {from_number}
🆔 VIN: {vin}
🚚 Truck Info: {truck}
🎂 Fecha de nacimiento: {dob}
🪪 Licencia: {license_num}

¡Transferido automáticamente por el AI Agent!
"""

        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Error enviando correo: {e}")

        response = VoiceResponse()
        response.say("Thank you. Transferring you now.", voice=client_data[from_number]["voice"])
        response.dial(os.getenv("FORWARD_NUMBER"))
        return str(response)

    # Generar respuesta hablada
    response = VoiceResponse()
    gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
    gather.say(reply, voice=client_data[from_number]["voice"])
    response.append(gather)
    return str(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
