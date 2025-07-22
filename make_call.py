from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+12816195256",  # reemplaza con tu número de prueba
    from_=twilio_number,
    url="https://ai-agent-01hn.onrender.com/voice"  # <--- correcto
)

print("✅ Llamada realizada:", call.sid)