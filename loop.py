from multiprocessing import Process, Manager
import os
import time
import sys
import json
# Import tetap sama
from modul_bot import worker, get_profiles_from_mapping, read_file_lines

# --- KONFIGURASI 12 JAM ---
# 12 Jam x 60 Menit x 60 Detik = 43200 Detik
# Bot akan jalan nonstop selama ini, baru kemudian direstart paksa.
MAX_BATCH_TIME = 43200 

def force_kill_chrome():
    # Perintah pembersih untuk Linux
    os.system("pkill chrome > /dev/null 2>&1")
    os.system("pkill chromedriver > /dev/null 2>&1")
    time.sleep(1)
    os.system("pkill -9 chrome > /dev/null 2>&1")
    os.system("pkill -9 chromedriver > /dev/null 2>&1")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- FUNGSI AUTO-HEAL (TETAP SAMA) ---
def fix_crash_restore_popup(profile_path):
    pref_file = os.path.join(profile_path, "Default", "Preferences")
    if not os.path.exists(pref_file): return
    try:
        with open(pref_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        changed = False
        if "profile" in data:
            if data["profile"].get("exit_type") != "Normal":
                data["profile"]["exit_type"] = "Normal"
                changed = True
            if data["profile"].get("exited_cleanly") is False:
                data["profile"]["exited_cleanly"] = True
                changed = True
        if changed:
            with open(pref_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
    except: pass
# ----------------------------------------

if __name__ == "__main__":
    MAPPING_FILE = "mapping_profil.txt"
    LINK_FILE = "link.txt"
    
    with Manager() as manager:
        status_dict = manager.dict()

        while True:
            force_kill_chrome()
            clear_screen()
            print(">>> MEMBERSIHKAN CHROME & MEMULAI SESI 12 JAM (NONSTOP)...")
            time.sleep(3) 

            if not os.path.exists(MAPPING_FILE) or not os.path.exists(LINK_FILE):
                print("⚠️ File data tidak ditemukan. Menunggu 30 detik...")
                time.sleep(30)
                continue

            user_profiles = get_profiles_from_mapping(MAPPING_FILE)
            all_links = read_file_lines(LINK_FILE)
            
            if not user_profiles or not all_links:
                print("⚠️ Data kosong. Menunggu 30 detik...")
                time.sleep(30)
                continue
            
            # Reset status
            for p in user_profiles:
                status_dict[p['name']] = "Waiting to start..."

            links_for_profiles = [[] for _ in user_profiles]
            for i, link in enumerate(all_links):
                links_for_profiles[i % len(user_profiles)].append(link)
            
            processes = []

            for i, profile in enumerate(user_profiles):
                # Obati profil dulu
                fix_crash_restore_popup(profile['user_data_dir'])
                
                p = Process(target=worker, args=(
                    profile['name'],
                    profile['user_data_dir'],
                    profile['profile_dir'],
                    profile['window_position'],
                    links_for_profiles[i],
                    status_dict 
                ))
                p.start()
                processes.append(p)
                time.sleep(1) 

            # --- MONITORING DASHBOARD ---
            start_wait = time.time()
            
            while True:
                clear_screen()
                elapsed = int(time.time() - start_wait)
                
                # Hitung sisa waktu untuk display
                sisa = MAX_BATCH_TIME - elapsed
                jam_sisa = sisa // 3600
                menit_sisa = (sisa % 3600) // 60
                
                print(f"=== MONITORING BOT 12 JAM (Time: {elapsed}s) ===")
                print(f"⏳ Refresh Otomatis dalam: {jam_sisa} Jam {menit_sisa} Menit\n")
                
                sorted_names = sorted([p['name'] for p in user_profiles])
                for name in sorted_names:
                    current_status = status_dict.get(name, "Unknown")
                    print(f"👤 {name.ljust(15)} : {current_status}")

                print("\n-------------------------------------------------")

                # Cek apakah process mati sendiri (sangat jarang terjadi karena mode nonstop)
                still_alive = any(p.is_alive() for p in processes)
                if not still_alive:
                    print("\n>>> Semua worker berhenti (Unexpected). Restarting...")
                    break
                
                # Jika sudah 12 Jam, matikan paksa
                if elapsed > MAX_BATCH_TIME:
                    print(f"\n⏰ WAKTU 12 JAM HABIS. MEREFRESH SYSTEM !!!")
                    for p in processes:
                        if p.is_alive():
                            p.terminate()
                    break
                
                time.sleep(2)

            print(">>> Sesi selesai. Restarting...\n")
            time.sleep(2)