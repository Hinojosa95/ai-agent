import pandas as pd
from twilio.rest import Client
import os
import time
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ai_agent_url = "https://ai-agent-01hn.onrender.com/voice"

client = Client(account_sid, auth_token)

df = pd.read_csv("nv_30days_070225.csv")

for index, row in df.iterrows():
    rep = row["Company_Rep1"] if pd.notnull(row["Company_Rep1"]) else row.get("Company_Rep2", "there")
    phone = row["Phone"]

    # Asegurarse que el número tenga formato correcto
    if not str(phone).startswith("+1"):
        phone = "+1" + str(phone)

    print(f"Llamando a {rep} al número {phone}...")

    try:
        call = client.calls.create(
            to=phone,
            from_=twilio_number,
            url=f"{ai_agent_url}?rep={rep}"
        )

        print(f"Llamada iniciada. SID: {call.sid}")
        
        # Esperar a que termine la llamada
        while True:
            status = client.calls(call.sid).fetch().status
            print(f"Estado de la llamada: {status}")
            if status in ["completed", "canceled", "failed", "busy", "no-answer"]:
                print(f"✅ Llamada a {phone} finalizada con estado: {status}")
                break
            time.sleep(5)  # Esperar 5 segundos antes de revisar de nuevo

    except Exception as e:
        print(f"❌ Error al llamar a {phone}: {e}")
