# ---------- kode utama ----------
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

def get_ip_with_browser(proxy: str = None, headless: bool = False, timeout: int = 20):
    """
    Buka whatismyipaddress.com (via Selenium), optionally lewat proxy,
    dan kembalikan dict {'ipv4': {'text':..., 'href':...}, 'ipv6': {...}}
    """
    opts = Options()
    if headless:
        # jika butuh headless, aktifkan
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
    # optional: non-root sandbox flags (untuk beberapa environment)
    opts.add_argument("--disable-dev-shm-usage")

    if proxy:
        opts.add_argument(f'--proxy-server={proxy}')

    # inisialisasi driver via webdriver-manager (otomatis download chromedriver)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    result = {"ipv4": None, "ipv6": None, "page_title": None}
    try:
        url = "https://whatismyipaddress.com"
        driver.get(url)

        # tunggu sampai elemen id ipv4 muncul (atau timeout)
        wait = WebDriverWait(driver, timeout)
        # kadang struktur situs berubah; saya coba dua pendekatan:
        # 1) cari elemen id 'ipv4' dan 'ipv6'
        # 2) fallback: cari text yang mengandung "IPv4:" / "IPv6:"
        try:
            ipv4_el = wait.until(EC.presence_of_element_located((By.ID, "ipv4")))
        except Exception:
            ipv4_el = None

        try:
            ipv6_el = wait.until(EC.presence_of_element_located((By.ID, "ipv6")))
        except Exception:
            ipv6_el = None

        # Ambil title halaman
        result["page_title"] = driver.title

        # Ambil IPv4
        if ipv4_el:
            # ipv4_el bisa berisi anchor di dalamnya
            try:
                a = ipv4_el.find_element(By.TAG_NAME, "a")
                ipv4_text = a.text.strip()
                ipv4_href = a.get_attribute("href")
            except Exception:
                ipv4_text = ipv4_el.text.strip()
                ipv4_href = None

            result["ipv4"] = {"text": ipv4_text, "href": ipv4_href}
        else:
            # fallback: cari teks yang mengandung "IPv4"
            try:
                ipv4_fallback = driver.find_element(By.XPATH, "//*[contains(text(),'IPv4:') or contains(text(),'IPv4')]")
                result["ipv4"] = {"text": ipv4_fallback.text.strip(), "href": None}
            except Exception:
                result["ipv4"] = None

        # Ambil IPv6
        if ipv6_el:
            try:
                a6 = ipv6_el.find_element(By.TAG_NAME, "a")
                ipv6_text = a6.text.strip()
                ipv6_href = a6.get_attribute("href")
            except Exception:
                ipv6_text = ipv6_el.text.strip()
                ipv6_href = None

            result["ipv6"] = {"text": ipv6_text, "href": ipv6_href}
        else:
            # fallback: cari teks yang mengandung "IPv6"
            try:
                ipv6_fallback = driver.find_element(By.XPATH, "//*[contains(text(),'IPv6:') or contains(text(),'IPv6')]")
                result["ipv6"] = {"text": ipv6_fallback.text.strip(), "href": None}
            except Exception:
                result["ipv6"] = None

        # kecilkan kemungkinan halaman belum sepenuhnya render JS dengan delay singkat (opsional)
        time.sleep(0.5)

    finally:
        driver.quit()

    return result


if __name__ == "__main__":
    # contoh: tanpa proxy
    res = get_ip_with_browser(proxy=None, headless=False, timeout=20)
    print("Page title:", res["page_title"])
    print("IPv4:", res["ipv4"])
    print("IPv6:", res["ipv6"])

    # contoh: dengan proxy (ganti proxy jika mau)
    # proxy = "123.45.67.89:8080"
    # res2 = get_ip_with_browser(proxy=proxy, headless=True)
    # print("Via proxy -> IPv4:", res2["ipv4"])