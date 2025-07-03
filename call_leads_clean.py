import pandas as pd
from twilio.rest import Client
import os
import time
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ai_agent_url = "https://ai-agent-01hn.onrender.com/voice"  # Tu URL de Render

client = Client(account_sid, auth_token)

# Cargar leads
df = pd.read_csv("nv_30days_070225.csv")

# Iterar sobre los leads
for index, row in df.iterrows():
    if "Phone" not in row or pd.isnull(row["Phone"]):
        continue

    rep = row["Company_Rep1"] if pd.notnull(row["Company_Rep1"]) else row.get("Company_Rep2", "there")
phone = str(row["Phone"]).strip()

if not phone.startswith("+"):
    phone = "+1" + phone # agregar código de país si falta

    print(f"Llamando a {rep} al número {phone}...")

    try:
        call = client.calls.create(
            to=phone,
            from_=twilio_number,
            url=f"{ai_agent_url}?rep={rep}"
        )
        print(f"✅ Llamada iniciada. SID: {call.sid}")
    except Exception as e:
        print(f"❌ Error al llamar a {phone}: {e}")

    time.sleep(3)  # Pausa entre llamadas
