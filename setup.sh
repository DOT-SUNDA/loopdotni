#!/bin/bash
# =======================================================
# CLEANUP & DETEKSI OS (UNIVERSAL)
# =======================================================
mkdir -p /root/botdot

echo "🔍 Mendeteksi Versi Ubuntu..."
source /etc/os-release
echo "👉 Terdeteksi: Ubuntu $VERSION_ID"

echo "🔧 INSTALL SYSTEM DEPENDENCIES..."
rm -f /etc/apt/sources.list.d/google-chrome.list
apt-get update -y

# --- LOGIKA INSTALL OTOMATIS BERDASARKAN VERSI ---
if [[ "$VERSION_ID" == "24.04" ]]; then
    echo "📦 Mode: Ubuntu 24.04 (Modern Packages)"
    # Install paket khusus Ubuntu 24 (t64)
    apt-get install -y xvfb xauth libxi6 libgbm1 libnss3 unzip curl gnupg python3 python3-pip \
    libgtk-3-0t64 libasound2t64 libatk-bridge2.0-0t64
else
    echo "📦 Mode: Ubuntu 20.04/22.04 (Legacy Packages)"
    # Install paket standar lama
    apt-get install -y xvfb xauth libxi6 libgbm1 libnss3 unzip curl gnupg python3 python3-pip \
    libgtk-3-0 libasound2 libatk-bridge2.0-0 libgconf-2-4
fi

# Install Library Python
pip3 uninstall -y selenium requests urllib3 webdriver-manager pyvirtualdisplay 2>/dev/null
pip3 install selenium==4.11.2 requests==2.31.0 urllib3==2.0.7 flask psutil pyautogui colorama Pillow \
    --break-system-packages --ignore-installed --root-user-action=ignore --force-reinstall

# Install Chrome 109
if ! google-chrome --version | grep -q "109"; then
    echo "⬇️ Download Chrome 109..."
    apt-get remove -y google-chrome-stable || true
    wget -q -O /tmp/chrome109.deb "https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_109.0.5414.74-1_amd64.deb"
    dpkg -i /tmp/chrome109.deb
    apt-get install -f -y
    rm /tmp/chrome109.deb
fi

# =======================================================
# PYTHON SCRIPT (FORMAT SESUAI REQUEST)
# =======================================================
wget -O /root/bot/main.py
wget -O /root/bot/login.py
wget -O /root/bot/loop.py

# =======================================================
# SYSTEMD SERVICE (Auto Start)
# =======================================================
echo "🛡️ Mengatur Systemd..."

cat <<EOF > /etc/systemd/system/botdot.service
[Unit]
Description=CloudSigma Bot
After=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cloudsigma_bot
ExecStart=/usr/bin/python3 /root/bot/main.py
Restart=on-failure
RestartSec=10s
StartLimitBurst=3
StartLimitInterval=120

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /etc/systemd/system/cloudsigma_bot.service
systemctl daemon-reload
systemctl enable cloudsigma_bot.service

echo "✅ SELESAI! Script universal siap dijalankan."
echo "👉 ketik: reboot"
