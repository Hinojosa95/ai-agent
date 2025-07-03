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

# Cargar leads
df = pd.read_csv("nv_30days_070225.csv")

# Omitir filas sin número
df = df[df["Phone"].notnull()]

# Iterar uno por uno
for index, row in df.iterrows():
    rep = row["Company_Rep1"] if pd.notnull(row["Company_Rep1"]) else row.get("Company_Rep2", "there")
    phone = str(row["Phone"])

    if not phone.startswith("+1"):
        phone = "+1" + phone

    print(f"📞 Llamando a {rep} al número {phone}...")

    try:
        call = client.calls.create(
            to=phone,
            from_=twilio_number,
            url=f"{ai_agent_url}?rep={rep}"
        )
        print(f"⏳ Esperando que termine la llamada. SID: {call.sid}")

        while True:
            status = client.calls(call.sid).fetch().status
            print(f"🌀 Estado de la llamada: {status}")
            if status in ["completed", "no-answer", "busy", "failed", "canceled"]:
                print(f"✅ Llamada finalizada con estado: {status}\n")
                break
            time.sleep(5)

    except Exception as e:
        print(f"❌ Error al llamar a {phone}: {e}")
