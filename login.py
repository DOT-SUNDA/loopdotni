import os
import time
import subprocess
import sys
import requests
import json
import pyautogui 
import mss  # <--- PERBAIKAN: Tambah library mss

# ==========================================
# ⚙️ KONFIGURASI
# ==========================================
TG_BOT_TOKEN = "8455364218:AAFoy_mvhZi9HYeTM48hO9aXapE-cYmWuCs"
TG_CHAT_ID = "-1003647070115"
PASSWORD = "Henstyle56"      
PROFILE_PREFIX = "dotaja"     
START_INDEX = 1               

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CHROME_PATH = "/usr/bin/google-chrome" 
BASE_PROFILE_DIR = "/root/chrome_profiles"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
EMAIL_FILE = os.path.join(BASE_PATH, "email.txt")
MAPPING_FILE = os.path.join(BASE_PATH, "mapping_profil.txt")

# --- AMBIL IP VPS ---
try:
    MY_IP = requests.get('https://api.ipify.org', timeout=10).text.strip()
except:
    MY_IP = "Unknown IP"

# ==========================================
# FUNGSI PENDUKUNG
# ==========================================
def save_mapping(full_path, profile_name):
    """
    Mencatat profil ke file mapping.
    Sinkron dengan AgentCS: Jika folder pernah dihapus lalu dibuat lagi, 
    mapping tetap memastikan path tersebut unik di dalam list.
    """
    new_entry = f"{full_path}|{profile_name}"
    existing_entries = []
    
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            existing_entries = [line.strip() for line in f if line.strip()]
            
    # Cek apakah path directory sudah ada di list
    path_exists = any(line.split('|')[0] == full_path for line in existing_entries if '|' in line)
    
    if not path_exists:
        with open(MAPPING_FILE, "a") as f:
            f.write(new_entry + "\n")
        print(f"✅ Mapping baru ditambahkan: {profile_name}")
    else:
        print(f"ℹ️ Mapping untuk {profile_name} sudah ada, tidak menulis ulang.")

def fix_crash_restore_popup(profile_path):
    pref_file = os.path.join(profile_path, "Default", "Preferences")
    if not os.path.exists(pref_file): return
    try:
        with open(pref_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "profile" in data:
            data["profile"]["exit_type"] = "Normal"
            data["profile"]["exited_cleanly"] = True
            with open(pref_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
    except: pass

def send_telegram_photo(caption, image_path):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    try:
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                full_caption = f"🌐 *IP VPS*: `{MY_IP}`\n{caption}"
                requests.post(url, files={'photo': photo}, data={'chat_id': TG_CHAT_ID, 'caption': full_caption, 'parse_mode': 'Markdown'})
    except: pass

def kill_chrome():
    os.system("pkill -9 -f chrome > /dev/null 2>&1")
    time.sleep(1)

# ==========================================
# MAIN EXECUTION
# ==========================================
if not os.path.exists(EMAIL_FILE): sys.exit(1)

with open(EMAIL_FILE, "r") as f:
    EMAILS = [line.strip() for line in f if line.strip()]

kill_chrome()

for i, EMAIL in enumerate(EMAILS, start=START_INDEX):
    folder_name = f"{PROFILE_PREFIX}{i:02d}"
    full_profile_path = os.path.join(BASE_PROFILE_DIR, folder_name)
    
    # Buat folder jika belum ada (misal setelah dihapus oleh AgentCS)
    if not os.path.exists(full_profile_path):
        os.makedirs(full_profile_path)
    
    save_mapping(full_profile_path, folder_name)
    fix_crash_restore_popup(full_profile_path)

    print(f"🚀 Login: {EMAIL} ({folder_name}) | VPS: {MY_IP}")

    cmd = [
        CHROME_PATH, 
        "--no-sandbox", "--disable-dev-shm-usage", "--start-maximized",
        "--test-type",
        "--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'",
        "--disable-component-update",
        "--disable-session-crashed-bubble",
        "--no-first-run", "--no-default-browser-check", 
        f"--window-size={SCREEN_WIDTH},{SCREEN_HEIGHT}",
        f"--user-data-dir={full_profile_path}", 
        "https://idx.google.com/joko" 
    ]
    
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(15) 

    try:
        pyautogui.write(EMAIL, interval=0.1)
        pyautogui.press("enter")
        time.sleep(8) 

        pyautogui.write(PASSWORD, interval=0.1)
        pyautogui.press("enter")
        time.sleep(15) 

        ss_path = os.path.join(BASE_PATH, f"bukti_{folder_name}.png")
        
        # --- PERBAIKAN BAGIAN SCREENSHOT (MENGHINDARI PILLOW/GNOME) ---
        try:
            with mss.mss() as sct:
                # Mengambil screenshot monitor pertama (biasanya Xvfb default)
                sct.shot(mon=-1, output=ss_path)
        except Exception as e_ss:
            print(f"⚠️ Gagal screenshot via mss: {e_ss}")
        # --------------------------------------------------------------

        send_telegram_photo(f"✅ *LOGIN OK*: `{EMAIL}`\nProfile: `{folder_name}`", ss_path)
        
        if os.path.exists(ss_path):
            os.remove(ss_path)
    except Exception as e:
        print(f"❌ Error: {e}")

    kill_chrome()
    time.sleep(2)

print(f"✅ Selesai! (VPS: {MY_IP})")