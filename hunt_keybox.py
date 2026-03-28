import os
import requests
import hashlib

# Targets
SOURCES = {
    "Yuri": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/keybox.xml",
    "tryigit": "https://raw.githubusercontent.com/tryigit/PlayIntegrityFix/main/keybox.xml",
    "MeowDump": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_keybox_hash.txt"

def get_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

def send_to_tg(content, source):
    # 1. Save files locally to send
    with open("keybox.xml", "w") as f:
        f.write(content)
    
    # 2. Send the Notification & XML
    url_doc = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    caption = f"⚡ NEW KEYBOX DETECTED\n👤 Source: {source}\n🛠 Status: Ready for Violet/Poco"
    
    with open("keybox.xml", "rb") as xml_file:
        requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': xml_file})

    # 3. Send the YAML file (The current bot config)
    yaml_path = ".github/workflows/hunt.yml"
    if os.path.exists(yaml_path):
        with open(yaml_path, "rb") as yml_file:
            requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': "📄 Current Bot Config (YML)"}, files={'document': yml_file})

def run_hunt():
    if not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f: f.write("")

    with open(HASH_FILE, "r") as f:
        last_hash = f.read().strip()

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                current_hash = get_hash(res.text)
                if current_hash != last_hash:
                    send_to_tg(res.text, name)
                    with open(HASH_FILE, "w") as f:
                        f.write(current_hash)
                    return True
        except: pass
    return False

if __name__ == "__main__":
    run_hunt()
