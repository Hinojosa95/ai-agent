import csv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
from dotenv import load_dotenv
import requests
import time

load_dotenv()

# Configuración
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
FORWARD_NUMBER = os.getenv("FORWARD_NUMBER")

client = Client(account_sid, auth_token)

# Cargar el lead
with open('nv_30days_070225.csv', newline='') as f:
    reader = csv.DictReader(f)
    lead = next(reader)

# Obtener nombre del cliente
name = lead.get("Company_Rep1") or lead.get("Company_Rep2") or "there"

# Texto del mensaje inicial
initial_script = (
    f"Hi {name}, this is Bryan. I help truckers save up to $500 per month per truck on insurance, "
    "get dispatching at just 4%, earn $3,000 to $4,000 a week, access gas cards with $2,500 credit, "
    "and get help financing your down payment. Do you have 2 minutes for a quick quote?"
)

# Guardar texto para usar desde la app
with open("mensaje_inicial.txt", "w") as f:
    f.write(initial_script)

# Hacer la llamada
call = client.calls.create(
    twiml=f'<Response><Redirect method="POST">https://ai-agent-01hn.onrender.com/voice?rep={name}</Redirect></Response>',
    to=lead["Phone""],
    from_=twilio_number
)

print(f"📞 Llamando a {name} al número {lead['Phone Number']}...")
print("SID de llamada:", call.sid)