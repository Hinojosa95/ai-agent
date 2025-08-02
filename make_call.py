from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

# ✅ Dirección pública en Render (ajústala si usas otra)
url = "https://ai-agent-01hn.onrender.com/voice"

try:
    call = client.calls.create(
        to="+12816195256",  # 🔁 ← Reemplaza con tu número de prueba
        from_=twilio_number,
        url=url
    )
    print("📞 Llamada realizada con SID:", call.sid)
except Exception as e:
    print("❌ Error al realizar la llamada:", e)