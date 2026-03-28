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

def get_hash(content):
    """Creates a unique ID based on the XML data itself."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def extract_xml_from_zip(zip_url, text_context):
    """Downloads ZIP and attempts to unlock using discovered or common passwords."""
    try:
        passwords = [None, "yuri", "pif", "123", "yigit", "integrity", "1234"]
        # Look for password patterns in Yuri's captions
        found_pwd = re.search(r"(?:Pass|Password|PW|pass is):\s*([A-Za-z0-9@#$]+)", text_context, re.I)
        if found_pwd:
            passwords.insert(0, found_pwd.group(1).strip())

        r = requests.get(zip_url, timeout=20)
        if r.status_code != 200: return None, None

        for pwd in passwords:
            try:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    for name in z.namelist():
                        if name.lower().endswith('.xml'):
                            data = z.read(name, pwd=pwd.encode() if pwd else None)
                            return data.decode('utf-8', errors='ignore'), pwd
            except: continue 
    except: pass
    return None, None

def run_hunt():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    # Identify what we currently have in the repo
    current_files = os.listdir(SAVE_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T probing: {name}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(5) 
                
                body_text = page.inner_text("body")
                html_content = page.content()

                # --- ZIP Extraction ---
                zip_link = page.query_selector("a[href*='.zip']")
                if zip_link:
                    dl_url = zip_link.get_attribute("href")
                    if dl_url and not dl_url.startswith("http"): dl_url = "https://t.me" + dl_url
                    xml_data, used_pwd = extract_xml_from_zip(dl_url, body_text)
                    if xml_data:
                        check_sync_and_push(xml_data, f"{name}_ZIP", current_files, f"🔑 Pass: {used_pwd}")

                # --- Raw XML Extraction ---
                xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html_content, re.S | re.I)
                if xml_match:
                    check_sync_and_push(xml_match.group(0).strip(), name, current_files)
                
            except Exception as e:
                print(f"⚠️ {name} failed: {e}")
        browser.close()

def check_sync_and_push(payload, source_name, current_files, extra=""):
    h = get_hash(payload)
    # File is named by its first 12 characters of SHA256
    fname = f"key_{h[:12]}.xml"
    
    # If you deleted it, fname won't be in current_files, so it triggers a re-push
    if fname in current_files:
        print(f"⏭️ {fname} exists. Skipping.")
        return

    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "w", encoding='utf-8') as f:
        f.write(payload)
    
    # Telegram Alert
    caption = f"🛡️ Z E U S B O T : SYNCED\n👤 Source: {source_name}\n🆔 Hash: {h[:12]}\n{extra}"
    with open(fpath, 'rb') as doc:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                      data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})
    print(f"✅ Synced/Pushed: {fname}")

if __name__ == "__main__":
    run_hunt()
