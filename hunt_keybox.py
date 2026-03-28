import os, hashlib, re, time, zipfile, io, requests, base64
from playwright.sync_api import sync_playwright
from datetime import datetime

# 🎯 TARGETS MARCH 2026
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
    if isinstance(content, str): content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def extract_xml_from_zip(zip_url, text_context):
    try:
        # Common passwords + Scraped password
        passwords = [None, "yuri", "pif", "123", "yigit", "integrity"]
        # Look for any alphanumeric string after 'pass' or 'pw'
        found_pwd = re.search(r"(?:pass|pw|password|code)\D*(\w{3,15})", text_context, re.I)
        if found_pwd: passwords.insert(0, found_pwd.group(1).strip())

        print(f"📦 Attempting ZIP: {zip_url}")
        r = requests.get(zip_url, timeout=25)
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
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    # Physical check of what's in the repo right now
    current_files = os.listdir(SAVE_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T probing: {name}")
                # Increased timeout and wait for network to be completely idle
                page.goto(url, wait_until="networkidle", timeout=90000)
                time.sleep(10) # Heavy sleep for Cloudflare/Slow JS
                
                body_text = page.inner_text("body")
                html_content = page.content()

                # --- 1. ZIP HUNT ---
                # Telegram web preview often wraps links in 'tgme_widget_message_document_wrap'
                zip_links = page.query_selector_all("a[href*='.zip']")
                for link in zip_links:
                    dl_url = link.get_attribute("href")
                    if dl_url and not dl_url.startswith("http"): dl_url = "https://t.me" + dl_url
                    
                    xml_data, used_pwd = extract_xml_from_zip(dl_url, body_text)
                    if xml_data:
                        check_and_sync(xml_data, f"{name}_ZIP", current_files, f"🔑 Pass: {used_pwd}")

                # --- 2. RAW XML HUNT ---
                xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html_content, re.S | re.I)
                if xml_match:
                    check_and_sync(xml_match.group(0).strip(), name, current_files)
                
            except Exception as e:
                print(f"⚠️ {name} failed: {e}")
        browser.close()

def check_and_sync(payload, source_name, current_files, extra=""):
    h = get_hash(payload)
    fname = f"key_{h[:12]}.xml"
    
    if fname in current_files:
        print(f"⏭️ {fname} already exists.")
        return

    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "w", encoding='utf-8') as f: f.write(payload)
    
    # Telegram Alert
    caption = f"🛡️ Z E U S B O T : SYNCED\n👤 Source: {source_name}\n🆔 Hash: {h[:12]}\n{extra}"
    with open(fpath, 'rb') as doc:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                      data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})
    print(f"✅ Re-pushed/Saved: {fname}")

if __name__ == "__main__":
    run_hunt()
