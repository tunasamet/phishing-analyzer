"""
Analiz akışının tamamını yöneten katman:
VirusTotal -> Selenium -> Gemini -> nihai karar -> veritabanına kayıt

main.py bu tek fonksiyonu çağırarak tüm işi tetikler.
"""
import json

from database import AnalysisRecord
from services.virustotal_service import virustotal_analiz_et
from services.selenium_service import sayfa_incele
from services.gemini_service import gemini_risk_analizi


def url_analiz_et(url: str, db) -> AnalysisRecord:
    print("1) VirusTotal analizi başlıyor...")
    vt_sonuc = virustotal_analiz_et(url)
    print("1) VirusTotal analizi bitti:", vt_sonuc)

    print("2) Selenium sayfa incelemesi başlıyor...")
    sayfa_bilgisi = sayfa_incele(url)
    print("2) Selenium bitti:", sayfa_bilgisi)

    print("3) Gemini analizi başlıyor...")
    gemini_sonuc = gemini_risk_analizi(url, vt_sonuc, sayfa_bilgisi)
    print("3) Gemini bitti:", gemini_sonuc)

    # Nihai kararı hem VirusTotal hem Gemini skorunu birlikte değerlendirerek veriyoruz.
    # Bu eşikleri kendi ihtiyacına göre kolayca ayarlayabilirsin.
    vt_oran = vt_sonuc.get("zararli_oran") or 0
    gemini_skoru = gemini_sonuc.get("risk_skoru") or 0

    if vt_oran > 0.15 or gemini_skoru >= 70:
        nihai_karar = "TEHLİKELİ"
    elif vt_oran > 0.03 or gemini_skoru >= 35:
        nihai_karar = "ŞÜPHELİ"
    else:
        nihai_karar = "GÜVENLİ"

    kayit = AnalysisRecord(
        url=url,
        virustotal_skoru=vt_sonuc.get("zararli_oran"),
        virustotal_detay=json.dumps(vt_sonuc.get("detay"), ensure_ascii=False),
        gemini_risk_skoru=gemini_sonuc.get("risk_skoru"),
        gemini_yorum=gemini_sonuc.get("aciklama"),
        kirmizi_bayraklar=json.dumps(gemini_sonuc.get("kirmizi_bayraklar", []), ensure_ascii=False),
        nihai_karar=nihai_karar,
        ekran_goruntusu_yolu=sayfa_bilgisi.get("ekran_goruntusu_yolu"),
    )

    db.add(kayit)
    db.commit()
    db.refresh(kayit)
    return kayit
