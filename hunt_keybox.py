import os
import requests
import hashlib
import re
from datetime import datetime

# OFFICIAL SOURCE MAPPING
SOURCES = {
    "Yuri": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/key",
    "tryigit": "https://raw.githubusercontent.com/tryigit/PlayIntegrityFix/main/keybox.xml",
    "MeowDump": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/keybox.xml"
}
MEOW_README = "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/README.md"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_clean_xml(raw_content):
    """
    Finds the first valid XML start tag and strips everything before it.
    Ensures @KeyBox_Checker_by_VD_Priv8_bot never sees 'Start tag expected' error.
    """
    try:
        # Look for standard keybox start tags
        match = re.search(r'(<\?xml|<AndroidAttestation|<whitebox)', raw_content, re.IGNORECASE)
        if match:
            return raw_content[match.start():].strip()
        return None
    except:
        return None

def get_hash(content):
    """Generates a unique fingerprint for the XML content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def is_duplicate(new_hash):
    """Scans the entire archive folder to prevent sending the same key twice."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        return False
    
    for filename in os.listdir(SAVE_DIR):
        file_path = os.path.join(SAVE_DIR, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                if get_hash(f.read()) == new_hash:
                    return True
    return False

def send_to_tg(filepath, caption):
    """Helper to send the document via Telegram API."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    with open(filepath, "rb") as doc:
        requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})

def run_hunt():
    # Check for Strong Integrity status from MeowDump README
    try:
        meow_status = requests.get(MEOW_README, timeout=10).text
        is_strong = "🟢🟢🟢" in meow_status
    except:
        is_strong = False

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                # 1. Clean the raw data to get valid XML
                clean_content = get_clean_xml(res.text)
                
                if clean_content and len(clean_content) > 100:
                    new_hash = get_hash(clean_content)
                    
                    # 2. Check if we already have this specific key archived
                    if not is_duplicate(new_hash):
                        # 3. Create unique filename with timestamp
                        ts = datetime.now().strftime("%Y%m%d_%H%M")
                        filename = f"keybox_{name}_{ts}.xml"
                        filepath = os.path.join(SAVE_DIR, filename)
                        
                        # 4. Save to Archive
                        with open(filepath, "w", encoding='utf-8') as f:
                            f.write(clean_content)
                        
                        # 5. Send to Telegram
                        status = "🟢 STRONG" if is_strong else "🟡 DEVICE"
                        caption = (
                            f"🚀 {status} KEYBOX ARCHIVED\n"
                            f"👤 Source: {name}\n"
                            f"📁 File: {filename}\n"
                            f"🤖 Identity: Z E U S B O T\n"
                            f"✨ Sanitized: YES"
                        )
                        send_to_tg(filepath, caption)
                        
                        # Also send the YML config as requested
                        yml_path = ".github/workflows/hunt.yml"
                        if os.path.exists(yml_path):
                            send_to_tg(yml_path, "📄 Current Bot Config (YML)")
                            
                        return True # Found a new one, exit until next hour
        except Exception as e:
            print(f"Error checking {name}: {e}")
            continue
    return False

if __name__ == "__main__":
    run_hunt()
