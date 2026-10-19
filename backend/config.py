"""
Uygulama genelinde kullanılan ayarlar.
API anahtarlarını .env dosyasından okur (repoya .env dosyasını asla eklemeyin!).
"""
import os
from dotenv import load_dotenv

load_dotenv()

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Varsayılan olarak SQLite kullanıyoruz, istersen PostgreSQL'e geçebilirsin:
# DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/phishing_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./phishing_analyzer.db")

SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "ekran_goruntuleri")
