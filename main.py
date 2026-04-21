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
SCREEN_LOGIN = "1280x720x24"
SCREEN_LOOP = "500x500x24"

# ==========================================
# 🖥️ INTERNAL WEB PANEL (HTML TEMPLATE)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GHOST COMMANDER - Panel dotaja</title>
    <style>
        body { background-color: #0d1117; color: #00ff00; font-family: monospace; padding: 20px; font-size: 14px; margin: 0; }
        h2 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-top: 0; }
        .container { max-width: 900px; margin: auto; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        button { background: #238636; color: #ffffff; border: 1px solid rgba(240,246,252,0.1); padding: 8px 12px; cursor: pointer; border-radius: 4px; font-family: monospace; font-weight: bold; transition: 0.2s; }
        button:hover { background: #2ea043; }
        button.danger { background: #da3633; }
        button.danger:hover { background: #f85149; }
        button.warning { background: #d29922; }
        input[type="text"] { width: 70%; background: #010409; color: #c9d1d9; border: 1px solid #30363d; padding: 7px; border-radius: 4px; font-family: monospace; }
        pre { background: #010409; padding: 10px; border: 1px solid #30363d; border-radius: 4px; height: 300px; overflow-y: auto; white-space: pre-wrap; font-size: 12px; }
        .status-badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status-on { background: #238636; color: white; }
        .status-off { background: #da3633; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h2>💀 GHOST COMMANDER - dotaja Panel</h2>
        
        <div class="card grid">
            <div>
                <strong>Status System:</strong><br><br>
                RAM Free: <span id="ram_free">Menghitung...</span><br>
                Login Script: <span id="status_login" class="status-badge status-off">OFF</span><br>
                Loop Script: <span id="status_loop" class="status-badge status-off">OFF</span>
            </div>
            <div>
                <strong>Kontrol Utama:</strong><br><br>
                <button onclick="apiCall('/start/login', 'POST')">Start Login</button>
                <button onclick="apiCall('/start/loop', 'POST')">Start Loop</button><br><br>
                <button class="danger" onclick="apiCall('/stop', 'POST')">Stop Semua</button>
                <button class="warning" onclick="apiCall('/clean_ram', 'POST')">Clean RAM</button>
            </div>
        </div>

        <div class="card grid">
            <div>
                <strong>Manajemen File:</strong><br><br>
                <input type="text" id="email_input" placeholder="Masukkan baris email...">
                <button onclick="addFile('email.txt', 'email_input')">Add Email</button><br><br>
                <input type="text" id="link_input" placeholder="Masukkan baris link...">
                <button onclick="addFile('link.txt', 'link_input')">Add Link</button><br><br>
                <button class="danger" onclick="apiCall('/file/email.txt', 'DELETE')">Clear Email</button>
                <button class="danger" onclick="apiCall('/file/link.txt', 'DELETE')">Clear Link</button>
            </div>
            <div>
                <strong>Manajemen Profil:</strong><br><br>
                <button class="danger" onclick="deleteProfile('all')">Hapus Semua Profil</button><br><br>
                <small>Menghapus Chrome profiles dan mapping_profil.txt</small>
            </div>
        </div>

        <div class="card">
            <strong>Log Terminal:</strong>
            <pre id="log_viewer">Memuat log...</pre>
        </div>
    </div>

    <script>
        const AUTH_KEY = "GHOST_SECRET_2026";
        const headers = { "X-Auth-Key": AUTH_KEY, "Content-Type": "application/json" };

        async function apiCall(endpoint, method = 'GET', body = null) {
            try {
                const options = { method, headers };
                if (body) options.body = JSON.stringify(body);
                const res = await fetch(endpoint, options);
                const data = await res.json();
                if (data.msg) alert(data.msg);
                updateStatus();
            } catch (err) {
                console.error(err);
            }
        }

        async function addFile(filename, inputId) {
            const content = document.getElementById(inputId).value;
            if (!content) return;
            await apiCall(`/file/${filename}`, 'POST', { content });
            document.getElementById(inputId).value = '';
        }

        async function deleteProfile(target) {
            if (confirm(`Yakin hapus profil: ${target}?`)) {
                await apiCall('/profiles', 'DELETE', { target });
            }
        }

        async function updateStatus() {
            try {
                const res = await fetch('/status', { headers });
                const data = await res.json();
                document.getElementById('ram_free').innerText = data.ram_free;
                
                const loginBadge = document.getElementById('status_login');
                loginBadge.className = data.login ? 'status-badge status-on' : 'status-badge status-off';
                loginBadge.innerText = data.login ? 'ON' : 'OFF';

                const loopBadge = document.getElementById('status_loop');
                loopBadge.className = data.loop ? 'status-badge status-on' : 'status-badge status-off';
                loopBadge.innerText = data.loop ? 'ON' : 'OFF';
            } catch (err) {}
        }

        async function fetchLogs() {
            try {
                const res = await fetch('/logs', { headers });
                const data = await res.json();
                const logViewer = document.getElementById('log_viewer');
                
                // Hanya scroll ke bawah jika user sedang berada di bawah
                const isScrolledToBottom = logViewer.scrollHeight - logViewer.clientHeight <= logViewer.scrollTop + 1;
                logViewer.innerText = data.logs || 'Belum ada log...';
                if (isScrolledToBottom) logViewer.scrollTop = logViewer.scrollHeight;
            } catch (err) {}
        }

        // Auto Refresh
        setInterval(updateStatus, 3000);
        setInterval(fetchLogs, 3000);
        updateStatus();
        fetchLogs();
    </script>
</body>
</html>
"""

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
    os.system(f"pkill -f {FILE_LOGIN}")
    os.system(f"pkill -f {FILE_LOOP}")
    os.system("pkill -f chrome")
    os.system("pkill -f chromedriver")
    os.system("pkill -f Xvfb")

def clean_system():
    os.system("ps -ef | awk '/defunct/ && !/awk/ {print $3}' | xargs -r kill -9")
    os.system("sync; echo 3 > /proc/sys/vm/drop_caches")

def auto_register():
    max_retries = 3  # Hanya mencoba 3 kali (Aman untuk limit dotaja)
    delay_retry = 3  
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Melapor ke Panel External (Percobaan {attempt}/{max_retries})...")
            my_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
            
            success_count = 0
            for url in PANEL_URL:
                resp = requests.post(
                    f"{url}/api/register", 
                    json={"ip": my_ip, "auth": AUTH_KEY}, 
                    timeout=10
                )
                if resp.status_code >= 400:
                    print(f"⚠️ Gagal lapor ke {url} | Status: {resp.status_code}")
                    resp.raise_for_status()
                else:
                    success_count += 1

            if success_count > 0:
                print("✅ Berhasil terhubung ke Panel External.")
                return 

        except Exception as e:
            print(f"⚠️ Terjadi kesalahan: {e}")
            if attempt < max_retries:
                print(f"⏳ Mencoba ulang dalam {delay_retry} detik...")
                time.sleep(delay_retry)
            else:
                print("❌ Gagal total setelah 3x percobaan. Berhenti agar dotaja aman.")
                return

# --- API ENDPOINTS ---

@app.before_request
def auth():
    # Bypass otentikasi HANYA untuk merender halaman UI Panel di route '/'
    if request.path == '/':
        return
    # Sisa endpoint API tetap terkunci
    if request.headers.get("X-Auth-Key") != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

# Endpoint Panel UI
@app.route('/', methods=['GET'])
def index():
    return HTML_TEMPLATE

@app.route('/start/login', methods=['POST'])
def menu_1():
    if check_process(FILE_LOGIN):
        return jsonify({"msg": "⚠️ Login sudah berjalan"})
    
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
            return jsonify({"msg": f"Data Added to {filename}"})
    if request.method == 'DELETE':
        open(filename, 'w').close()
        return jsonify({"msg": f"{filename} Cleared"})
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
