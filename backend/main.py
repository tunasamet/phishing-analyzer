"""
FastAPI backend giriş noktası.

Çalıştırmak için:
    uvicorn main:app --reload

Otomatik oluşan API dokümantasyonu: http://127.0.0.1:8000/docs
"""
import json
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import init_db, get_db, AnalysisRecord
from schemas import AnalizIstegi, AnalizSonucu
from services.analyzer import url_analiz_et
from config import SCREENSHOT_DIR

app = FastAPI(title="AI Destekli Phishing Analizörü")

init_db()

# Ekran görüntülerine tarayıcı/istemci üzerinden erişilebilmesi için statik dosya sunucusu
app.mount(f"/{SCREENSHOT_DIR}", StaticFiles(directory=SCREENSHOT_DIR), name=SCREENSHOT_DIR)


def _kayit_to_sonuc(kayit: AnalysisRecord) -> AnalizSonucu:
    """SQLAlchemy nesnesini API'nin döndüreceği Pydantic modeline çevirir."""
    return AnalizSonucu(
        id=kayit.id,
        url=kayit.url,
        virustotal_skoru=kayit.virustotal_skoru,
        gemini_risk_skoru=kayit.gemini_risk_skoru,
        gemini_yorum=kayit.gemini_yorum,
        kirmizi_bayraklar=json.loads(kayit.kirmizi_bayraklar or "[]"),
        nihai_karar=kayit.nihai_karar,
        ekran_goruntusu_yolu=kayit.ekran_goruntusu_yolu,
        olusturulma_tarihi=kayit.olusturulma_tarihi,
    )


@app.post("/analyze", response_model=AnalizSonucu)
def analiz_yap(istek: AnalizIstegi, db: Session = Depends(get_db)):
    """Yeni bir URL analizi başlatır. Bu istek birkaç saniye sürebilir."""
    if not istek.url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL http:// veya https:// ile başlamalı")

    kayit = url_analiz_et(istek.url, db)
    return _kayit_to_sonuc(kayit)


@app.get("/history", response_model=List[AnalizSonucu])
def gecmis(db: Session = Depends(get_db), limit: int = 50):
    """En son yapılan analizleri listeler (varsayılan: en yeni 50 kayıt)."""
    kayitlar = db.query(AnalysisRecord).order_by(AnalysisRecord.id.desc()).limit(limit).all()
    return [_kayit_to_sonuc(k) for k in kayitlar]


@app.get("/analysis/{kayit_id}", response_model=AnalizSonucu)
def tek_kayit(kayit_id: int, db: Session = Depends(get_db)):
    """Belirli bir analiz kaydını id'sine göre döndürür."""
    kayit = db.query(AnalysisRecord).filter(AnalysisRecord.id == kayit_id).first()
    if not kayit:
        raise HTTPException(404, "Kayıt bulunamadı")
    return _kayit_to_sonuc(kayit)


@app.get("/")
def anasayfa():
    return {"mesaj": "AI Destekli Phishing Analizörü API çalışıyor. Detaylar için /docs adresine gidin."}
