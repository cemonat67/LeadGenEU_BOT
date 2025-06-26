from flask import Flask, request, jsonify, send_file
from lead_generator import LeadGenerator
import tempfile
import os
import pandas as pd

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__)
generator = LeadGenerator()

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    country = data.get("country", "Germany")
    max_leads = int(data.get("max_leads", 5))
    results = generator.generate_leads_for_country(country, max_per_country=max_leads)
    return jsonify({"results": results, "count": len(results)})

@app.route("/api/export", methods=["POST"])
def api_export():
    data = request.get_json()
    leads = data.get("leads", [])
    if not leads:
        return jsonify({"error": "No leads"}), 400
    df = pd.DataFrame(leads)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False, encoding="utf-8")
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name="leads_export.csv")

@app.route("/api/email_export", methods=["POST"])
def api_email_export():
    data = request.get_json()
    leads = data.get("leads", [])
    to_email = data.get("to_email")
    if not leads or not to_email:
        return jsonify({"error": "Eksik veri"}), 400

    df = pd.DataFrame(leads)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False, encoding="utf-8")
    tmp.close()

    from_email = "cemonat67@gmail.com"       # <-- BURAYA KENDİ GMAİL ADRESİNİ YAZ
    app_password = "ewvs nqze rldf aijt"          # <-- BURAYA 16 HANELİ APP PASSWORD'U YAZ

    subject = "Lead List CSV Export"
    body = "Lead listesi ekte. Cem Onat LeadGenEU_BOT"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(tmp.name, "rb") as file:
        part = MIMEApplication(file.read(), Name="leads_export.csv")
        part['Content-Disposition'] = 'attachment; filename=\"leads_export.csv\"'
        msg.attach(part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        os.remove(tmp.name)
        return jsonify({"success": True, "message": f"E-posta {to_email} adresine gönderildi!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
