from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

# --- KONFIGURASI ---
SLEEP_SEBELUM_AKSI = 20
SLEEP_SESUDAH_AKSI = 20
SLEEP_JIKA_ERROR = 5

def get_options(user_data_dir, profile_dir):
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_dir}")
    
    # --- BLOCK POPUPS (UPDATE & RESTORE PAGES) ---
    options.add_argument("--test-type")
    options.add_argument("--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    # ---------------------------------------------

    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-features=InfiniteSessionRestore,Translate,OptimizationGuideModelDownloading,MediaRouter,MetricsReporting")
    
    # SAYA KEMBALIKAN KE 500x500 SESUAI PERMINTAAN
    options.add_argument("--window-size=500,500")
    
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu") 
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--disable-setuid-sandbox")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.exit_type": "Normal", # Paksa simpan state normal
        "profile.exited_cleanly": True
    })
    return options

def read_file_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_profiles_from_mapping(path):
    profiles = []
    lines = read_file_lines(path)
    for line in lines:
        if "|" in line:
            parts = line.split("|")
            path_dir = parts[0].strip()
            name = parts[1].strip()
            profiles.append({
                "name": name,
                "user_data_dir": path_dir,
                "profile_dir": "Default",
                "window_position": (0, 0)
            })
    return profiles

# FUNGSI DI BAWAH INI SAMA PERSIS DENGAN YANG KAMU UPLOAD
# TIDAK SAYA UBAH LOGIKANYA
def process_single_link(driver, link, profile_name, status_dict):
    try:
        status_dict[profile_name] = f"Membuka: {link}..."
        driver.get(link)
        wait = WebDriverWait(driver, 5)
        
        status_dict[profile_name] = "tombol 'Trust'..."
        try:
            trust = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'I trust the owner')]")))
            trust.click()
        except: pass # Skip if not found/already trusted

        status_dict[profile_name] = "tombol 'Open'..."
        open_ws = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Open Workspace')]")))
        open_ws.click()
        
        status_dict[profile_name] = "Iframe IDE..."
        iframe_element = wait.until(EC.visibility_of_element_located((
                By.CSS_SELECTOR, "iframe.the-iframe.is-loaded[src*='ide-start']"
            )))
        
        status_dict[profile_name] = f"Idle {SLEEP_SEBELUM_AKSI}shortcut..."
        time.sleep(SLEEP_SEBELUM_AKSI)
        
        driver.find_element(By.TAG_NAME, "body").click()
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("c").key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
        
        status_dict[profile_name] = "Shortcut dikirim"
        time.sleep(SLEEP_SESUDAH_AKSI)
        
        status_dict[profile_name] = "✅ Selesai link ini."
        return True

    except Exception as e:
        status_dict[profile_name] = f"❌ Error: {str(e)[:20]}..."
        time.sleep(SLEEP_JIKA_ERROR)
        return False
        
def worker(profile_name, user_data_dir, profile_dir, window_position, links, status_dict):
    if not links:
        status_dict[profile_name] = "Tidak ada link."
        return

    options = get_options(user_data_dir, profile_dir)
    driver = None
    try:
        status_dict[profile_name] = "Membuka Browser Nonstop..."
        driver = webdriver.Chrome(options=options)

        if window_position:
            driver.set_window_position(*window_position)

        # --- MODIFIKASI LOOPING NONSTOP ---
        putaran = 1
        while True: # Loop ini akan menjaga browser tetap hidup selamanya
            status_dict[profile_name] = f"🔄 Masuk Putaran ke-{putaran}"
            
            for i, link in enumerate(links):
                # Update status progress global
                status_dict[profile_name] = f"[Putaran {putaran}] Link ({i+1}/{len(links)}) - Proses..."
                process_single_link(driver, link, profile_name, status_dict)
            
            # Setelah semua link selesai, JANGAN QUIT.
            # Kita istirahat sebentar, lalu lanjut loop while (balik ke link 1)
            status_dict[profile_name] = f"✅ Putaran {putaran} Selesai. Mengulang..."
            putaran += 1
            time.sleep(3) 
        # ----------------------------------
            
    except Exception as e:
        status_dict[profile_name] = f"CRITICAL ERROR: {e}"
    finally:
        # Browser hanya mati jika error parah atau dimatikan oleh loop.py
        if driver:
            try:
                driver.quit()
            except: pass