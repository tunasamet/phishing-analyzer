"""
FastAPI'nin request/response doğrulaması için kullandığı Pydantic modelleri.
Veritabanı modelinden (database.py) farklı olarak, bunlar dış dünyaya açılan sözleşmedir.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AnalizIstegi(BaseModel):
    url: str


class AnalizSonucu(BaseModel):
    id: int
    url: str
    virustotal_skoru: Optional[float] = None
    gemini_risk_skoru: Optional[int] = None
    gemini_yorum: Optional[str] = None
    kirmizi_bayraklar: List[str] = []
    nihai_karar: str
    ekran_goruntusu_yolu: Optional[str] = None
    olusturulma_tarihi: datetime

    class Config:
        from_attributes = True  # SQLAlchemy nesnesinden otomatik dönüşüm için
