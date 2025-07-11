import csv
import time
import os
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

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

    rep_name = lead.get("Company_Rep1") or lead.get("Company_Rep2") or "there"

    try:
        call = client.calls.create(
            twiml=f'<Response><Redirect method="POST">https://ai-agent-01hn.onrender.com/voice?rep={rep_name}</Redirect></Response>',
            to=phone,
            from_=TWILIO_NUMBER
        )
        print(f"✅ Llamada iniciada a {phone}")
        reporte.append({
            "timestamp": datetime.now().isoformat(),
            "lead": rep_name,
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
with open("reporte_llamadas.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["timestamp", "lead", "phone", "status", "call_sid"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in reporte:
        writer.writerow(row)

print("📋 Reporte diario guardado en reporte_llamadas.csv")