# AI Destekli Phishing Analizörü

Bir web adresinin (URL) phishing (oltalama) olup olmadığını üç kaynağı birleştirerek değerlendiren masaüstü uygulaması.

1. **VirusTotal**: 70'ten fazla güvenlik motorunun ve zararlı adres listesinin itibar taraması
2. **Selenium**: Siteyi görünmez bir Chrome ile açıp sayfa başlığını, ekran görüntüsünü, şifre alanı olup olmadığını ve formların verileri nereye gönderdiğini toplar
3. **Gemini API**: Toplanan tüm sinyalleri yorumlayıp risk puanı, kırmızı bayraklar ve sade bir açıklama üretir

Sonuçlar SQLite veri tabanında saklanır, PyQt6 arayüzünden görüntülenir. Uygulama tek dosyaya çift tıklanarak açılır.

## Nasıl Çalışır

1. Kullanıcı bir URL girer ve "Analiz Et" düğmesine basar
2. VirusTotal adresi sorgular (daha önce taranmamışsa yeni tarama başlatır) ve zararlı/şüpheli diyen motorların oranını hesaplar
3. Selenium sayfayı açıp başlık, ekran görüntüsü, şifre alanı ve form hedeflerini toplar
4. Gemini bu verileri yorumlayıp 0-100 arası risk puanı, kırmızı bayrak listesi ve açıklama üretir
5. İki sonuç birleştirilerek nihai karar verilir:

| Karar | Koşul |
|---|---|
| TEHLİKELİ | VirusTotal oranı %15'in üzerinde **veya** Gemini puanı 70 ve üzeri |
| ŞÜPHELİ | VirusTotal oranı %3'ün üzerinde **veya** Gemini puanı 35 ve üzeri |
| GÜVENLİ | Diğer durumlar |

Eşik değerleri `backend/services/analyzer.py` içinde değiştirilebilir.

## Mimari

```
launcher.py  ──▶  backend'i arka planda başlatır, sonra arayüzü açar
                  
desktop/app.py  (PyQt6 arayüz)
      │  HTTP isteği (requests)
      ▼
backend/main.py (FastAPI)
      │
      ├── services/virustotal_service.py   VirusTotal sorgusu
      ├── services/selenium_service.py     sayfa incelemesi
      ├── services/gemini_service.py       yapay zekâ yorumu
      └── services/analyzer.py             hepsini birleştirir, veri tabanına kaydeder
```

## Proje Yapısı

```
phishing_analyzer/
├── backend/
│   ├── main.py              FastAPI uygulaması ve uç noktalar
│   ├── config.py            .env ayarlarını okur
│   ├── database.py          SQLAlchemy modeli ve bağlantı
│   ├── schemas.py           API veri şemaları
│   └── services/            VirusTotal, Selenium, Gemini, birleştirici
├── desktop/
│   └── app.py               PyQt6 arayüzü
├── launcher.py              Tek tıkla başlatıcı
├── baslat.bat               Başlatıcıyı çalıştırır (konsol açık)
├── baslat_sessiz.bat        Başlatıcıyı çalıştırır (konsol gizli)
├── requirements.txt
└── .env.example
```

## Gereksinimler

- Windows
- Python 3.11 veya üzeri
- Google Chrome (Selenium 4.6+ chromedriver'ı otomatik indirir, ayrıca kurulum gerekmez)
- VirusTotal ve Gemini API anahtarları (ikisi de ücretsiz)

## Kurulum

Proje klasöründe, **cmd** üzerinden:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

`.env` dosyasına API anahtarlarını yaz. Tırnak işareti ve boşluk kullanma:

```
VIRUSTOTAL_API_KEY=anahtarin
GEMINI_API_KEY=anahtarin
```

- VirusTotal anahtarı: https://www.virustotal.com/gui/my-apikey
- Gemini anahtarı: https://aistudio.google.com/apikey

## Çalıştırma

**`baslat.bat`** dosyasına çift tıkla. Backend arka planda açılır, hazır olunca arayüz gelir. Arayüzü kapatınca backend de kapanır.

- `baslat.bat`: Küçük bir konsol penceresi açık kalır, sorun olursa orada görünür
- `baslat_sessiz.bat`: Konsol görünmez, sadece uygulama penceresi açılır. Masaüstü kısayolu için bu uygundur

**Elle çalıştırma (geliştirme için):**

```
cd backend
uvicorn main:app
```

Ayrı bir terminalde, proje klasöründe:

```
venv\Scripts\activate
python desktop/app.py
```

API dokümantasyonu: http://127.0.0.1:8000/docs

## Kullanım

1. Arayüze bir URL yapıştır (örn. `https://ornek-site.com`)
2. "Analiz Et" düğmesine bas ve 20-40 saniye bekle
3. Karar (yeşil, turuncu, kırmızı), VirusTotal oranı, Gemini puanı, açıklama, kırmızı bayraklar ve sayfanın ekran görüntüsü gösterilir
4. Alt kısımdaki geçmiş listesinden önceki analizlere tekrar bakabilirsin

## Test İçin Güvenli Adresler

Gerçek zararlı sitelere gitmek yerine, güvenlik araçlarını denemek için hazırlanmış resmi test adreslerini kullan:

| Adres | Beklenen sonuç |
|---|---|
| https://testsafebrowsing.appspot.com/ | Düşük risk / Şüpheli |
| http://testsafebrowsing.appspot.com/apiv4/ANY_PLATFORM/SOCIAL_ENGINEERING/URL/ | Tehlikeli (oltalama kategorisi) |
| https://secure.eicar.org/eicar.com | Şüpheli (antivirüs test dosyası) |
| https://www.google.com | Güvenli |

## Sorun Giderme

- **Uygulama açılmıyor:** Proje klasöründeki `backend.log` dosyasına bak, backend hataları oraya yazılır
- **"DLL load failed" hatası:** Uygulamayı Spyder içinden değil, `baslat.bat` ile çalıştır. Spyder kendi PyQt5'ini kullandığı için PyQt6 ile çakışır
- **Gemini "404 model" ya da "429 quota" hatası:** Google model adlarını sık değiştiriyor. Kod `gemini-flash-latest` takma adını kullanır. Hâlâ hata alırsan anahtarı yeni bir projeyle yeniden oluştur ve `gemini_service.py` içindeki model adını güncel olanla değiştir
- **Türkçe karakter / "unicode error":** Dosyaları UTF-8 olarak kaydet (Not Defteri'nde "Farklı Kaydet" ekranında Kodlama: UTF-8)
- **Analiz çok uzun sürüyor:** VirusTotal ücretsiz kotası dakikada 4 istektir. Art arda çok analiz yapma

## Güvenlik Notu

Bu araç, gerçekten zararlı olabilecek sitelere Selenium ile gidiyor. Gerçek kullanımda:

- Uygulamayı izole bir sanal makine ya da konteyner içinde çalıştır
- O ortamda gerçek kimlik bilgilerin bulunmasın
- Mümkünse kurum ağından ayrı bir ağ segmentinde çalıştır
- `.env` dosyasını asla paylaşma ve GitHub'a yükleme (`.gitignore` içinde olmalı)

Dosya indirmeyi ve açılır pencereleri engelleyen ek Chrome ayarları, riski azaltmak için geliştirilebilecek iyileştirmeler arasındadır.

## Sınırlılıklar

- Sadece web adreslerini analiz eder, e-posta ve ek dosyaları kapsamaz
- Sayfa incelemesi temel göstergelere bakar (başlık, şifre alanı, form hedefleri)
- Gemini yorumu bir karar destek aracıdır, güvenlik uzmanının değerlendirmesinin yerini almaz
- Ücretsiz API sınırları yoğun kullanımda kısıt oluşturabilir

## Geliştirme Fikirleri

- Alan adı yaşı (WHOIS) ve marka taklidi (typosquatting) kontrolü
- Dosya indirme ve açılır pencere engelleme gibi Chrome güvenlik sertleştirmeleri
- Docker ile izole çalıştırma
- Toplu URL analizi (CSV yükleyip hepsini sırayla tarama)
- E-posta (.eml) dosyasındaki bağlantıların taranması
- PostgreSQL'e geçip çok kullanıcılı kullanım
