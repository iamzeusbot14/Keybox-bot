import os
import requests
import hashlib
import re
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

def clean_xml_content(content):
    """Strips any text before the actual XML start tag to prevent parser errors."""
    # Find the start of the XML tag (<?xml or <whitebox)
    match = re.search(r'(<[\?]?xml|<whitebox)', content, re.IGNORECASE)
    if match:
        return content[match.start():].strip()
    return content.strip()

def get_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

def is_duplicate(new_hash):
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
    # SANITIZE CONTENT BEFORE SAVING
    clean_content = clean_xml_content(content)
    
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"keybox_{source}_{timestamp}.xml"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "w") as f:
        f.write(clean_content)
    
    status = "🟢 STRONG" if is_strong else "🟡 DEVICE"
    caption = (
        f"🚀 {status} KEYBOX ARCHIVED\n"
        f"👤 Source: {source}\n"
        f"📁 Saved as: {filename}\n"
        f"🤖 Identity: Z E U S B O T\n"
        f"✨ Auto-Cleaned: YES"
    )
    
    url_doc = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    
    with open(filepath, "rb") as xml_file:
        requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': xml_file})

def run_hunt():
    try:
        meow_status = requests.get(MEOW_README, timeout=10).text
        is_strong = "🟢🟢🟢" in meow_status
    except:
        is_strong = False

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200 and len(res.text) > 50:
                content = res.text
                # Hash the CLEANED version to ensure uniqueness of the actual XML
                cleaned = clean_xml_content(content)
                new_hash = get_hash(cleaned)
                
                if not is_duplicate(new_hash):
                    send_and_save(content, name, is_strong)
                    return True 
        except:
            continue
    return False

if __name__ == "__main__":
    run_hunt()
