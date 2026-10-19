"""
PyQt6 masaüstü arayüzü.

Backend (FastAPI) ayrı bir process olarak çalışmalı:
    uvicorn main:app --reload   (backend/ klasöründe)

Sonra bu dosyayı çalıştır:
    python desktop/app.py

Ağ isteği arayüzü dondurmasın diye ayrı bir QThread (AnalizIsciSi) içinde yapılıyor.
"""
import sys
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QTextEdit, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

BACKEND_URL = "http://127.0.0.1:8000"


class AnalizIsciSi(QThread):
    """Backend'e istek atarken arayüzün donmaması için ayrı thread'de çalışır."""
    tamamlandi = pyqtSignal(dict)
    hata_olustu = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            yanit = requests.post(f"{BACKEND_URL}/analyze", json={"url": self.url}, timeout=120)
            yanit.raise_for_status()
            self.tamamlandi.emit(yanit.json())
        except Exception as e:
            self.hata_olustu.emit(str(e))


class AnaPencere(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Destekli Phishing Analizörü")
        self.resize(950, 650)
        self._arayuzu_kur()

    def _arayuzu_kur(self):
        ana_layout = QVBoxLayout()

        # --- Üst kısım: URL girişi ---
        ust_satir = QHBoxLayout()
        self.url_girisi = QLineEdit()
        self.url_girisi.setPlaceholderText("Analiz edilecek URL'i girin (https://...)")
        self.url_girisi.returnPressed.connect(self._analiz_baslat)
        self.analiz_butonu = QPushButton("Analiz Et")
        self.analiz_butonu.clicked.connect(self._analiz_baslat)
        ust_satir.addWidget(self.url_girisi)
        ust_satir.addWidget(self.analiz_butonu)
        ana_layout.addLayout(ust_satir)

        self.durum_etiketi = QLabel("")
        ana_layout.addWidget(self.durum_etiketi)

        # --- Orta kısım: sonuç metni + ekran görüntüsü yan yana ---
        orta_satir = QHBoxLayout()

        self.sonuc_alani = QTextEdit()
        self.sonuc_alani.setReadOnly(True)
        orta_satir.addWidget(self.sonuc_alani, 2)

        self.goruntu_etiketi = QLabel("Ekran görüntüsü burada gösterilecek")
        self.goruntu_etiketi.setFixedSize(360, 270)
        self.goruntu_etiketi.setStyleSheet("border: 1px solid gray;")
        self.goruntu_etiketi.setScaledContents(True)
        orta_satir.addWidget(self.goruntu_etiketi, 1)

        ana_layout.addLayout(orta_satir)

        # --- Alt kısım: geçmiş analizler ---
        ana_layout.addWidget(QLabel("Geçmiş Analizler (tıklayınca detay görüntülenir):"))
        self.gecmis_listesi = QListWidget()
        self.gecmis_listesi.itemClicked.connect(self._gecmisten_sec)
        ana_layout.addWidget(self.gecmis_listesi)

        self.setLayout(ana_layout)
        self._gecmisi_yukle()

    def _analiz_baslat(self):
        url = self.url_girisi.text().strip()
        if not url:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir URL girin.")
            return

        self.analiz_butonu.setEnabled(False)
        self.durum_etiketi.setText("Analiz ediliyor, lütfen bekleyin... (VirusTotal + Selenium + Gemini)")
        self.sonuc_alani.clear()

        self.isci = AnalizIsciSi(url)
        self.isci.tamamlandi.connect(self._sonucu_goster)
        self.isci.hata_olustu.connect(self._hata_goster)
        self.isci.start()

    def _sonucu_goster(self, veri: dict):
        self.analiz_butonu.setEnabled(True)
        self.durum_etiketi.setText("Analiz tamamlandı.")

        renkler = {"GÜVENLİ": "green", "ŞÜPHELİ": "orange", "TEHLİKELİ": "red"}
        renk = renkler.get(veri["nihai_karar"], "black")

        bayraklar_html = "<br>".join(f"- {b}" for b in veri.get("kirmizi_bayraklar", [])) or "Bulunamadı"

        metin = f"""
        <h2 style='color:{renk}'>Karar: {veri['nihai_karar']}</h2>
        <b>URL:</b> {veri['url']}<br>
        <b>VirusTotal Zararlı Oranı:</b> {veri['virustotal_skoru']}<br>
        <b>Gemini Risk Skoru:</b> {veri['gemini_risk_skoru']}/100<br><br>
        <b>Açıklama:</b><br>{veri['gemini_yorum']}<br><br>
        <b>Kırmızı Bayraklar:</b><br>{bayraklar_html}
        """
        self.sonuc_alani.setHtml(metin)

        if veri.get("ekran_goruntusu_yolu"):
            self.goruntu_etiketi.setPixmap(QPixmap(veri["ekran_goruntusu_yolu"]))
        else:
            self.goruntu_etiketi.setText("Ekran görüntüsü alınamadı")

        self._gecmisi_yukle()

    def _hata_goster(self, mesaj: str):
        self.analiz_butonu.setEnabled(True)
        self.durum_etiketi.setText("Hata oluştu.")
        QMessageBox.critical(self, "Hata", mesaj)

    def _gecmisi_yukle(self):
        try:
            yanit = requests.get(f"{BACKEND_URL}/history", timeout=10)
            self.gecmis_listesi.clear()
            for kayit in yanit.json():
                metin = f"[{kayit['nihai_karar']}] {kayit['url']}"
                oge = QListWidgetItem(metin)
                oge.setData(1000, kayit)
                self.gecmis_listesi.addItem(oge)
        except Exception:
            pass  # Backend henüz açılmamış olabilir, sessizce geç

    def _gecmisten_sec(self, oge: QListWidgetItem):
        veri = oge.data(1000)
        self._sonucu_goster(veri)


if __name__ == "__main__":
    uygulama = QApplication(sys.argv)
    pencere = AnaPencere()
    pencere.show()
    sys.exit(uygulama.exec())
