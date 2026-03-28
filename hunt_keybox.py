import os
import requests
import hashlib
import re
from datetime import datetime

# UPDATED SOURCES
SOURCES = {
    "Yuri": "https://raw.githubusercontent.com/Yurii0307/yurikey/main/key",
    "tryigit": "https://raw.githubusercontent.com/tryigit/PlayIntegrityFix/main/keybox.xml",
    "MeowDump": "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/keybox.xml"
}
MEOW_README = "https://raw.githubusercontent.com/MeowDump/Integrity-Box/main/README.md"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SAVE_DIR = "keyboxes"

def clean_xml_content(content):
    """
    Forcefully cleans the content to ensure it starts with '<'
    and removes any hidden binary/BOM characters.
    """
    try:
        # 1. Ensure content is a string and strip whitespace
        content = str(content).strip()
        
        # 2. Find the index of the first '<'
        start_index = content.find('<')
        
        if start_index != -1:
            # 3. Slice from the first '<' to the end
            cleaned = content[start_index:]
            
            # 4. Final check: Does it actually look like XML?
            if cleaned.startswith('<'):
                return cleaned
        return content
    except Exception as e:
        print(f"Sanitization Error: {e}")
        return content

def get_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def is_duplicate(new_hash):
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        return False
    for filename in os.listdir(SAVE_DIR):
        file_path = os.path.join(SAVE_DIR, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                if get_hash(f.read()) == new_hash:
                    return True
    return False

def send_and_save(content, source, is_strong):
    # RUN AGGRESSIVE CLEANING
    clean_content = clean_xml_content(content)
    
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"keybox_{source}_{timestamp}.xml"
    filepath = os.path.join(SAVE_DIR, filename)

    # Save with explicit UTF-8 encoding (no BOM)
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(clean_content)
    
    status = "🟢 STRONG" if is_strong else "🟡 DEVICE"
    caption = (
        f"🚀 {status} KEYBOX ARCHIVED\n"
        f"👤 Source: {source}\n"
        f"📁 File: {filename}\n"
        f"🤖 Identity: Z E U S B O T\n"
        f"✨ Fix: Binary/BOM Stripped"
    )
    
    url_doc = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    
    with open(filepath, "rb") as xml_file:
        requests.post(url_doc, data={'chat_id': TG_CHAT_ID, 'caption': caption}, files={'document': xml_file})

def run_hunt():
    try:
        meow_status = requests.get(MEOW_README, timeout=10).text
        is_strong = "🟢🟢🟢" in meow_status
    except:
        is_strong = False

    for name, url in SOURCES.items():
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                # Force decode to handle potential encoding issues from the web
                content = res.content.decode('utf-8', errors='ignore')
                
                # Check cleaned version for duplication
                cleaned = clean_xml_content(content)
                if len(cleaned) < 50: continue # Skip if empty/invalid
                
                new_hash = get_hash(cleaned)
                
                if not is_duplicate(new_hash):
                    send_and_save(content, name, is_strong)
                    return True 
        except Exception as e:
            print(f"Error checking {name}: {e}")
            continue
    return False

if __name__ == "__main__":
    run_hunt()
