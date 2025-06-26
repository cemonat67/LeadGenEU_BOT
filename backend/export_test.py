import requests

leads = [
    {
        'company_name': 'Wholesale Fashion Trends | Wholesale Clothing for Boutiques ...',
        'country': 'France',
        'description': 'Wholesale Fashion Trends is Your Premium Clothing & Accessories Supplier. Trendy Tops, Bottoms, Jewelry, & More. Competitively Priced & Shipped From the US.',
        'emails': 'info@wholesalefashiontrends.commonday, info@wholesalefashiontrends.com',
        'found_date': '2025-06-26 15:32:33',
        'source': 'Google Search',
        'website': 'https://www.wholesalefashiontrends.com/'
    },
    {
        'company_name': 'Efashion Paris',
        'country': 'France',
        'description': 'For professionals? Efashion Paris, your B2B online marketplace specialized in ready-to-wear and fashion, with over 100,000 products and 600 wholesalers. Happy\xa0...',
        'emails': 'service@efashion-paris.com',
        'found_date': '2025-06-26 15:32:54',
        'source': 'Google Search',
        'website': 'https://www.efashion-paris.com/en/'
    }
]

resp = requests.post("http://127.0.0.1:8080/api/export", json={"leads": leads})

with open("leads_test.csv", "wb") as f:
    f.write(resp.content)

print("CSV olarak kaydedildi!")
