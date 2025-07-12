from dotenv import load_dotenv
import os

# Cargar .env explícitamente
load_dotenv(dotenv_path=".env")

# Imprimir valores para verificar
print("TWILIO_SID =", os.getenv("TWILIO_SID"))
print("TWILIO_AUTH_TOKEN =", os.getenv("TWILIO_AUTH_TOKEN"))
print("TWILIO_PHONE_NUMBER =", os.getenv("TWILIO_PHONE_NUMBER"))