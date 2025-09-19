from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- SETUP SELENIUM ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--force-device-scale-factor=0.67")  # set zoom 67%
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 15)


def handle_channel_popup(channel_name=None):
    """Cek dan isi popup channel kalau muncul"""
    try:
        popup = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'MuiDialog-paper')]"))
        )
        print("💡 Popup konfirmasi channel muncul!")

        options_radio = popup.find_elements(By.XPATH, ".//label//span[contains(@class,'MuiTypography-body1')]")
        chosen = False
        if channel_name:
            for opt in options_radio:
                if channel_name.lower().strip() == opt.text.strip().lower():
                    opt.click()
                    print(f"✅ Channel '{opt.text}' dipilih di popup")
                    chosen = True
                    break
        if not chosen and options_radio:
            options_radio[0].click()
            print("⚠️ Nama channel tidak cocok, pilih opsi pertama agar submit aktif")

        submit_btn = popup.find_element(By.XPATH, ".//button[normalize-space()='Submit']")
        wait.until(EC.element_to_be_clickable((By.XPATH, ".//button[normalize-space()='Submit']")))
        submit_btn.click()
        print("📤 Submit popup channel berhasil!")
        time.sleep(3)

    except:
        print("👌 Tidak ada popup channel")


# --- STEP 1: LOGIN ---
driver.get("https://earningvibe.com/login/")

email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
email_input.clear()
email_input.send_keys("example@gmail.com")

password_input = driver.find_element(By.NAME, "password")
password_input.clear()
password_input.send_keys("examplepassword")

login_btn = driver.find_element(By.XPATH, "//button[@type='submit' and text()='Login']")
login_btn.click()
print("✅ Login berhasil, masuk ke dashboard...")
time.sleep(3)

# --- STEP 2: Klik sidebar YouTube ---
youtube_sidebar = wait.until(EC.element_to_be_clickable((By.XPATH, "//p[text()='Youtube']")))
youtube_sidebar.click()
print("📺 Sidebar YouTube diklik...")
time.sleep(3)


def process_page():
    """Proses semua card di halaman saat ini"""
    cards = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'MuiCard-root')]//img[@src='/svg/youtube-icon.svg']/ancestor::div[contains(@class,'MuiCard-root')]"
    )

    print(f"🔍 Ditemukan {len(cards)} tugas YouTube di halaman ini")

    for i, card in enumerate(cards, start=1):
        try:
            print(f"\n▶️ Memulai tugas {i}...")

            # --- LOOP submission task sampai habis ---
            while True:
                try:
                    submission_btn = card.find_element(
                        By.XPATH,
                        ".//button[.//span[contains(@class,'css-57i5t7')]]"
                    )
                    submission_btn.click()
                    print("📝 Klik tombol submission task...")

                    time.sleep(20)

                    # --- Pindah ke tab YouTube ---
                    channel_name = None
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        print("📂 Tab YouTube terbuka...")

                        try:
                            channel_el = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "#channel-name #text a"))
                            )
                            channel_name = channel_el.text.strip()
                            print(f"📛 Nama channel terdeteksi: {channel_name}")
                        except Exception as e:
                            print(f"⚠️ Tidak bisa ambil nama channel: {e}")

                        driver.close()
                        print("❌ Tab YouTube ditutup...")
                        driver.switch_to.window(driver.window_handles[0])

                    # --- Handle popup setelah submission ---
                    handle_channel_popup(channel_name)

                except:
                    print("✅ Semua submission task habis untuk card ini")
                    break

            # --- Klik tombol collect reward ---
            try:
                collect_btn = WebDriverWait(card, 10).until(
                    EC.element_to_be_clickable((By.XPATH, ".//button[.//span[contains(@class,'css-ulktgh')]]"))
                )
            except:
                # fallback: ambil tombol terakhir di card
                all_buttons = card.find_elements(By.XPATH, ".//button")
                collect_btn = all_buttons[-1]

            collect_btn.click()
            print("🏆 Klik tombol collect reward...")

            # --- Handle popup setelah reward ---
            handle_channel_popup()

            print(f"✅ Tugas {i} selesai!")
            time.sleep(2)

        except Exception as e:
            print(f"⚠️ Error di tugas {i}: {e}")


# --- STEP 4: Loop semua halaman dengan pagination ---
page_num = 1

while True:
    print(f"\n📄 Sedang proses halaman {page_num}...")
    process_page()

    try:
        next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to next page']"))
        )
        next_btn.click()
        print("➡️ Klik tombol Next Page...")
        page_num += 1

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'MuiCard-root')]//img[@src='/svg/youtube-icon.svg']")
                )
            )
        except:
            print("⚠️ Tidak ada card muncul setelah klik Next (mungkin halaman kosong).")
            break

        time.sleep(2)

    except:
        print("⛔ Tidak ada tombol Next Page, selesai semua!")
        break


print("\n🎉 Semua tugas di semua halaman selesai! Browser tetap terbuka, tutup manual kalau sudah beres.")



# driver.quit()
