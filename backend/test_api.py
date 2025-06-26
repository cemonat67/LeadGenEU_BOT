import requests

payload = {"country": "France", "max_leads": 2}
r = requests.post("http://127.0.0.1:8080/api/search", json=payload)
print(r.json())
