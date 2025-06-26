from flask import Flask, request, jsonify, send_file
from lead_generator import LeadGenerator
import tempfile
import os
import pandas as pd

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

if __name__ == "__main__":
    app.run(debug=True, port=8080)
