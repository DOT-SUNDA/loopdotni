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
PANEL_URL = ["https://cs.dotaja.works"]
AUTH_KEY = "GHOST_SECRET_2026"

FILE_LOGIN = "login.py"
FILE_LOOP = "loop.py"
LOG_FILE = "bot_log.txt"
MAPPING_FILE = "mapping_profil.txt"
PROFILE_DIR = "/root/chrome_profiles"

SCREEN_LOGIN = "1280x720x24"
SCREEN_LOOP = "500x500x24"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
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
    os.system(f"pkill -f {FILE_LOGIN}")
    os.system(f"pkill -f {FILE_LOOP}")
    os.system("pkill -f chrome")
    os.system("pkill -f chromedriver")
    os.system("pkill -f Xvfb")

def clean_system():
    os.system("ps -ef | awk '/defunct/ && !/awk/ {print $3}' | xargs -r kill -9")
    os.system("sync; echo 3 > /proc/sys/vm/drop_caches")

def auto_register():
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            my_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
            for url in PANEL_URL:
                requests.post(f"{url}/api/register", json={"ip": my_ip, "auth": AUTH_KEY}, timeout=10)
            return 
        except:
            time.sleep(3)

# ==========================================
# 🛡️ AUTH & API ENDPOINTS
# ==========================================

@app.before_request
def auth():
    if request.headers.get("X-Auth-Key") != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/status', methods=['GET'])
def status():
    mem = psutil.virtual_memory()
    return jsonify({
        "login": check_process(FILE_LOGIN),
        "loop": check_process(FILE_LOOP),
        "ram_free": f"{mem.available // 1048576} MB"
    })

@app.route('/start/login', methods=['POST'])
def menu_1():
    if check_process(FILE_LOGIN): return jsonify({"msg": "Active"})
    run_bg(f"nohup xvfb-run -a --server-args='-screen 0 {SCREEN_LOGIN}' python3 {FILE_LOGIN} > {LOG_FILE} 2>&1 &")
    return jsonify({"msg": "Login Started"})

@app.route('/start/loop', methods=['POST'])
def menu_2():
    if check_process(FILE_LOOP): return jsonify({"msg": "Active"})
    run_bg(f"nohup xvfb-run -a --server-args='-screen 0 {SCREEN_LOOP}' python3 -u {FILE_LOOP} > {LOG_FILE} 2>&1 &")
    return jsonify({"msg": "Loop Started"})

@app.route('/logs', methods=['GET'])
def menu_3():
    if not os.path.exists(LOG_FILE): return jsonify({"logs": ""})
    raw_logs = subprocess.check_output(['tail', '-n', '100', LOG_FILE]).decode('utf-8', errors='ignore')
    clean_logs = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', raw_logs)
    return jsonify({"logs": clean_logs})

@app.route('/stop', methods=['POST'])
def menu_4():
    kill_processes()
    clean_system()
    return jsonify({"msg": "Stopped"})

@app.route('/clean_ram', methods=['POST'])
def menu_7():
    clean_system()
    return jsonify({"msg": "Optimized"})

if __name__ == '__main__':
    threading.Thread(target=auto_register, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
