import os, hashlib, re, time, requests
from playwright.sync_api import sync_playwright
from datetime import datetime

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
    # Regex for XML or Base64 patterns typical of keyboxes
    xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html, re.S | re.I)
    if xml_match:
        return xml_match.group(0).strip()
    return None

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a high-end User Agent to avoid bot detection
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T scanning: {name}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Brute force scroll to load all messages in the web preview
                for _ in range(3):
                    page.mouse.wheel(0, 5000)
                    time.sleep(2)
                
                content = page.content()
                payload = extract_xml(content)
                
                if payload:
                    h = get_hash(payload)
                    is_new = True
                    # Check against all existing files in the archive
                    for f in os.listdir(SAVE_DIR):
                        if f.endswith('.xml'):
                            with open(os.path.join(SAVE_DIR, f), 'r') as old:
                                if get_hash(old.read()) == h:
                                    is_new = False
                                    break
                    
                    if is_new:
                        fname = f"key_{name}_{datetime.now().strftime('%m%d_%H%M')}.xml"
                        fpath = os.path.join(SAVE_DIR, fname)
                        with open(fpath, "w") as f:
                            f.write(payload)
                        
                        # Immediate Telegram Alert
                        files = {'document': open(fpath, 'rb')}
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                                      data={'chat_id': TG_CHAT_ID, 'caption': f"✅ NEW KEY: {name}"}, 
                                      files=files)
                        print(f"🌟 Found and sent new key from {name}")
                else:
                    print(f"ℹ️ No XML pattern found on {name} currently.")
            except Exception as e:
                print(f"❌ Error on {name}: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_hunt()
