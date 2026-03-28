import os, requests, hashlib, base64, re, time
from datetime import datetime

# 🎯 2026 OMNI-SOURCES: Web, GitHub, and Telegram Previews
SOURCES = {
    "Yuri_Archives": "https://t.me/s/yuriiarchives",   # Yuri's public mirror
    "Yuri_Raw": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/key",
    "tryigit_Hub": "https://tryigit.dev/keybox/",     # Web Hub
    "Pif_Next": "https://raw.githubusercontent.com/EricInacio01/PlayIntegrityFix-NEXT/main/keybox.xml",
    "Meow_Files": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/files/keybox.xml",
    "TrickyStore": "https://raw.githubusercontent.com/5ec1cff/TrickyStore/main/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def extract_payload(content):
    """Deep search for XML or Base64 across all formats."""
    # 1. Direct XML Match
    xml_pattern = r'(<\?xml|<AndroidAttestation|<whitebox).*?(</AndroidAttestation>|</whitebox>)'
    xml_match = re.search(xml_pattern, content, re.DOTALL | re.IGNORECASE)
    if xml_match: return xml_match.group(0).strip()
    
    # 2. Base64 Block Hunt (For encoded Telegram/Web messages)
    b64_blocks = re.findall(r'[A-Za-z0-9+/]{200,}=*', content)
    for block in b64_blocks:
        try:
            decoded = base64.b64decode(block).decode('utf-8', errors='ignore')
            if '<AndroidAttestation' in decoded:
                start = decoded.find('<')
                return decoded[start:].strip()
        except: continue
    return None

def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def is_duplicate(new_hash):
    if not os.path.exists(SAVE_DIR): return False
    for f in os.listdir(SAVE_DIR):
        path = os.path.join(SAVE_DIR, f)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as file:
                if get_hash(file.read()) == new_hash: return True
    return False

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    # Stealth Headers to bypass simple bot filters
    session = requests.Session()
