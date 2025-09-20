# ---------- kode utama ----------
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

def open_youtube(idx, url, headless=False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        print(f"[{idx}] Membuka {url}")
        driver.get(url)

        # Biarkan browser terbuka selama 2 menit (120 detik)
        time.sleep(120)

    finally:
        driver.quit()
        print(f"[{idx}] Browser ditutup")

if __name__ == "__main__":
    yt_url = "https://www.youtube.com/shorts/IxZw_BWNueQ"

    for i in range(1, 4):   # coba buka 3 browser dulu
        open_youtube(i, yt_url, headless=False)  # headless=False supaya kelihatan
