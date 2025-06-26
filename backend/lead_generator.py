#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EU Fashion Lead Generator
Hazır giyim şirketleri için lead toplama sistemi
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime
import os
import json
from urllib.parse import urljoin, urlparse
import random
from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID, REQUESTS_PER_MINUTE, DAILY_SEARCH_LIMIT

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LeadGenerator:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.search_engine_id = SEARCH_ENGINE_ID
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.leads = []
        self.request_count = 0
        self.max_requests = DAILY_SEARCH_LIMIT
        
        # EU Ülkeleri
        self.eu_countries = [
            'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
            'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece',
            'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
            'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia',
            'Slovenia', 'Spain', 'Sweden'
        ]
        
        # Hazır giyim arama terimleri
        self.search_terms = [
            'fashion wholesale clothing suppliers',
            'garment manufacturers',
            'textile clothing brands',
            'fashion apparel companies',
            'clothing retail brands',
            'fashion wholesale distributors',
            'textile manufacturing companies',
            'fashion brands contact'
        ]
        
        # Email regex patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]

    def create_directories(self):
        """Gerekli klasörleri oluştur"""
        directories = ['data', 'data/daily_reports', 'logs']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        logger.info("Dizinler oluşturuldu")

    def google_search(self, query, country=None):
        """Google Custom Search API ile arama yap"""
        if self.request_count >= self.max_requests:
            logger.warning("Günlük API limiti aşıldı")
            return []
        
        # Ülke spesifik arama
        if country:
            query = f"{query} site:{country.lower()}"
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 10,
            'gl': 'eu' if not country else country[:2].lower(),
            'lr': 'lang_en',
            'safe': 'medium'
        }
        
        try:
            logger.info(f"Arama yapılıyor: {query}")
            response = self.session.get(url, params=params, timeout=30)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                logger.error(f"API hatası: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Arama hatası: {str(e)}")
            return []
        
        finally:
            # Rate limiting
            time.sleep(60 / REQUESTS_PER_MINUTE)

    def extract_emails_from_text(self, text):
        """Metinden email adreslerini çıkar"""
        emails = set()
        for pattern in self.email_patterns:
            found_emails = re.findall(pattern, text, re.IGNORECASE)
            emails.update(found_emails)
        
        # Geçersiz uzantıları filtrele
        valid_emails = []
        invalid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.doc', '.zip']
        
        for email in emails:
            email = email.lower().strip()
            if not any(email.endswith(ext) for ext in invalid_extensions):
                if len(email) > 5 and '@' in email and '.' in email.split('@')[1]:
                    valid_emails.append(email)
        
        return list(set(valid_emails))

    def scrape_website(self, url):
        """Web sitesini tara ve email adreslerini bul"""
        try:
            logger.info(f"Site taranıyor: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Metni çıkar
            text_content = soup.get_text()
            
            # Email adreslerini bul
            emails = self.extract_emails_from_text(text_content)
            
            # İletişim sayfalarını ara
            contact_links = []
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                link_text = link.get_text().lower()
                
                if any(word in href or word in link_text for word in ['contact', 'about', 'info']):
                    full_url = urljoin(url, link['href'])
                    contact_links.append(full_url)
            
            # İletişim sayfalarını tara
            for contact_url in contact_links[:2]:  # Sadece 2 tanesini tara
                try:
                    contact_response = self.session.get(contact_url, timeout=10)
                    contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                    contact_emails = self.extract_emails_from_text(contact_soup.get_text())
                    emails.extend(contact_emails)
                except:
                    continue
            
            # Site meta bilgilerini al
            title = soup.find('title')
            title = title.get_text().strip() if title else ''
            
            description = soup.find('meta', attrs={'name': 'description'})
            description = description.get('content', '').strip() if description else ''
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'emails': list(set(emails)),
                'contact_links': contact_links
            }
            
        except Exception as e:
            logger.error(f"Site tarama hatası {url}: {str(e)}")
            return None

    def process_search_results(self, search_results, country):
        """Arama sonuçlarını işle"""
        country_leads = []
        
        for item in search_results:
            url = item.get('link', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            
            # Web sitesini tara
            website_data = self.scrape_website(url)
            
            if website_data and website_data['emails']:
                lead = {
                    'country': country,
                    'company_name': title,
                    'website': url,
                    'description': website_data['description'] or snippet,
                    'emails': ', '.join(website_data['emails']),
                    'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'Google Search'
                }
                
                country_leads.append(lead)
                logger.info(f"Lead bulundu: {title} - {len(website_data['emails'])} email")
            
            # Rate limiting
            time.sleep(2)
        
        return country_leads

    def generate_leads_for_country(self, country, max_per_country=15):
        """Belirli bir ülke için lead'ler oluştur"""
        logger.info(f"🇪🇺 {country} için lead arama başladı")
        country_leads = []
        
        # Her arama terimi için
        for search_term in self.search_terms[:4]:  # İlk 4 terimi kullan
            if len(country_leads) >= max_per_country:
                break
                
            if self.request_count >= self.max_requests:
                logger.warning("API limiti aşıldı, durduruluyor")
                break
            
            # Ülke spesifik arama yap
            query = f"{search_term} {country}"
            search_results = self.google_search(query)
            
            if search_results:
                new_leads = self.process_search_results(search_results, country)
                country_leads.extend(new_leads)
                
                logger.info(f"{country} - {search_term}: {len(new_leads)} yeni lead")
            
            # API rate limiting
            time.sleep(3)
        
        logger.info(f"✅ {country} tamamlandı: {len(country_leads)} lead bulundu")
        return country_leads

    def save_leads(self, leads):
        """Lead'leri CSV dosyasına kaydet"""
        if not leads:
            logger.warning("Kaydedilecek lead bulunamadı")
            return
        
        df = pd.DataFrame(leads)
        
        # Dosya adı
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"data/leads_{today}.csv"
        
        # CSV'ye kaydet
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"📊 {len(leads)} lead kaydedildi: {filename}")
        
        # Özet rapor oluştur
        self.create_summary_report(leads, today)

    def create_summary_report(self, leads, date):
        """Özet rapor oluştur"""
        df = pd.DataFrame(leads)
        
        # Ülke bazında istatistikler
        country_stats = df.groupby('country').size().to_dict()
        
        # Toplam email sayısı
        total_emails = sum(len(lead['emails'].split(', ')) for lead in leads if lead['emails'])
        
        report = {
            'date': date,
            'total_leads': len(leads),
            'total_emails': total_emails,
            'countries_covered': len(country_stats),
            'country_breakdown': country_stats,
            'api_requests_used': self.request_count
        }
        
        # JSON raporu kaydet
        report_filename = f"data/daily_reports/report_{date}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Konsol raporu
        print("\n" + "="*50)
        print(f"📈 GÜNLÜK RAPOR - {date}")
        print("="*50)
        print(f"Toplam Lead: {len(leads)}")
        print(f"Toplam Email: {total_emails}")
        print(f"Kapsanan Ülke: {len(country_stats)}")
        print(f"Kullanılan API: {self.request_count}/{self.max_requests}")
        print("\nÜlke Bazında:")
        for country, count in sorted(country_stats.items()):
            print(f"  {country}: {count} lead")
        print("="*50)

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        logger.info("🚀 EU Fashion Lead Generator başlatıldı")
        
        # Dizinleri oluştur
        self.create_directories()
        
        # Tüm lead'ler
        all_leads = []
        
        # Her ülke için lead toplama
        for country in self.eu_countries:
            if self.request_count >= self.max_requests:
                logger.warning("Günlük API limiti doldu")
                break
            
            try:
                country_leads = self.generate_leads_for_country(country)
                all_leads.extend(country_leads)
                
                # Her ülkeden sonra biraz bekle
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"{country} için hata: {str(e)}")
                continue
        
        # Sonuçları kaydet
        if all_leads:
            self.save_leads(all_leads)
        else:
            logger.warning("Hiç lead bulunamadı!")
        
        logger.info("✅ Lead generation tamamlandı")

if __name__ == "__main__":
    generator = LeadGenerator()
    generator.run()