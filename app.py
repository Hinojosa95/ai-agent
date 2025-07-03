from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
from chat_agent import get_response

load_dotenv()

app = Flask(__name__)
client_data = {}

@app.route("/voice", methods=['POST', 'GET'])
def voice():
    from_number = request.values.get("From")
    rep_name = request.args.get("rep", "there")

    # Script de introducción
    greeting = f"Hi {rep_name}, my name is Bryan, and I help truckers save up to 500 dollars a month on truck insurance, pick up a rental for 500 dollars a week, and secure them with high-paying loads. Do you have 2 minutes for a quick quote?"

    # Crear historial del cliente si no existe
    if from_number not in client_data:
        client_data[from_number] = {
            "messages": [{"role": "system", "content": f"You are a sales agent for truck insurance. Start the call by saying: '{greeting}'"}],
        }

    # Obtener lo que dijo el usuario (speech-to-text)
    speech_result = request.values.get("SpeechResult", "").lower()

    # Lógica de conversación
    if speech_result:
        client_data[from_number]["messages"].append({"role": "user", "content": speech_result})
        reply = get_response(client_data[from_number]["messages"])
        client_data[from_number]["messages"].append({"role": "assistant", "content": reply})
    else:
        reply = greeting  # Primer mensaje si es la primera vuelta

    # Si menciona que quiere hablar con alguien, transferimos
    if any(word in speech_result for word in ["agent", "speak", "cotizar", "quote", "transfer", "help"]):
        response = VoiceResponse()
        response.say("One moment please, I’ll transfer you to a live agent.")
        response.dial(os.getenv("FORWARD_NUMBER"))
        return str(response)

    # Continuar recogiendo la conversación
    response = VoiceResponse()
    gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
    gather.say(reply)
    response.append(gather)

    return str(response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
