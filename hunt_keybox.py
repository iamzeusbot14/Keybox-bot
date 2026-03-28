import os, requests, hashlib, base64, re, time
from datetime import datetime

# UPDATED SOURCES MARCH 2026
SOURCES = {
    "Yuri_TG": "https://t.me/s/yurikeybox",
    "tryigit_TG": "https://t.me/s/tr_pif",
    "Pif_Next": "https://raw.githubusercontent.com/EricInacio01/PlayIntegrityFix-NEXT/main/keybox.xml",
    "Meow_Files": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/files/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def extract_payload(content):
    """Aggressive extraction: XML -> Base64 -> Raw Hex blocks."""
    # Try standard XML
    xml_match = re.search(r'(<\?xml|<AndroidAttestation|<whitebox).*?(</AndroidAttestation>|</whitebox>)', content, re.DOTALL | re.IGNORECASE)
    if xml_match: return xml_match.group(0).strip()
    
    # Try Base64 blocks (Common in Yuri's posts)
    b64_blocks = re.findall(r'[A-Za-z0-9+/]{200,}=*', content)
    for block in b64_blocks:
        try:
            decoded = base64.b64decode(block).decode('utf-8', errors='ignore')
            if '<AndroidAttestation' in decoded or '<whitebox' in decoded:
                start = decoded.find('<')
                return decoded[start:].strip()
        except: continue
    return None

def run_hunt():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    # Create .gitkeep so the folder is never 'empty' to Git
    with open(os.path.join(SAVE_DIR, ".gitkeep"), "w") as f: f.write("zeus")

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    
    for name, url in SOURCES.items():
        try:
            print(f"📡 Probing {name}...")
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200:
                print(f"❌ {name} returned {res.status_code}")
                continue

            payload = extract_payload(res.text)
            if payload:
                h = hashlib.sha256(payload.encode()).hexdigest()
                
                # Check for duplicates in local folder
                is_new = True
                for existing in os.listdir(SAVE_DIR):
                    if existing.endswith(".xml"):
                        with open(os.path.join(SAVE_DIR, existing), "r") as ef:
                            if hashlib.sha256(ef.read().encode()).hexdigest() == h:
                                is_new = False; break
                
                if is_new:
                    fname = f"key_{name}_{datetime.now().strftime('%m%d_%H%M')}.xml"
                    fpath = os.path.join(SAVE_DIR, fname)
                    with open(fpath, "w") as f: f.write(payload)
                    
                    # Send to Telegram
                    caption = f"🚀 Z E U S B O T : NEW KEY\n👤 Source: {name}\n📁 File: {fname}"
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                                  data={'chat_id': TG_CHAT_ID, 'caption': caption}, 
                                  files={'document': open(fpath, 'rb')})
                    print(f"✅ Saved and Sent: {fname}")
            else:
                print(f"⚠️ {name}: No keybox pattern found in response.")
        except Exception as e:
            print(f"❌ {name} Error: {e}")

if __name__ == "__main__":
    run_hunt()
