import os
import subprocess
import psutil
import time
import requests
import threading
import re 
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIG
# ==========================================
PANEL_URL = [
    "https://cs.dotaja.works"
]
AUTH_KEY = "GHOST_SECRET_2026"

FILE_LOGIN = "login.py"
FILE_LOOP = "loop.py"
LOG_FILE = "bot_log.txt"
MAPPING_FILE = "mapping_profil.txt"
PROFILE_DIR = "/root/chrome_profiles"

# --- PENGATURAN RESOLUSI LAYAR (PENTING!) ---
SCREEN_LOGIN = "1280x720x24" # Wajib lebar untuk Login & PyAutoGUI
SCREEN_LOOP = "500x500x24"   # Wajib kecil sesuai request modul_bot kamu

# --- HELPER FUNCTIONS ---
def run_bg(cmd):
    subprocess.Popen(cmd, shell=True)

def check_process(script_name):
    for p in psutil.process_iter(['cmdline']):
        try:
            if p.info['cmdline'] and script_name in p.info['cmdline']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def kill_processes():
    # Kill script python spesifik
    os.system(f"pkill -f {FILE_LOGIN}")
    os.system(f"pkill -f {FILE_LOOP}")
    # Kill Chrome & Driver
    os.system("pkill -f chrome")
    os.system("pkill -f chromedriver")
    # Kill Xvfb sisa
    os.system("pkill -f Xvfb")

def clean_system():
    os.system("ps -ef | awk '/defunct/ && !/awk/ {print $3}' | xargs -r kill -9")
    os.system("sync; echo 3 > /proc/sys/vm/drop_caches")

def auto_register():
    # --- KONFIGURASI SMART RETRY ---
    max_retries = 3  # Hanya mencoba 3 kali (Aman untuk limit worker)
    delay_retry = 3  # Jeda detik sebelum mencoba ulang
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Melapor ke Panel (Percobaan {attempt}/{max_retries})...")
            
            # 1. Ambil IP (Timeout 10s biar ga stuck)
            my_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
            
            success_count = 0
            # 2. Loop ke semua URL Panel
            for url in PANEL_URL:
                resp = requests.post(
                    f"{url}/api/register", 
                    json={"ip": my_ip, "auth": AUTH_KEY}, 
                    timeout=10
                )
                
                # Cek jika ada Error 404, 500, dll.
                if resp.status_code >= 400:
                    print(f"⚠️ Gagal lapor ke {url} | Status: {resp.status_code}")
                    # Raise error agar masuk ke 'except' dan memicu retry
                    resp.raise_for_status()
                else:
                    success_count += 1

            # Jika kode sampai sini tanpa error, berarti SUKSES.
            if success_count > 0:
                print("✅ Berhasil terhubung ke Panel.")
                return # KELUAR dari fungsi (Stop Loop)

        except Exception as e:
            # Tangkap semua error (Koneksi putus, 404, Timeout, dll)
            print(f"⚠️ Terjadi kesalahan: {e}")
            
            if attempt < max_retries:
                print(f"⏳ Mencoba ulang dalam {delay_retry} detik...")
                time.sleep(delay_retry)
            else:
                print("❌ Gagal total setelah 3x percobaan. Berhenti agar worker aman.")
                return

# --- API ENDPOINTS ---
@app.before_request
def auth():
    if request.headers.get("X-Auth-Key") != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/start/login', methods=['POST'])
def menu_1():
    if check_process(FILE_LOGIN):
        return jsonify({"msg": "⚠️ Login sudah berjalan"})
    
    # Login butuh layar 1280x720
    cmd = (
        "nohup xvfb-run -a --server-args='-screen 0 {screen}' "
        "{python} {login} > {log} 2>&1 &"
    ).format(
        screen=SCREEN_LOGIN,
        python="python3",
        login=FILE_LOGIN,
        log=LOG_FILE
    )
    run_bg(cmd)
    return jsonify({"msg": "Login Started"})

@app.route('/start/loop', methods=['POST'])
def menu_2():
    if check_process(FILE_LOOP):
        return jsonify({"msg": "⚠️ Loop sudah berjalan"})

    # Loop pake layar 500x500 (Sesuai Request)
    cmd = (
        "nohup xvfb-run -a --server-args='-screen 0 {screen}' "
        "{python} -u {loop} > {log} 2>&1 &"
    ).format(
        screen=SCREEN_LOOP,
        python="python3",
        loop=FILE_LOOP,
        log=LOG_FILE
    )
    run_bg(cmd)
    return jsonify({"msg": "Loop Started"})

@app.route('/logs', methods=['GET'])
def menu_3():
    if not os.path.exists(LOG_FILE): return jsonify({"logs": "Log kosong."})
    try:
        raw_logs = subprocess.check_output(['tail', '-n', '100', LOG_FILE]).decode('utf-8', errors='ignore')
        header = "=== MONITORING BOT"
        if header in raw_logs:
            final_logs = header + raw_logs.split(header)[-1]
        else:
            final_logs = raw_logs
        clean_logs = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', final_logs)
        return jsonify({"logs": clean_logs})
    except Exception as e: 
        return jsonify({"logs": f"Error: {str(e)}"})

@app.route('/stop', methods=['POST'])
def menu_4():
    kill_processes()
    clean_system()
    return jsonify({"msg": "Bot Stopped"})

@app.route('/file/<filename>', methods=['GET', 'POST', 'DELETE'])
def menu_5_6(filename):
    if filename not in ['email.txt', 'link.txt']: return jsonify({"error": "Forbidden"}), 403
    if request.method == 'POST': 
        content = request.json.get('content', '')
        if content:
            with open(filename, 'w') as f: f.write(content + "\n")
            os.system(f"sed -i '/^$/d' {filename}")
            return jsonify({"msg": "Data Added"})
    if request.method == 'DELETE':
        open(filename, 'w').close()
        return jsonify({"msg": "File Cleared"})
    return jsonify({"msg": "Ready"})

@app.route('/clean_ram', methods=['POST'])
def menu_7():
    clean_system()
    mem = psutil.virtual_memory()
    return jsonify({"msg": "RAM Optimized", "free": f"{mem.available // 1048576} MB"})

@app.route('/profiles', methods=['GET', 'DELETE'])
def menu_8():
    if request.method == 'GET':
        if not os.path.exists(MAPPING_FILE): return jsonify({"profiles": []})
        data = []
        with open(MAPPING_FILE, 'r') as f:
            for i, line in enumerate(f):
                if "|" in line:
                    parts = line.split('|')
                    data.append({"id": i, "name": parts[1].strip()})
        return jsonify({"profiles": data})
    if request.method == 'DELETE':
        target = request.json.get('target')
        if target == 'all':
            os.system(f"rm -rf {PROFILE_DIR}/*")
            open(MAPPING_FILE, 'w').close()
            return jsonify({"msg": "All Profiles Deleted"})
        else:
            try:
                idx = int(target)
                lines = open(MAPPING_FILE).readlines()
                if 0 <= idx < len(lines):
                    path = lines[idx].split('|')[0]
                    os.system(f"rm -rf {path}")
                    del lines[idx]
                    with open(MAPPING_FILE, 'w') as f: f.writelines(lines)
                    return jsonify({"msg": "Profile Deleted"})
            except: pass
        return jsonify({"msg": "Done"})

@app.route('/status', methods=['GET'])
def status():
    mem = psutil.virtual_memory()
    return jsonify({
        "login": check_process(FILE_LOGIN),
        "loop": check_process(FILE_LOOP),
        "ram_free": f"{mem.available // 1048576} MB"
    })

if __name__ == '__main__':
    threading.Thread(target=auto_register, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
