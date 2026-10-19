"""
Selenium ile şüpheli URL'i headless (görünmez) tarayıcıda ziyaret edip
phishing analizi için önemli olan sinyalleri toplar.

ÖNEMLİ GÜVENLİK NOTU:
Bu fonksiyon gerçekten zararlı olabilecek sitelere gidiyor. Üretimde bunu
izole bir sanal makine/konteyner içinde çalıştırmanız, gerçek kimlik
bilgilerinizin makinede olmamasını sağlamanız önerilir.

Selenium 4.6+ sürümü "Selenium Manager" ile chromedriver'ı otomatik indirir,
bu yüzden ayrıca driver kurmanıza gerek yok (Chrome tarayıcısının kurulu
olması yeterli).
"""
import os
import uuid
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import SCREENSHOT_DIR

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def sayfa_incele(url: str) -> dict:
    """
    Sayfayı ziyaret eder, ekran görüntüsü alır ve şu sinyalleri toplar:
    - Sayfa başlığı
    - Şifre alanı var mı (login/kimlik avı sayfalarının tipik özelliği)
    - Formlar hangi adrese veri gönderiyor (asıl domain ile uyuşuyor mu)
    """
    secenekler = Options()
    secenekler.add_argument("--headless=new")
    secenekler.add_argument("--no-sandbox")
    secenekler.add_argument("--disable-dev-shm-usage")
    secenekler.add_argument("--window-size=1280,900")
    # Sayfanın otomatik dosya indirmesini / bildirim istemesini engelle
    secenekler.add_argument("--disable-notifications")

    sonuc = {
        "basarili": False,
        "baslik": None,
        "ekran_goruntusu_yolu": None,
        "sifre_alani_var_mi": False,
        "form_hedefleri": [],
        "dis_domain_form_sayisi": 0,
        "hata": None,
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=secenekler)
        driver.set_page_load_timeout(15)
        driver.get(url)

        sonuc["baslik"] = driver.title

        dosya_adi = f"{uuid.uuid4().hex}.png"
        yol = os.path.join(SCREENSHOT_DIR, dosya_adi)
        driver.save_screenshot(yol)
        sonuc["ekran_goruntusu_yolu"] = yol

        # Şifre input alanı var mı? (klasik phishing sayfası belirtisi)
        sifre_inputlari = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        sonuc["sifre_alani_var_mi"] = len(sifre_inputlari) > 0

        # Formlar farklı bir domaine mi veri gönderiyor?
        asil_domain = urlparse(url).netloc
        formlar = driver.find_elements(By.TAG_NAME, "form")
        dis_form_sayisi = 0
        hedefler = []
        for form in formlar:
            action = form.get_attribute("action") or ""
            hedefler.append(action)
            hedef_domain = urlparse(action).netloc
            if hedef_domain and hedef_domain != asil_domain:
                dis_form_sayisi += 1

        sonuc["form_hedefleri"] = hedefler
        sonuc["dis_domain_form_sayisi"] = dis_form_sayisi
        sonuc["basarili"] = True

    except Exception as e:
        sonuc["hata"] = str(e)
    finally:
        if driver:
            driver.quit()

    return sonuc
