from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import openai, requests, os, uuid

load_dotenv()
app = Flask(__name__)

TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_URL = "https://ai-agent-01hn.onrender.com"

# Inicializar variable global (vacía por ahora)
GREETING_URL = ""

@app.route("/voice", methods=["GET", "POST"])
def voice():
    print("🟢 Reproduciendo saludo inicial:", GREETING_URL)

    response = VoiceResponse()
    response.play(GREETING_URL)
    response.pause(length=1)

    gather = response.gather(
        input="speech",
        action=f"{BASE_URL}/process_speech",
        method="POST",
        timeout=15,
        speech_timeout="auto",
        actionOnEmptyResult=True
    )

    return str(response), 200, {"Content-Type": "text/xml"}

@app.route("/process_speech", methods=["POST"])
def process_speech():
    print("🔍 Datos recibidos en /process_speech:")
    for key in request.values:
        print(f"{key} = {request.values.get(key)}")

    speech = request.values.get("SpeechResult", "").strip()
    print("🗣️ Cliente dijo:", speech)

    response = VoiceResponse()

    if not speech:
        print("⚠️ No se recibió entrada de voz.")
        response.say("Sorry, I didn't hear anything. Let's try again.")
        response.redirect(f"{BASE_URL}/voice")
        return str(response), 200, {"Content-Type": "text/xml"}

    try:
        prompt = f"Client: {speech}\nAgent:"
        gpt_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful insurance agent for truckers."},
                {"role": "user", "content": prompt}
            ]
        )
        reply = gpt_response.choices[0].message.content.strip()
        print("🤖 GPT responde:", reply)
    except Exception as e:
        print(f"❌ Error GPT: {e}")
        response.say("Sorry, there was a problem generating the response.")
        return str(response), 200, {"Content-Type": "text/xml"}

    audio_url = generate_audio(reply)
    if not audio_url:
        response.say("Sorry, I couldn't generate the audio response.")
        return str(response), 200, {"Content-Type": "text/xml"}

    response.play(audio_url)
    response.pause(length=1)

    gather = response.gather(
        input="speech",
        action=f"{BASE_URL}/process_speech",
        method="POST",
        timeout=15,
        speech_timeout="auto",
        actionOnEmptyResult=True
    )

    return str(response), 200, {"Content-Type": "text/xml"}

def generate_audio(text, filename=None):
    if not filename:
        filename = f"response_{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(res.content)
        print("✅ Audio generado:", filename)
        return f"{BASE_URL}/static/{filename}"
    else:
        print("❌ Error generando audio:", res.status_code, res.text)
        return None

@app.route('/static/<path:filename>')
def serve_audio(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    # Crear carpeta static si no existe
    if not os.path.exists("static"):
        os.makedirs("static")
    
    # Crear saludo y guardar global
    greeting_filename = f"greeting_{uuid.uuid4()}.mp3"
    GREETING_URL = generate_audio("Hi, this is Bryan. Do you have 2 minutes for a quick quote?", greeting_filename)

    app.run(debug=False, host="0.0.0.0", port=5001)