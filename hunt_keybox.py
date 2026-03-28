import os, hashlib, re, time, zipfile, io, requests, base64
from playwright.sync_api import sync_playwright
from datetime import datetime

# 🎯 2026 TARGET ARCHIVE
SOURCES = {
    "Yuri_TG": "https://t.me/s/yurikeybox",
    "tryigit_Web": "https://tryigit.dev/keybox/", 
    "Meow_TG": "https://t.me/s/MeowDump",
    "Pif_Next": "https://raw.githubusercontent.com/EricInacio01/PlayIntegrityFix-NEXT/main/keybox.xml"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def extract_xml_from_zip(zip_url, text_context):
    """Downloads ZIP and attempts to unlock using discovered or common passwords."""
    try:
        # 1. Password List: Common fallbacks + Scraped password
        passwords = [None, "yuri", "pif", "123", "yigit", "integrity", "1234"]
        
        # 2. Regex to find password in the message text (e.g., 'Pass: 1234')
        found_pwd = re.search(r"(?:Pass|Password|PW|pass is):\s*([A-Za-z0-9@#$]+)", text_context, re.I)
        if found_pwd:
            passwords.insert(0, found_pwd.group(1).strip())

        response = requests.get(zip_url, timeout=20)
        if response.status_code != 200: return None, None

        # 3. Attempt to unzip with each password
        for pwd in passwords:
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    for name in z.namelist():
                        if name.lower().endswith('.xml'):
                            data = z.read(name, pwd=pwd.encode() if pwd else None)
                            return data.decode('utf-8', errors='ignore'), pwd
            except:
                continue 
    except Exception as e:
        print(f"❌ ZIP Error: {e}")
    return None, None

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    # Ensure folder visibility for Git
    with open(os.path.join(SAVE_DIR, ".gitkeep"), "w") as f: f.write("Z E U S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mimic a real Linux developer browser
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T probing: {name}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5) # Wait for Cloudflare/JS
                
                body_text = page.inner_text("body")
                html_content = page.content()

                # --- VECTOR 1: ZIP EXTRACTION (Yuri/Telegram) ---
                zip_links = page.query_selector_all("a[href*='.zip']")
                found_new = False
                for link in zip_links:
                    dl_url = link.get_attribute("href")
                    if dl_url and not dl_url.startswith("http"):
                        dl_url = "https://t.me" + dl_url
                    
                    xml_data, used_pwd = extract_xml_from_zip(dl_url, body_text)
                    if xml_data:
                        save_and_notify(xml_data, f"{name}_ZIP", f"🔑 ZIP Pass: {used_pwd}")
                        found_new = True; break

                if found_new: continue

                # --- VECTOR 2: RAW XML HUNT (Yigit/Web/GitHub) ---
                xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html_content, re.S | re.I)
                if xml_match:
                    save_and_notify(xml_match.group(0).strip(), name)
                
            except Exception as e:
                print(f"⚠️ {name} failed: {e}")
        browser.close()

def save_and_notify(payload, source_name, extra=""):
    h = get_hash(payload)
    if any(get_hash(open(os.path.join(SAVE_DIR, f), 'r').read()) == h 
           for f in os.listdir(SAVE_DIR) if f.endswith('.xml')):
        return # Duplicate found

    fname = f"key_{source_name}_{datetime.now().strftime('%m%d_%H%M')}.xml"
    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "w") as f: f.write(payload)
    
    caption = f"🛡️ Z E U S B O T : NEW KEY\n👤 Source: {source_name}\n{extra}"
    with open(fpath, 'rb') as doc:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                      data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})
    print(f"✅ Archived: {fname}")

if __name__ == "__main__":
    run_hunt()
