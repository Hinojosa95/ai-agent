import pandas as pd
from twilio.rest import Client
import os
from dotenv import load_dotenv
import csv
from datetime import datetime, time as dt_time
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
ai_agent_url = "https://ai-agent-01hn.onrender.com/voice"

client = Client(account_sid, auth_token)

# Cargar leads
df = pd.read_csv("nv_30days_070225.csv")

# Crear archivo de log si no existe
log_file = "llamadas_log.csv"
if not os.path.exists(log_file):
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Fecha", "Nombre", "Teléfono", "SID"])

def dentro_de_horario():
    ahora = datetime.now().time()
    return dt_time(8, 0) <= ahora <= dt_time(17, 0)

llamadas_realizadas = 0
MAX_LLAMADAS_DIARIAS = 700

for index, row in df.iterrows():
    if llamadas_realizadas >= MAX_LLAMADAS_DIARIAS:
        print("✅ Se alcanzó el límite diario de llamadas.")
        break

    while not dentro_de_horario():
        print("⏳ Fuera de horario. Esperando a que sea entre 8:00am y 5:00pm...")
        time.sleep(300)  # Esperar 5 minutos

    rep = row["Company_Rep1"] if pd.notnull(row["Company_Rep1"]) else row.get("Company_Rep2", "there")
    phone = str(row["Phone"])

    if not phone.startswith("+1"):
        phone = "+1" + phone

    print(f"\n📞 Llamando a {rep} al número {phone}...")

    try:
        call = client.calls.create(
            to=phone,
            from_=twilio_number,
            url=f"{ai_agent_url}?rep={rep}"
        )

        print(f"✅ Llamada iniciada. SID: {call.sid}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now, rep, phone, call.sid])

        llamadas_realizadas += 1

    except Exception as e:
        print(f"❌ Error al llamar a {phone}:\n{e}")

    time.sleep(10)

def enviar_reporte_email():
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    subject = "📊 Reporte diario de llamadas del AI Agent"
    body = "Adjunto encontrarás el archivo con el historial de llamadas realizadas hoy."

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_receiver
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    filename = "llamadas_log.csv"
    if not os.path.exists(filename):
        print("⚠️ No hay archivo de log de llamadas todavía.")
        return

    with open(filename, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        print("✅ Reporte enviado por correo exitosamente.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

# Enviar reporte al terminar
enviar_reporte_email()
