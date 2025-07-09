# call_single_lead.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# --- Configuración desde .env ---
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

# --- URL del agente AI ---
# Puedes personalizar el nombre del representante y agregar un parámetro de origen para pruebas
ai_agent_url = "https://ai-agent-01hn.onrender.com/voice?rep=Bryan&source=prueba"

# --- Número al que deseas llamar ---
target_number = "+12816195256"  # Cámbialo si quieres probar con otro número verificado

# --- Inicializar el cliente de Twilio ---
client = Client(account_sid, auth_token)

# --- Hacer la llamada ---
print(f"📞 Iniciando llamada a {target_number} desde {twilio_number}...")

try:
    call = client.calls.create(
        to=target_number,
        from_=twilio_number,
        url=ai_agent_url
    )
    print(f"✅ Llamada iniciada correctamente. SID: {call.sid}")
except Exception as e:
    print("❌ Error al intentar iniciar la llamada:")
    print(e)