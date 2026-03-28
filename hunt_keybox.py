import os
import requests
import hashlib
from datetime import datetime

# UPDATED SOURCES
SOURCES = {
    "Yuri": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/key",
    "tryigit": "https://raw.githubusercontent.com/tryigit/PlayIntegrityFix/main/keybox.xml",
    "MeowDump": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/keybox.xml"
}
MEOW_README = "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/README.md"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_hash(content):
    """Generates a unique SHA-256 fingerprint for the keybox content."""
    return hashlib.sha256(content.encode()).hexdigest()

def is_duplicate(new_hash):
    """Scans the entire archive folder to see if this key already exists."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        return False
    
    for filename in os.listdir(SAVE_DIR):
        file_path = os.path.join(SAVE_DIR, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r") as f:
                if get_hash(f.read()) == new_hash:
                    return True
    return False

def send_and_save(content, source, is_strong):
    """Saves the unique keybox to a new file and pings Telegram."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # Create unique filename: keybox_Source_YYYYMMDD_HHMM.xml
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"keybox_{source}_{timestamp}.xml"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "w") as f:
        f.write(content)
    
    # Telegram Notification
    status = "🟢 STRONG" if is_strong else "🟡 DEVICE"
    caption = (
        f"🚀 {status} KEYBOX ARCHIVED\n"
        f"👤 Source: {source}\n"
        f"📁 Saved as: {filename}\n"
        f"🤖 Identity: Z E U S B O T"
    )
    
    url_doc = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    
    # Send the XML Keybox
    with open(filepath, "rb") as xml_file:
        requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': xml_file})

    # Send the YML Config as requested
    yaml_path = ".github/workflows/hunt.yml"
    if os.path.exists(yaml_path):
        with open(yaml_path, "rb") as yml_file:
            requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': "📄 Current Bot Config (YML)"}, files={'document': yml_file})

def run_hunt():
    # Check for Strong Integrity status from MeowDump
    try:
        meow_status = requests.get(MEOW_README, timeout=10).text
        is_strong = "🟢🟢🟢" in meow_status
    except:
        is_strong = False

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200 and len(res.text) > 100:
                content = res.text
                new_hash = get_hash(content)
                
                if not is_duplicate(new_hash):
                    print(f"New unique keybox found from {name}!")
                    send_and_save(content, name, is_strong)
                    return True # Found one, stop until next hour
        except Exception as e:
            print(f"Error checking {name}: {e}")
            continue
    return False

if __name__ == "__main__":
    run_hunt()
