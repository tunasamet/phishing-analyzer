"""
VirusTotal API v3 ile URL itibar taraması.

Mantık:
1) Önce bu URL daha önce taranmış mı diye bakıyoruz (hızlı, ücretsiz kotayı korur).
2) Kayıt yoksa yeni bir tarama başlatıp sonucu kısa süre bekliyoruz (polling).
3) 70+ antivirüs motorunun "zararlı" / "şüpheli" oy oranını hesaplayıp döndürüyoruz.

Ücretsiz VirusTotal API anahtarı: https://www.virustotal.com/gui/join-us
"""
import base64
import time
import requests

from config import VIRUSTOTAL_API_KEY

VT_BASE_URL = "https://www.virustotal.com/api/v3"


def _url_id(url: str) -> str:
    """VirusTotal, URL'leri base64 (padding'siz) bir id ile tanımlar."""
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")


def virustotal_analiz_et(url: str) -> dict:
    """
    Verilen URL'i VirusTotal'da analiz eder.
    Dönüş: {"zararli_oran": 0-1 arası float ya da None, "detay": dict}
    """
    if not VIRUSTOTAL_API_KEY:
        return {"zararli_oran": None, "detay": {"hata": "VIRUSTOTAL_API_KEY tanımlı değil (.env dosyasını kontrol edin)"}}

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    url_id = _url_id(url)

    try:
        rapor = requests.get(f"{VT_BASE_URL}/urls/{url_id}", headers=headers, timeout=15)

        if rapor.status_code != 200:
            # Bu URL daha önce hiç taranmamış -> yeni tarama başlat
            gonder = requests.post(
                f"{VT_BASE_URL}/urls", headers=headers, data={"url": url}, timeout=15
            )
            if gonder.status_code not in (200, 201):
                return {"zararli_oran": None, "detay": {"hata": f"VT gönderim hatası: {gonder.status_code}"}}

            analiz_id = gonder.json()["data"]["id"]

            # Tarama tamamlanana kadar kısa aralıklarla kontrol et (en fazla ~18 saniye)
            for _ in range(6):
                time.sleep(3)
                durum = requests.get(f"{VT_BASE_URL}/analyses/{analiz_id}", headers=headers, timeout=15)
                if durum.status_code == 200 and durum.json()["data"]["attributes"]["status"] == "completed":
                    break

            rapor = requests.get(f"{VT_BASE_URL}/urls/{url_id}", headers=headers, timeout=15)
            if rapor.status_code != 200:
                return {"zararli_oran": None, "detay": {"hata": "Tarama zaman aşımına uğradı, tekrar deneyin"}}

        veri = rapor.json()["data"]["attributes"]
        istatistik = veri.get("last_analysis_stats", {})

        zararli = istatistik.get("malicious", 0)
        supheli = istatistik.get("suspicious", 0)
        toplam = sum(istatistik.values()) or 1

        zararli_oran = round((zararli + supheli) / toplam, 3)

        return {
            "zararli_oran": zararli_oran,
            "detay": {
                "istatistikler": istatistik,
                "kategori": veri.get("categories", {}),
                "itibar": veri.get("reputation", 0),
            },
        }

    except requests.exceptions.RequestException as e:
        return {"zararli_oran": None, "detay": {"hata": f"Bağlantı hatası: {e}"}}
