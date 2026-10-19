"""
Tek tikla baslatici.

Yaptigi isler (sirayla):
1) Backend (FastAPI) zaten calisiyor mu diye bakar
2) Calismiyorsa arka planda gorunmez sekilde baslatir
3) Backend hazir olana kadar bekler
4) Masaustu arayuzunu (PyQt6) acar
5) Arayuz kapatilinca backend'i de kapatir

Backend ciktilari 'backend.log' dosyasina yazilir (hata olursa buraya bak).
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent
BACKEND_DIZINI = KOK / "backend"
ARAYUZ_DOSYASI = KOK / "desktop" / "app.py"
LOG_DOSYASI = KOK / "backend.log"

HOST = "127.0.0.1"
PORT = 8000
BEKLEME_SANIYESI = 40  # backend en fazla bu kadar sure icinde acilmali


def hata_goster(mesaj: str):
    """Hatayi hem konsola yazar hem de Windows'ta pencere olarak gosterir."""
    print("HATA:", mesaj)
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, mesaj, "Phishing Analizoru", 0x10)
        except Exception:
            pass


def port_acik_mi() -> bool:
    """Backend'in portu dinleyip dinlemedigini kontrol eder."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, PORT)) == 0


def backend_baslat():
    """Backend'i gorunmez bir alt surec olarak baslatir."""
    log = open(LOG_DOSYASI, "w", encoding="utf-8")
    ek_ayarlar = {}
    if os.name == "nt":
        # Windows'ta siyah konsol penceresi acilmasin
        ek_ayarlar["creationflags"] = subprocess.CREATE_NO_WINDOW

    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", HOST, "--port", str(PORT)],
        cwd=BACKEND_DIZINI,
        stdout=log,
        stderr=subprocess.STDOUT,
        **ek_ayarlar,
    )


def main():
    backend = None

    if port_acik_mi():
        print("Backend zaten calisiyor, onu kullaniyorum.")
    else:
        print("Backend baslatiliyor...")
        backend = backend_baslat()

        baslangic = time.time()
        while not port_acik_mi():
            if backend.poll() is not None:
                hata_goster("Backend baslatilamadi. Detay icin backend.log dosyasina bak.")
                return
            if time.time() - baslangic > BEKLEME_SANIYESI:
                backend.terminate()
                hata_goster("Backend zamaninda acilmadi. Detay icin backend.log dosyasina bak.")
                return
            time.sleep(0.5)
        print("Backend hazir.")

    try:
        # Arayuz kapanana kadar burada bekler
        subprocess.run([sys.executable, str(ARAYUZ_DOSYASI)], cwd=KOK)
    finally:
        # Arayuz kapaninca, biz baslattiysak backend'i de kapat
        if backend is not None:
            backend.terminate()
            try:
                backend.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend.kill()


if __name__ == "__main__":
    main()
