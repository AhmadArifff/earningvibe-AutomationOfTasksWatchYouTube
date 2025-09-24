# app_full_fixed.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from difflib import get_close_matches
import traceback

# # -------------- CONFIG --------------
# CHROME_OPTIONS = webdriver.ChromeOptions()
# CHROME_OPTIONS.add_argument("--start-maximized")
# CHROME_OPTIONS.add_argument("--force-device-scale-factor=0.67")  # zoom 67%

# driver = webdriver.Chrome(options=CHROME_OPTIONS)
# wait = WebDriverWait(driver, 15)
# actions = ActionChains(driver)

driver = None
wait = None
actions = None

def init_driver():
    global driver, wait, actions
    if driver is None:
        CHROME_OPTIONS = webdriver.ChromeOptions()
        CHROME_OPTIONS.add_argument("--start-maximized")
        CHROME_OPTIONS.add_argument("--force-device-scale-factor=0.67")
        driver = webdriver.Chrome(options=CHROME_OPTIONS)
        wait = WebDriverWait(driver, 15)
        actions = ActionChains(driver)
    return driver


# -------------- HELPERS --------------
def normalize(text: str) -> str:
    if text is None:
        return ""
    return "".join(ch for ch in text.lower() if ch.isalnum())


def find_visible_popup(max_wait=3):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        candidates = driver.find_elements(By.CLASS_NAME, "MuiDialogContent-root")
        for c in candidates:
            try:
                if c.is_displayed():
                    return c
            except:
                continue
        time.sleep(0.2)
    return None


def get_label_text(label_el):
    try:
        try:
            span = label_el.find_element(By.XPATH, ".//span[contains(@class,'MuiFormControlLabel-label')]")
        except:
            try:
                span = label_el.find_element(By.XPATH, ".//span[contains(@class,'MuiTypography-root')]")
            except:
                span = None
        if span and span.is_displayed():
            txt = span.get_attribute("innerText") or span.text
            return txt.strip()
    except:
        pass
    try:
        inp = label_el.find_element(By.XPATH, ".//input[@type='radio']")
        val = inp.get_attribute("value")
        return (val or "").strip()
    except:
        pass
    try:
        return label_el.text.strip()
    except:
        return ""


def wait_for_submit_enabled_in_popup(popup_el, timeout=10):
    end = time.time() + timeout
    submit_btn = None
    while time.time() < end:
        try:
            submit_btn = popup_el.find_element(By.XPATH, ".//button[normalize-space()='Submit' or contains(., 'Submit')]")
        except:
            submit_btn = None
        if submit_btn:
            disabled_attr = submit_btn.get_attribute("disabled")
            aria_disabled = submit_btn.get_attribute("aria-disabled")
            class_attr = submit_btn.get_attribute("class") or ""
            is_enabled_api = False
            try:
                is_enabled_api = submit_btn.is_enabled()
            except:
                pass
            if disabled_attr in (None, "false", "") and aria_disabled not in ("true", "True") and ("Mui-disabled" not in class_attr) and is_enabled_api:
                return submit_btn
        time.sleep(0.4)
    return submit_btn


def click_element_with_retries(el):
    try:
        el.click()
        return True, "click()"
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
        time.sleep(0.15)
        driver.execute_script("arguments[0].click();", el)
        return True, "js-click"
    except Exception:
        pass
    try:
        actions.move_to_element(el).pause(0.05).click(el).perform()
        return True, "actions-click"
    except Exception:
        pass
    try:
        el.send_keys("\n")
        return True, "enter"
    except Exception:
        pass
    return False, "all click attempts failed"


# -------------- CORE: handle popup --------------
def handle_channel_popup(youtube_channel: str, popup_wait=3):
    try:
        popup = find_visible_popup(max_wait=popup_wait)
        if not popup:
            print("👌 Tidak ada popup channel muncul.")
            return False

        print("💡 Popup konfirmasi channel muncul (visible).")
        labels = popup.find_elements(By.XPATH, ".//label[contains(@class,'MuiFormControlLabel-root') or contains(@class,'MuiFormControlLabel')]")
        visible_labels = [l for l in labels if l.is_displayed()]
        if not visible_labels:
            inputs = popup.find_elements(By.XPATH, ".//input[@type='radio']")
            visible_inputs = [i for i in inputs if i.is_displayed()]
            visible_labels = []
            for inp in visible_inputs:
                try:
                    lbl = inp.find_element(By.XPATH, "./ancestor::label")
                    if lbl.is_displayed():
                        visible_labels.append(lbl)
                except:
                    pass
        if not visible_labels:
            print("❌ Tidak ada opsi radio terlihat di popup.")
            try:
                print("🔍 Snapshot popup (awal 300 char):", popup.get_attribute("innerHTML")[:300])
            except:
                pass
            return False

        options = []
        for lbl in visible_labels:
            txt = get_label_text(lbl)
            try:
                inp = lbl.find_element(By.XPATH, ".//input[@type='radio']")
                val = inp.get_attribute("value") or ""
            except:
                val = ""
            options.append({"label_el": lbl, "text": txt, "value": val})

        print("📋 Opsi radio (visible) di popup:")
        for idx, o in enumerate(options, start=1):
            print(f"   {idx}. text='{o['text']}' | value='{o['value']}' | norm='{normalize(o['text'])}'")

        target_raw = youtube_channel or ""
        if target_raw.startswith("@"):
            target_raw = target_raw[1:]
        print(f"🔎 Cari match untuk: '{target_raw}'")

        norm_map = {}
        norm_list = []
        for o in options:
            n = normalize(o["text"]) or normalize(o["value"])
            norm_list.append(n)
            norm_map[n] = o

        matched_option = None
        if target_raw:
            target_norm = normalize(target_raw)
            candidate_norms = get_close_matches(target_norm, norm_list, n=1, cutoff=0.35)
            if candidate_norms:
                matched_option = norm_map.get(candidate_norms[0])
                print(f"✅ Channel cocok ditemukan (fuzzy): '{matched_option['text']}'")
        if matched_option is None and options:
            matched_option = options[0]
            print(f"⚠️ Fallback: memilih opsi pertama: '{matched_option['text']}'")

        lbl_el = matched_option["label_el"]
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl_el)
            time.sleep(0.12)
            driver.execute_script("arguments[0].click();", lbl_el)
        except:
            try:
                lbl_el.click()
            except:
                try:
                    actions.move_to_element(lbl_el).click().perform()
                except:
                    try:
                        inp = lbl_el.find_element(By.XPATH, ".//input[@type='radio']")
                        driver.execute_script("arguments[0].click();", inp)
                    except:
                        pass
        print(f"☑️ Radio button '{matched_option['text']}' dicentang (attempt).")

        submit_btn = wait_for_submit_enabled_in_popup(popup, timeout=10)
        if not submit_btn:
            time.sleep(5)
            submit_btn = wait_for_submit_enabled_in_popup(popup, timeout=2)
        if not submit_btn:
            try:
                submit_btn = popup.find_element(By.XPATH, ".//button[normalize-space()='Submit' or contains(., 'Submit')]")
            except:
                submit_btn = None
        if not submit_btn:
            print("❌ Tidak menemukan tombol Submit di popup. Skip.")
            return False

        print(f"🔔 Status tombol sebelum klik: enabled={submit_btn.is_enabled()}, disabled_attr={submit_btn.get_attribute('disabled')}, aria-disabled={submit_btn.get_attribute('aria-disabled')}")
        success, method_info = click_element_with_retries(submit_btn)
        if not success:
            try:
                driver.execute_script("arguments[0].removeAttribute('disabled'); arguments[0].setAttribute('aria-disabled','false');", submit_btn)
                time.sleep(0.12)
                driver.execute_script("arguments[0].click();", submit_btn)
                success = True
                print("📤 Submit berhasil via removeAttribute + js-click (darurat).")
            except:
                success = False

        if success:
            try:
                WebDriverWait(driver, 3).until(EC.staleness_of(popup))
                print("✅ Popup konfirmasi tertutup, submit sukses!")
                return True
            except:
                try:
                    WebDriverWait(driver, 4).until(EC.invisibility_of_element(popup))
                    print("✅ Popup konfirmasi tertutup (invisibility).")
                    return True
                except:
                    print("⚠️ Popup masih ada setelah klik.")
                    try:
                        print(popup.get_attribute("innerHTML")[:400], "...")
                    except:
                        pass
                    return False
        else:
            return False

    except Exception:
        print(traceback.format_exc())
        return False


def handle_channel_popup_with_retry(youtube_channel: str, max_attempts=2):
    attempt = 1
    while attempt <= max_attempts:
        print(f"🔁 Attempt {attempt} untuk popup channel...")
        success = handle_channel_popup(youtube_channel, popup_wait=3)
        if success:
            print(f"✅ Popup channel berhasil di-handle di attempt {attempt}")
            return True
        else:
            print(f"⚠️ Popup masih ada / gagal submit. Retry {attempt+1}/{max_attempts}")
            time.sleep(2)
            attempt += 1
    print(f"❌ Gagal handle popup channel setelah {max_attempts} attempt, skip task ini.")
    return False


# -------------- MAIN FLOW --------------
def login_and_navigate(email, password):
    # driver.get("https://earningvibe.com/login/")
    drv = init_driver()
    drv.get("https://earningvibe.com/login/")
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    email_input.clear()
    email_input.send_keys(email)
    password_input = driver.find_element(By.NAME, "password")
    password_input.clear()
    password_input.send_keys(password)
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit' and text()='Login']")
    login_btn.click()
    print("✅ Login berhasil, masuk ke dashboard...")
    time.sleep(3)
    youtube_sidebar = wait.until(EC.element_to_be_clickable((By.XPATH, "//p[text()='Youtube']")))
    youtube_sidebar.click()
    print("📺 Sidebar YouTube diklik...")
    time.sleep(2)


def extract_channel_from_youtube_tab():
    last_channel_name = None
    try:
        channel_el = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#channel-name #text a"))
        )
        last_channel_name = channel_el.text.strip()
        print(f"📛 Nama channel terdeteksi (header): {last_channel_name}")
        return last_channel_name
    except:
        pass
    try:
        channel_reel = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "yt-reel-channel-bar-view-model span a"))
        )
        raw_name = channel_reel.text.strip()
        if raw_name.startswith("@"):
            parsed = raw_name[1:]
            print(f"📛 Nama channel terdeteksi (reel bar, parsed): {parsed}")
            return parsed
        else:
            print(f"📛 Nama channel terdeteksi (reel bar): {raw_name}")
            return raw_name
    except Exception as e:
        print("⚠️ Tidak bisa ambil nama channel di tab YouTube:", e)
        return None

def retry_action(func, attempts=2, delay=0.5, name="action"):
    for i in range(1, attempts + 1):
        try:
            return func()
        except Exception as e:
            print(f"⚠️ Retry {i}/{attempts} gagal untuk {name}: {e}")
            time.sleep(delay)
    return None

def click_element(el, name="element", scroll=True):
    if not el:
        return False
    try:
        if scroll:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.1)
        el.click()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except:
            try:
                actions.move_to_element(el).click().perform()
                return True
            except:
                return False

def get_visible_text(el):
    try:
        if el.is_displayed():
            return el.text.strip()
    except:
        return ""

def fetch_profile_info():
    def _fetch():
        avatar_btn = driver.find_element(By.XPATH, "//button[.//div[contains(@class,'MuiAvatar-root')]]")
        # tunggu backdrop hilang
        try:
            WebDriverWait(driver, 2).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.MuiBackdrop-root"))
            )
        except:
            pass
        click_element(avatar_btn, "avatar profile")
        info_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.MuiBox-root.css-1y19tqg")))
        p_tags = info_box.find_elements(By.XPATH, ".//p[contains(@class,'MuiTypography-body2')]")
        email = get_visible_text(p_tags[0]) if p_tags else None
        balance = get_visible_text(p_tags[-1]) if p_tags else None
        click_element(avatar_btn, "avatar close")
        return email, balance
    result = retry_action(_fetch, attempts=4, delay=0.6, name="fetch profile info")
    if result:
        email, balance = result
        print(f"📧 Gmail: {email} | 💰 Balance: {balance}")
        return email, balance
    else:
        print("⚠️ Gagal ambil Gmail / Balance")
        return None, None

def process_page(stop_flag=None):
    cards = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'MuiCard-root')]//img[@src='/svg/youtube-icon.svg']/ancestor::div[contains(@class,'MuiCard-root')]"
    )
    print(f"🔍 Ditemukan {len(cards)} tugas YouTube di halaman ini")

    # Ambil info Gmail dan Balance sekali sebelum proses semua card
    email, balance = fetch_profile_info()

    for i, card in enumerate(cards, start=1):
        if stop_flag and stop_flag.get("stop"):
            print("🛑 Stop flag terdeteksi di tengah card loop, keluar...")
            return

        email, balance = fetch_profile_info()
        try:
            print(f"\n▶️ Memulai tugas {i}...")
            last_channel_name = None
            # Klik submission task
            while True:
                if stop_flag and stop_flag.get("stop"):
                    print("🛑 Stop flag terdeteksi di dalam submission loop, keluar...")
                    return
                try:
                    submission_btn = card.find_element(By.XPATH, ".//button[.//span[contains(@class,'css-57i5t7')]]")
                    click_element(submission_btn, "submission button") 
                    print("📝 Klik tombol submission task...")
                    time.sleep(10)
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                        print("📂 Tab YouTube terbuka...")
                        last_channel_name = extract_channel_from_youtube_tab()
                        driver.close()
                        print("❌ Tab YouTube ditutup...")
                        driver.switch_to.window(driver.window_handles[0])
                    else:
                        print("ℹ️ Tidak ada tab YouTube baru terbuka setelah klik submission.")
                except:
                    print("✅ Semua submission task habis untuk card ini (no more submission button).")
                    break

            # Klik tombol collect reward
            try:
                collect_btn = WebDriverWait(card, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//button[.//span[contains(@class,'css-ulktgh')]]"))
                )
            except Exception:
                all_buttons = card.find_elements(By.XPATH, ".//button")
                collect_btn = all_buttons[-1] if all_buttons else None

            if collect_btn:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.MuiBackdrop-root"))
                    )
                except:
                    pass
                click_element(collect_btn, "collect button")  
                print("🏆 Klik tombol collect reward...")
                time.sleep(0.8)
            else:
                print("⚠️ Tombol collect reward tidak ditemukan!")

            # Handle popup channel
            ok = handle_channel_popup_with_retry(last_channel_name, max_attempts=2)
            if ok:
                print("✔️ Popup di-handle dan submit sukses.")
            else:
                print("❌ Popup gagal di-handle, lanjut task berikutnya.")

            print(f"✅ Tugas {i} selesai!")
            time.sleep(1.2)
        except Exception as e:
            print(f"⚠️ Error di tugas {i}:", e)
            traceback.print_exc()


def process_page_with_loop(log_message, stats, stop_flag):
    try:
        page_num = 1
        while not stop_flag.get("stop", False):
            log_message(f"\n📄 Sedang proses halaman {page_num}...")
            process_page(stop_flag=stop_flag)

            if stop_flag.get("stop"):
                log_message("🛑 Stop flag terdeteksi, keluar dari loop.")
                break

            stats["tasks_done"] += 1
            stats["reward_today"] += 1  

            # cari tombol next
            next_btns = driver.find_elements(By.XPATH, "//button[@aria-label='Go to next page']")
            next_btn = None
            for b in next_btns:
                cls = b.get_attribute("class") or ""
                disabled = b.get_attribute("disabled")
                if "Mui-disabled" not in cls and not disabled:
                    next_btn = b
                    break

            if not next_btn:
                log_message("⛔ Tidak ada tombol Next Page aktif, selesai semua!")
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
                time.sleep(0.2)
                next_btn.click()
                log_message("➡️ Klik tombol Next Page...")
            except:
                driver.execute_script("arguments[0].click();", next_btn)
                log_message("➡️ Klik tombol Next Page (js-fallback)...")

            page_num += 1
            time.sleep(1.5)

        log_message("\n🎉 Semua tugas selesai / dihentikan.")
    except Exception as e:
        log_message(f"❗ Fatal error di loop: {e}")
        traceback.print_exc()
