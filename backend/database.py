"""
SQLAlchemy ile veritabanı bağlantısı ve tablo tanımı.
Her analiz sonucu 'analiz_kayitlari' tablosuna kaydedilir.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from config import DATABASE_URL

# SQLite tek thread kısıtlamasını kaldırmak için connect_args gerekiyor.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analiz_kayitlari"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    # VirusTotal sonuçları
    virustotal_skoru = Column(Float, nullable=True)   # 0-1 arası, zararlı/şüpheli oy oranı
    virustotal_detay = Column(Text, nullable=True)     # JSON string olarak saklanır

    # Gemini sonuçları
    gemini_risk_skoru = Column(Integer, nullable=True)  # 0-100 arası risk puanı
    gemini_yorum = Column(Text, nullable=True)
    kirmizi_bayraklar = Column(Text, nullable=True)     # JSON liste olarak saklanır

    # Nihai karar
    nihai_karar = Column(String, nullable=True)  # "GÜVENLİ" / "ŞÜPHELİ" / "TEHLİKELİ"
    ekran_goruntusu_yolu = Column(String, nullable=True)


def init_db():
    """Uygulama ilk açıldığında tabloları oluşturur."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency injection için veritabanı oturumu üretir."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
