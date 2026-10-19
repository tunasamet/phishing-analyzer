"""
Toplanan sinyalleri (VirusTotal + Selenium) Gemini'ye gonderip
risk degerlendirmesi ve kirmizi bayrak listesi alir.
"""
import json
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_risk_analizi(url: str, vt_sonuc: dict, sayfa_bilgisi: dict) -> dict:
    prompt = f"""
Sen deneyimli bir siber guvenlik analistisin. Asagidaki verilere bakarak bu
URL'in phishing (oltalama) olma ihtimalini degerlendir.

URL: {url}

VirusTotal Sonucu:
{json.dumps(vt_sonuc, ensure_ascii=False, indent=2)}

Sayfa Incelemesi (Selenium ile toplandi):
- Sayfa Basligi: {sayfa_bilgisi.get('baslik')}
- Sifre alani var mi: {sayfa_bilgisi.get('sifre_alani_var_mi')}
- Farkli domaine giden form sayisi: {sayfa_bilgisi.get('dis_domain_form_sayisi')}
- Form hedefleri: {sayfa_bilgisi.get('form_hedefleri')}
- Sayfa yuklenirken hata olustu mu: {sayfa_bilgisi.get('hata')}

Yalnizca asagidaki JSON formatinda, baska hicbir aciklama veya markdown eklemeden yanit ver:
{{
  "risk_skoru": 0,
  "karar": "GUVENLI",
  "kirmizi_bayraklar": [],
  "aciklama": "kisa aciklama"
}}

risk_skoru 0-100 arasi olmali (100 en tehlikeli).
karar sadece su uc degerden biri olmali: GUVENLI, SUPHELI, TEHLIKELI.
"""

    try:
        yanit = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )
        metin = yanit.text.strip()
        metin = metin.replace("```json", "").replace("```", "").strip()
        return json.loads(metin)
    except Exception as e:
        return {
            "risk_skoru": None,
            "karar": "BILINMIYOR",
            "kirmizi_bayraklar": [],
            "aciklama": f"Gemini analizi basarisiz oldu: {e}",
        }