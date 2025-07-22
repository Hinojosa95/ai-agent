from flask import Flask, request, send_from_directory
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import requests, os

load_dotenv()

app = Flask(__name__)

TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

@app.route('/static/greeting.mp3')
def serve_audio():
    return send_from_directory('static', 'greeting.mp3')

@app.route("/voice", methods=["GET", "POST"])
def voice():
    audio_url = request.url_root + "static/greeting.mp3"
    print("🟢 URL del audio para Twilio:", audio_url)

    response = VoiceResponse()
    response.play(url=audio_url)
    response.pause(length=5)
    return str(response)

def generate_greeting(text="Hi, this is Bryan, and I help trucks pay as low as 800 dollars per month on truck insurance, and secure dispatching to help that will garantee you make 3 to 4 thousand a week. do you have 2 minutes for a quick quote?"):
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
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        if not os.path.exists("static"):
            os.makedirs("static")
        with open("static/greeting.mp3", "wb") as f:
            f.write(response.content)
        print("✅ greeting.mp3 generado.")
    else:
        print(f"❌ Error generando greeting: {response.status_code} - {response.text}")

if __name__ == "__main__":
    generate_greeting()  # ⚠️ Solo ejecútalo manualmente si necesitas regenerar el audio
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=5001)