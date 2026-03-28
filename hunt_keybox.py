import os
import requests
import hashlib
import base64
import re
from datetime import datetime

# SOURCES: Targeting Telegram Previews to bypass Web-Bot Protection
SOURCES = {
    "Yuri_TG": "https://t.me/s/yurikeybox",
    "tryigit_TG": "https://t.me/s/tr_pif",
    "Meow_TG": "https://t.me/s/MeowDump",
    "Pif_Next": "https://raw.githubusercontent.com/EricInacio01/PlayIntegrityFix-NEXT/main/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def extract_keybox(html_content):
    """Hunts for XML or Base64 blocks in HTML source."""
    # Try finding raw XML first
    xml_match = re.search(r'(<\?xml|<AndroidAttestation|<whitebox).*?(</AndroidAttestation>|</whitebox>)', html_content, re.DOTALL | re.IGNORECASE)
    if xml_match:
        return xml_match.group(0).strip()
    
    # Try finding Base64 blocks (common in Yuri's channel)
    b64_blocks = re.findall(r'[A-Za-z0-9+/]{100,}=*', html_content)
    for block in b64_blocks:
        try:
            decoded = base64.b64decode(block).decode('utf-8', errors='ignore')
            if '<AndroidAttestation' in decoded or '<whitebox' in decoded:
                start = decoded.find('<')
                return decoded[start:].strip()
        except:
            continue
    return None

def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def is_duplicate(new_hash):
    if not os.path.exists(SAVE_DIR): return False
    for f in os.listdir(SAVE_DIR):
        file_path = os.path.join(SAVE_DIR, f)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                if get_hash(file.read()) == new_hash: return True
    return False

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    
    found_any = False
    for name, url in SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code == 200:
                clean_xml = extract_keybox(res.text)
                
                if clean_xml and not is_duplicate(get_hash(clean_xml)):
                    ts = datetime.now().strftime("%Y%m%d_%H%M")
                    fname = f"keybox_{name}_{ts}.xml"
                    fpath = os.path.join(SAVE_DIR, fname)
                    
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(clean_xml)
                    
                    # Notify Telegram
                    caption = f"🛡️ BYPASS SUCCESS: {name}\n📁 Saved: {fname}\n🤖 Z E U S B O T"
                    with open(fpath, 'rb') as doc:
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                                      data={'chat_id': TG_CHAT_ID, 'caption': caption}, 
                                      files={'document': doc})
                    found_any = True
        except: continue
    return found_any

if __name__ == "__main__":
    run_hunt()
