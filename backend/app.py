from flask import Flask, request, jsonify, send_file
import pandas as pd
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import email.utils   # EKLENDİ!
import os

app = Flask(__name__)

# SMTP AYARLARI (GoDaddy/Hosting üzerinden)
FROM_EMAIL = "cem@onat.ltd"
PASSWORD = "Cm277010!"
SMTP_SERVER = "smtpout.secureserver.net"
SMTP_PORT = 465  # SSL

def send_leads_email(leads, to_email):
    # Geçici CSV dosyası oluştur
    df = pd.DataFrame(leads)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False, encoding="utf-8")
    tmp.close()

    # E-posta mesajı kur
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = "LeadGenEU_BOT: Lead Export"
    msg["Message-ID"] = email.utils.make_msgid()  # <-- Gmail hatasını önler!
    body = "Merhaba, ekte lead listeniz var. Cem Onat / LeadGenEU_BOT"
    msg.attach(MIMEText(body, "plain"))

    # CSV dosyasını ekle
    with open(tmp.name, "rb") as f:
        part = MIMEApplication(f.read(), Name="leads_export.csv")
    part["Content-Disposition"] = 'attachment; filename="leads_export.csv"'
    msg.attach(part)

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(FROM_EMAIL, PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        os.remove(tmp.name)
        return True
    except Exception as e:
        print("E-posta gönderilemedi:", e)
        os.remove(tmp.name)
        return False

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    country = data.get("country", "France")
    max_leads = data.get("max_leads", 2)
    results = [
        {
            "company_name": "Test Textile",
            "country": country,
            "description": "Test firması",
            "emails": "test@test.com",
            "found_date": "2025-06-26",
            "source": "Test",
            "website": "https://test.com"
        }
    ] * max_leads
    return jsonify({"count": len(results), "results": results})

@app.route("/api/email_export", methods=["POST"])
def api_email_export():
    data = request.get_json()
    leads = data.get("leads", [])
    to_email = data.get("to_email")
    if not leads or not to_email:
        return jsonify({"error": "Eksik veri"}), 400

    ok = send_leads_email(leads, to_email)
    if ok:
        return jsonify({"success": True, "message": f"E-posta {to_email} adresine gönderildi!"})
    else:
        return jsonify({"success": False, "message": "E-posta gönderilemedi!"}), 500

@app.route("/api/download_csv", methods=["POST"])
def api_download_csv():
    data = request.get_json()
    leads = data.get("leads", [])
    if not leads:
        return jsonify({"error": "Eksik veri"}), 400

    df = pd.DataFrame(leads)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False, encoding="utf-8")
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name="leads_export.csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
