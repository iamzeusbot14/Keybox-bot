import os, requests, hashlib, base64, re, time
from datetime import datetime

SOURCES = {
    "Yuri_TG": "https://t.me/s/yurikeybox",
    "tryigit_TG": "https://t.me/s/tr_pif",
    "Meow_TG": "https://t.me/s/MeowDump",
    "Pif_Next": "https://raw.githubusercontent.com/EricInacio01/PlayIntegrityFix-NEXT/main/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def extract_payload(content):
    xml_pattern = r'(<\?xml|<AndroidAttestation|<whitebox).*?(</AndroidAttestation>|</whitebox>)'
    xml_match = re.search(xml_pattern, content, re.DOTALL | re.IGNORECASE)
    if xml_match: return xml_match.group(0).strip()
    
    b64_blocks = re.findall(r'[A-Za-z0-9+/]{200,}=*', content)
    for block in b64_blocks:
        try:
            decoded = base64.b64decode(block).decode('utf-8', errors='ignore')
            if '<AndroidAttestation' in decoded:
                return decoded[decoded.find('<'):].strip()
        except: continue
    return None

def run_hunt():
    # Ensure directory exists immediately
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        open(f"{SAVE_DIR}/.gitkeep", 'a').close() # Keeps folder visible to Git

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    
    for name, url in SOURCES.items():
        try:
            print(f"📡 Probing {name}...")
            res = requests.get(url, headers=headers, timeout=25)
            
            if res.status_code != 200:
                print(f"❌ {name} failed with Status {res.status_code}")
                continue

            payload = extract_payload(res.text)
            if not payload:
                print(f"⚠️ {name} returned content, but no XML found.")
                continue

            # Unique Check logic
            h = hashlib.sha256(payload.encode()).hexdigest()
            duplicate = False
            for f in os.listdir(SAVE_DIR):
                if f.endswith('.xml'):
                    with open(os.path.join(SAVE_DIR, f), 'r') as old:
                        if hashlib.sha256(old.read().encode()).hexdigest() == h:
                            duplicate = True; break
            
            if not duplicate:
                fname = f"keybox_{name}_{datetime.now().strftime('%m%d_%H%M')}.xml"
                with open(os.path.join(SAVE_DIR, fname), "w") as f: f.write(payload)
                print(f"✅ Found NEW keybox from {name}!")
                
                # Send to Telegram
                requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                              data={'chat_id': TG_CHAT_ID, 'caption': f"🚀 NEW: {name}"}, 
                              files={'document': open(os.path.join(SAVE_DIR, fname), 'rb')})
        except Exception as e:
            print(f"❌ Error with {name}: {e}")

if __name__ == "__main__":
    run_hunt()
