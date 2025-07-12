import csv
import time
import os
import urllib.parse
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    raise ValueError("❌ Error: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN o TWILIO_PHONE_NUMBER no están configuradas.")


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

csv_file = "nv_30days_070225.csv"
max_calls_per_day = 700
call_interval_seconds = 10
reporte = []

with open(csv_file, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    leads = list(reader)

call_count = 0
for lead in leads:
    if call_count >= max_calls_per_day:
        break

    phone = lead.get("Phone", "").strip()
    if not phone:
        continue
    if not phone.startswith("+"):
        phone = "+1" + phone

    rep_name_raw = lead.get("Company_Rep1") or lead.get("Company_Rep2") or "there"
    rep_name_encoded = quote_plus(rep_name_raw)

    try:
        call = client.calls.create(
        twiml=f'<Response><Redirect method="POST">https://ai-agent-01hn.onrender.com/voice?rep={rep_name_encoded}</Redirect></Response>',
        to=phone,
        from_=TWILIO_PHONE_NUMBER
    )
        
        print(f"✅ Llamada iniciada a {phone}")
        reporte.append({
            "timestamp": datetime.now().isoformat(),
            "lead": rep_name_raw,
            "phone": phone,
            "status": "Llamada iniciada",
            "call_sid": call.sid
        })
        call_count += 1
        time.sleep(call_interval_seconds)

    except Exception as e:
        print(f"❌ Error llamando a {phone}: {e}")
        reporte.append({
            "timestamp": datetime.now().isoformat(),
            "lead": rep_name,
            "phone": phone,
            "status": f"Error: {e}"
        })

# Guardar reporte
filename = f"reporte_llamadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open("reporte_llamadas.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["timestamp", "lead", "phone", "status", "call_sid"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in reporte:
        writer.writerow(row)

print("📋 Reporte diario guardado en reporte_llamadas.csv")