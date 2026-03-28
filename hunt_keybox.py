import os, hashlib, re, time, zipfile, io, requests
from playwright.sync_api import sync_playwright
from datetime import datetime

# 🎯 2026 TARGETS
SOURCES = {
    "Yuri_Root": "https://t.me/s/yuriiroot",
    "Yuri_Archives": "https://t.me/s/yurikeybox",
    "tryigit_Web": "https://tryigit.dev/keybox/", 
    "Meow_Dump": "https://t.me/s/MeowDump"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_hash(content):
    if isinstance(content, str): content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def extract_xml_from_zip(zip_url, page_text):
    """
    Specifically tuned for Yuri's '🛡Password: Yurikey_v45' format.
    Downloads the ZIP and extracts the clean XML.
    """
    try:
        # 1. Targeted Password Scraping
        passwords = [None, "yuri", "pif"]
        
        # Regex tuned for Yuri's specific emoji and password string
        # Looks for the word immediately following '🛡Password:' or 'Password:'
        match = re.search(r"(?:🛡Password|Password|Pass|PW)\s*[:=-]*\s*([A-Za-z0-9_]{3,25})", page_text, re.I)
        if match:
            pwd_found = match.group(1).strip()
            passwords.insert(0, pwd_found)
            print(f"🔑 Scraped Yuri Password: {pwd_found}")

        print(f"📦 Downloading Yuri ZIP: {zip_url}")
        r = requests.get(zip_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: return None, None

        # 2. Extract only the XML from the encrypted ZIP
        for pwd in passwords:
            try:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    for name in z.namelist():
                        if name.lower().endswith('.xml'):
                            data = z.read(name, pwd=pwd.encode() if pwd else None)
                            return data.decode('utf-8', errors='ignore'), pwd
            except (zipfile.BadZipFile, RuntimeError):
                continue 
    except Exception as e:
        print(f"❌ ZIP Extraction Error: {e}")
    return None, None

def run_hunt():
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    current_files = os.listdir(SAVE_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T probing: {name}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(10) 

                # Strip Telegram login popups
                page.evaluate("document.querySelectorAll('.login_modal, #telegram-login, .overlay').forEach(el => el.remove())")

                html_content = page.content()
                body_text = page.inner_text("body")

                # --- Yuri's ZIP links ---
                zip_links = page.query_selector_all("a[href*='.zip']")
                for link in zip_links:
                    dl_url = link.get_attribute("href")
                    if dl_url and not dl_url.startswith("http"):
                        dl_url = "https://t.me" + dl_url
                    
                    xml_data, used_pwd = extract_xml_from_zip(dl_url, body_text)
                    if xml_data:
                        check_and_sync(xml_data, f"{name}_EXTRACTED", current_files, f"🔑 ZIP Pass: {used_pwd}")

                # --- Fallback for Raw XML ---
                xml_match = re.search(r'(<\?xml|<AndroidAttestation).*?(</AndroidAttestation>)', html_content, re.S | re.I)
                if xml_match:
                    check_and_sync(xml_match.group(0).strip(), name, current_files)
                
            except Exception as e:
                print(f"⚠️ {name} failed: {e}")
        browser.close()

def check_and_sync(payload, source_name, current_files, extra=""):
    h = get_hash(payload)
    fname = f"key_{h[:12]}.xml"
    
    # Check if the file already exists in the folder
    if fname in current_files:
        print(f"⏭️ {fname} already synced.")
        return

    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "w", encoding='utf-8') as f:
        f.write(payload)
    
    # Notify Z E U S via Telegram
    if TG_TOKEN and TG_CHAT_ID:
        caption = f"🛡️ Z E U S B O T : NEW KEY EXTRACTED\n👤 Source: {source_name}\n🆔 ID: {h[:12]}\n{extra}"
        with open(fpath, 'rb') as doc:
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                          data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})
    print(f"✅ Success: {fname}")

if __name__ == "__main__":
    run_hunt()
