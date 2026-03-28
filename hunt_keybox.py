import os, hashlib, re, time
from playwright.sync_api import sync_playwright
from datetime import datetime
import requests

SOURCES = {
    "Yuri_TG": "https://t.me/s/yurikeybox",
    "tryigit_TG": "https://t.me/s/tr_pif",
    "Meow_TG": "https://t.me/s/MeowDump"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def extract_xml(html):
    # Hunt for XML tags or Base64 patterns in the browser's rendered HTML
    xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html, re.S | re.I)
    if xml_match:
        return xml_match.group(0).strip()
    return None

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    with sync_playwright() as p:
        # Launch a headless browser (like your Chrome on Arch)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"🌐 Z E U S B O T opening browser for: {name}")
                page.goto(url, wait_until="networkidle")
                # Scroll down to trigger any lazy-loaded messages
                page.mouse.wheel(0, 5000)
                time.sleep(3) 
                
                content = page.content()
                payload = extract_xml(content)
                
                if payload:
                    h = get_hash(payload)
                    is_new = True
                    for f in os.listdir(SAVE_DIR):
                        if f.endswith('.xml'):
                            with open(os.path.join(SAVE_DIR, f), 'r') as old:
                                if get_hash(old.read()) == h: is_new = False; break
                    
                    if is_new:
                        fname = f"key_{name}_{datetime.now().strftime('%m%d_%H%M')}.xml"
                        fpath = os.path.join(SAVE_DIR, fname)
                        with open(fpath, "w") as f: f.write(payload)
                        
                        # Send to Telegram
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                                      data={'chat_id': TG_CHAT_ID, 'caption': f"🚀 BROWSER FETCH: {name}"}, 
                                      files={'document': open(fpath, 'rb')})
            except Exception as e:
                print(f"❌ Error with {name}: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_hunt()
