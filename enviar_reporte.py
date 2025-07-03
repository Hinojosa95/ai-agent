import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv()

email_user = os.getenv("EMAIL_USER")
email_password = os.getenv("EMAIL_PASSWORD")
email_receiver = os.getenv("EMAIL_RECEIVER")

subject = "📊 Reporte Diario de Llamadas del AI Agent"

body = "Adjunto encontrarás el archivo con el reporte diario de las llamadas realizadas por el AI Agent."

msg = MIMEMultipart()
msg["From"] = email_user
msg["To"] = email_receiver
msg["Subject"] = subject

msg.attach(MIMEText(body, "plain"))

filename = "llamadas_log.csv"
if os.path.exists(filename):
    with open(filename, "rb") as file:
        part = MIMEApplication(file.read(), Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)
else:
    print("⚠️ No hay archivo de log de llamadas todavía.")

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_user, email_password)
    server.send_message(msg)
    server.quit()
    print("✅ Reporte enviado correctamente.")
except Exception as e:
    print(f"❌ Error enviando el correo: {e}")
