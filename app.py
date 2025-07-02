from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
from chat_agent import get_response

load_dotenv()

app = Flask(__name__)
client_data = {}

@app.route("/voice", methods=['POST'])
def voice():
    from_number = request.form.get("From")
    speech_result = request.form.get("SpeechResult", "").strip().lower()

    if from_number not in client_data:
        client_data[from_number] = {
            "messages": [{"role": "system", "content": "Eres un agente de seguros. Pregunta nombre, tipo de seguro que busca, y si está listo para cotizar. Transfiere si está interesado."}],
        }

    if speech_result:
        client_data[from_number]["messages"].append({"role": "user", "content": speech_result})
        reply = get_response(client_data[from_number]["messages"])
        client_data[from_number]["messages"].append({"role": "assistant", "content": reply})
    else:
        reply = "Hola, gracias por llamar. ¿En qué puedo ayudarte hoy?"

    if "hablar" in speech_result or "agente" in speech_result or "cotizar" in speech_result:
        response = VoiceResponse()
        response.say("Un momento, te transfiero con un agente.")
        response.dial(os.getenv("FORWARD_NUMBER"))
        return str(response)

    response = VoiceResponse()
    gather = Gather(input="speech", action="/voice", method="POST", timeout=5)
    gather.say(reply)
    response.append(gather)
    return str(response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
