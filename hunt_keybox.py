import os, hashlib, re, time, zipfile, io, requests, base64
from playwright.sync_api import sync_playwright
from datetime import datetime

# 🎯 2026 OMNI-TARGETS (Bypassing Login Walls)
SOURCES = {
    "Yuri_Root": "https://t.me/s/yuriiroot",
    "Yuri_Archives": "https://t.me/s/yurikeybox",
    "tryigit_JSON": "https://tryigit.dev/keybox/pif.json", # Direct Data Bypass
    "tryigit_Web": "https://tryigit.dev/keybox/", 
    "Meow_Dump": "https://t.me/s/MeowDump"
}

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def get_hash(content):
    if isinstance(content, str): content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def extract_xml_from_zip(zip_url, text_context):
    try:
        passwords = [None, "yuri", "pif", "123", "yigit", "integrity"]
        found_pwd = re.search(r"(?:pass|pw|password|code)\D*(\w{3,15})", text_context, re.I)
        if found_pwd: passwords.insert(0, found_pwd.group(1).strip())

        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
        r = requests.get(zip_url, headers=headers, timeout=25)
        
        if r.status_code == 200:
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
    current_files = os.listdir(SAVE_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        for name, url in SOURCES.items():
            try:
                print(f"📡 Z E U S B O T probing: {name}")
                
                # Method A: Direct Request for JSON/XML
                if url.endswith(('.json', '.xml')):
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        check_and_sync(r.text, name, current_files)
                        continue

                # Method B: Browser Stealth for Telegram/Web
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(10) 

                # 🚫 LOGIN BYPASS: Delete Telegram Login Modals from the UI
                page.evaluate("""() => {
                    const garbage = ['.login_modal', '#telegram-login', 'iframe[src*="telegram"]', '.overlay', '.modal-backdrop'];
                    garbage.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
                    document.body.style.overflow = 'auto'; // Re-enable scrolling if locked
                }""")

                html_content = page.content()
                body_text = page.inner_text("body")

                # ZIP Scan
                zip_links = page.query_selector_all("a[href*='.zip']")
                for link in zip_links:
                    dl_url = link.get_attribute("href")
                    if dl_url and not dl_url.startswith("http"): dl_url = "https://t.me" + dl_url
                    xml_data, used_pwd = extract_xml_from_zip(dl_url, body_text)
                    if xml_data:
                        check_and_sync(xml_data, f"{name}_ZIP", current_files, f"🔑 Pass: {used_pwd}")

                # Raw XML/Base64 Scan
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
        print(f"⏭️ {fname} exists in repo.")
        return

    fpath = os.path.join(SAVE_DIR, fname)
    with open(fpath, "w", encoding='utf-8') as f: f.write(payload)
    
    caption = f"🛡️ Z E U S B O T : SYNC SUCCESS\n👤 Source: {source_name}\n🆔 ID: {h[:12]}\n{extra}"
    with open(fpath, 'rb') as doc:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument", 
                      data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': doc})
    print(f"✅ Synced: {fname}")

if __name__ == "__main__":
    run_hunt()
