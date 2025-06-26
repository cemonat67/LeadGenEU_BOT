import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pandas as pd
import tempfile
import os

def send_leads_email(leads, to_email):
    from_email = "cem@onat.ltd"
    password = "Cm277010!"
    smtp_server = "smtpout.secureserver.net"
    smtp_port = 465  # SSL

    # CSV dosyasını oluştur
    df = pd.DataFrame(leads)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False, encoding="utf-8")
    tmp.close()

    # E-posta oluştur
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "LeadGenEU_BOT: Lead Export"
    body = "Merhaba, ekte lead listeniz var. Cem Onat / LeadGenEU_BOT"
    msg.attach(MIMEText(body, "plain"))

    # CSV dosyasını ekle
    with open(tmp.name, "rb") as f:
        part = MIMEApplication(f.read(), Name="leads_export.csv")
    part["Content-Disposition"] = 'attachment; filename="leads_export.csv"'
    msg.attach(part)

    # SMTP bağlantısı ve gönderim
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        os.remove(tmp.name)
        print(f"Başarılı! E-posta {to_email} adresine gönderildi.")
        return True
    except Exception as e:
        print(f"E-posta gönderilemedi: {e}")
        return False

# TEST İÇİN:
if __name__ == "__main__":
    leads = [
        {
            "company_name": "Test Textile",
            "country": "France",
            "description": "Test firması",
            "emails": "test@test.com",
            "found_date": "2025-06-26",
            "source": "Test",
            "website": "https://test.com"
        }
    ]
    send_leads_email(leads, "kendiadresin@gmail.com")  # Buraya kendi test adresini koy!
