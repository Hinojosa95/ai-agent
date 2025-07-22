from twilio.rest import Client
import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Inicializar cliente Twilio
client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Crear llamada
call = client.calls.create(
    to="+12816195256",  # Reemplaza esto con tu número real para pruebas
    from_=os.getenv("TWILIO_PHONE_NUMBER"),
    url="https://cad8f5b26d11.ngrok-free.app"  # Si usas ngrok, reemplaza con el dominio público
)

print(f"Llamada iniciada. SID: {call.sid}")