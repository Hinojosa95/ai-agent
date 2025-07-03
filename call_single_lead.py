# call_single_lead.py
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Configuración desde variables de entorno
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ai_agent_url = "https://ai-agent-01hn.onrender.com/voice?rep=Bryan"  # Puedes personalizar el nombre

# Cliente de Twilio
client = Client(account_sid, auth_token)

# Número al que se le llamará
target_number = "+12816195256"

print(f"Llamando a {target_number}...")

try:
    call = client.calls.create(
        to=target_number,
        from_=twilio_number,
        url=ai_agent_url
    )
    print(f"✅ Llamada iniciada. SID: {call.sid}")
except Exception as e:
    print(f"❌ Error al llamar a {target_number}:\n{e}")
