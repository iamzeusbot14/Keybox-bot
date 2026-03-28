import os
import requests
import hashlib
import re

# Targets
SOURCES = {
    "Yuri": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/keybox.xml",
    "tryigit": "https://raw.githubusercontent.com/tryigit/PlayIntegrityFix/main/keybox.xml",
    "MeowDump": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/keybox.xml"
}
MEOW_README = "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/README.md"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_keybox_hash.txt"

def get_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

def send_to_tg(content, source, is_strong):
    with open("keybox.xml", "w") as f:
        f.write(content)
    
    status_icon = "🟢 STRONG" if is_strong else "🟡 DEVICE"
    caption = f"🚀 {status_icon} KEYBOX FOUND\n👤 Source: {source}\n⚡ Status: Verified"
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    with open("keybox.xml", "rb") as doc:
        requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})

def run_hunt():
    # 1. Check MeowDump README for global "Strong" status
    meow_readme = requests.get(MEOW_README).text
    global_strong = "🟢🟢🟢" in meow_readme

    # 2. Load the last hash we sent to avoid duplicates
    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                content = res.text
                current_hash = get_hash(content)

                if current_hash != last_hash:
                    print(f"New keybox detected from {name}!")
                    # Check CRL briefly (optional but recommended)
                    send_to_tg(content, name, global_strong)
                    
                    # Update the local hash so we don't send this again
                    with open(HASH_FILE, "w") as f:
                        f.write(current_hash)
                    return True 
        except Exception as e:
            print(f"Error checking {name}: {e}")
            
    return False

if __name__ == "__main__":
    run_hunt()
  
