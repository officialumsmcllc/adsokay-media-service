import requests
import json
import time
import datetime
import sys
import os
import re
import hashlib
import html

# Hostinger API & Secret
IMPORTER_URL = os.getenv("IMPORTER_URL", "https://admin.adsokay.com/olx_importer_backend.php")
SECRET = os.getenv("IMPORTER_SECRET", "adsokay_olx_secret_2026")

# Local media server endpoint on Render
MEDIA_SERVER_URL = os.getenv("MEDIA_SERVER_URL", "http://127.0.0.1:8000")

PAK_FIRST_NAMES = [
    'Muhammad', 'Ali', 'Hamza', 'Usman', 'Bilal', 'Zubair', 'Farhan', 'Shahid', 'Kashif', 'Waqas',
    'Adeel', 'Hassan', 'Noman', 'Asad', 'Kamran', 'Faisal', 'Omer', 'Danish', 'Arslan', 'Zeeshan',
    'Saad', 'Umair', 'Tariq', 'Sohail', 'Imran', 'Babar', 'Haris', 'Junaid', 'Rashid', 'Mohsin',
    'Taimoor', 'Ahsan', 'Irfan', 'Baqir', 'Shoaib', 'Mubashir', 'Rehman', 'Shahzaib', 'Ammar', 'Haider'
]
PAK_LAST_NAMES = [
    'Khan', 'Ahmed', 'Malik', 'Raza', 'Bhatti', 'Chaudhry', 'Sheikh', 'Butt', 'Siddiqui', 'Shah',
    'Mehmood', 'Hussain', 'Ashraf', 'Javed', 'Akram', 'Nadeem', 'Farooq', 'Qureshi', 'Rehman', 'Iqbal',
    'Ansari', 'Mirza', 'Abbasi', 'Mughal', 'Gillani', 'Wattoo', 'Cheema', 'Tarar', 'Bajwa', 'Virk'
]
PAK_PREFIXES = [
    '0300', '0301', '0302', '0303', '0304', '0305', '0306', '0307', '0308', '0309',
    '0310', '0311', '0312', '0313', '0314', '0315', '0316', '0317', '0318',
    '0320', '0321', '0322', '0323', '0324', '0325',
    '0331', '0332', '0333', '0334', '0335', '0336', '0337',
    '0340', '0341', '0342', '0343', '0344', '0345', '0346', '0347'
]

PAKISTAN_STREAMS = [
    ("All Pakistan - Stream 1", "https://www.olx.com.pk/items?page=1"),
    ("All Pakistan - Stream 2", "https://www.olx.com.pk/items?page=2"),
    ("All Pakistan - Stream 3", "https://www.olx.com.pk/items?page=3"),
    ("All Pakistan - Mobile Phones", "https://www.olx.com.pk/mobile-phones_c1453"),
    ("All Pakistan - Cars", "https://www.olx.com.pk/cars_c84"),
    ("All Pakistan - Motorcycles", "https://www.olx.com.pk/motorcycles_c81"),
    ("All Pakistan - Plots & Land", "https://www.olx.com.pk/plots-land_c1723"),
    ("All Pakistan - Property for Sale", "https://www.olx.com.pk/property-for-sale_c2"),
    ("All Pakistan - TVs & Audio", "https://www.olx.com.pk/tvs-video-audio_c300"),
    ("All Pakistan - Clothes", "https://www.olx.com.pk/clothes_c88"),
    ("All Pakistan - Fashion & Beauty", "https://www.olx.com.pk/fashion-beauty_c87"),
    ("All Pakistan - Services", "https://www.olx.com.pk/services_c619"),
    
    # Sindh
    ("Karachi (Sindh) - Page 1", "https://www.olx.com.pk/karachi_g4060695?page=1"),
    ("Karachi (Sindh) - Page 2", "https://www.olx.com.pk/karachi_g4060695?page=2"),
    ("Hyderabad (Sindh) - Page 1", "https://www.olx.com.pk/hyderabad_g4060674?page=1"),
    ("Sukkur (Sindh) - Page 1", "https://www.olx.com.pk/sukkur_g4060686?page=1"),
    ("Larkana (Sindh) - Page 1", "https://www.olx.com.pk/larkana_g4060676?page=1"),
    
    # Punjab
    ("Lahore (Punjab) - Page 1", "https://www.olx.com.pk/lahore_g4060673?page=1"),
    ("Lahore (Punjab) - Page 2", "https://www.olx.com.pk/lahore_g4060673?page=2"),
    ("Rawalpindi (Punjab) - Page 1", "https://www.olx.com.pk/rawalpindi_g4060682?page=1"),
    ("Faisalabad (Punjab) - Page 1", "https://www.olx.com.pk/faisalabad_g4060677?page=1"),
    ("Multan (Punjab) - Page 1", "https://www.olx.com.pk/multan_g4060680?page=1"),
    ("Gujranwala (Punjab) - Page 1", "https://www.olx.com.pk/gujranwala_g4060678?page=1"),
    ("Sialkot (Punjab) - Page 1", "https://www.olx.com.pk/sialkot_g4060684?page=1"),
    ("Sahiwal (Punjab) - Page 1", "https://www.olx.com.pk/sahiwal_g4060683?page=1"),
    ("Bahawalpur (Punjab) - Page 1", "https://www.olx.com.pk/bahawalpur_g4060675?page=1"),
    ("Sargodha (Punjab) - Page 1", "https://www.olx.com.pk/sargodha_g4060685?page=1"),
    ("Gujrat (Punjab) - Page 1", "https://www.olx.com.pk/gujrat_g4060690?page=1"),
    ("Sheikhupura (Punjab) - Page 1", "https://www.olx.com.pk/sheikhupura_g4060687?page=1"),
    ("Jhang (Punjab) - Page 1", "https://www.olx.com.pk/jhang_g4060688?page=1"),
    ("Rahim Yar Khan (Punjab) - Page 1", "https://www.olx.com.pk/rahim-yar-khan_g4060689?page=1"),
    ("Okara (Punjab) - Page 1", "https://www.olx.com.pk/okara_g4060691?page=1"),
    ("Kasur (Punjab) - Page 1", "https://www.olx.com.pk/kasur_g4060692?page=1"),
    
    # ICT (Capital)
    ("Islamabad (ICT) - Page 1", "https://www.olx.com.pk/islamabad_g2003003?page=1"),
    ("Islamabad (ICT) - Page 2", "https://www.olx.com.pk/islamabad_g2003003?page=2"),
    
    # KPK
    ("Peshawar (KPK) - Page 1", "https://www.olx.com.pk/peshawar_g4060681?page=1"),
    ("Abbottabad (KPK) - Page 1", "https://www.olx.com.pk/abbottabad_g4060693?page=1"),
    ("Mardan (KPK) - Page 1", "https://www.olx.com.pk/mardan_g4060694?page=1"),
    ("Swat (KPK) - Page 1", "https://www.olx.com.pk/swat_g4060696?page=1"),
    
    # Balochistan & AJK
    ("Quetta (Balochistan) - Page 1", "https://www.olx.com.pk/quetta_g4060679?page=1"),
    ("Gwadar (Balochistan) - Page 1", "https://www.olx.com.pk/gwadar_g4060697?page=1"),
    ("Mirpur (AJK) - Page 1", "https://www.olx.com.pk/mirpur-azad-kashmir_g4060698?page=1"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [OLX] {msg}", flush=True)

def clean_seller_name(raw_name, ad_id):
    if raw_name:
        name = html.unescape(raw_name).strip()
        name = re.sub(r'[\(\)\[\]\{\}\*\#\_\~\|\<\>\@\$\%\^\&\+\=\?\/\\\"\'\`\:\;]', ' ', name)
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        lower_name = name.lower()
        bad_words = ['olx user', 'user', 'unknown', 'seller', 'fazol', 'offers', 'message', 'call', 'rate', 'urgent', 'available', 'karachi', 'lahore', 'pakistan', 'null', 'none']
        is_bad = any(bw in lower_name and len(name.split()) <= 2 for bw in bad_words)
        if len(name) >= 3 and not is_bad and not name.isdigit():
            return ' '.join(w.capitalize() for w in name.split()[:3])
            
    h = int(hashlib.md5(str(ad_id).encode()).hexdigest(), 16)
    fn = PAK_FIRST_NAMES[h % len(PAK_FIRST_NAMES)]
    ln = PAK_LAST_NAMES[(h // 100) % len(PAK_LAST_NAMES)]
    return f"{fn} {ln}"

def save_images_to_render(img_urls):
    """Sends external image URLs to Render media service to save on Persistent Disk"""
    if not img_urls:
        return []
    try:
        r = requests.post(
            f"{MEDIA_SERVER_URL}/api/save-remote-images",
            json={"urls": img_urls, "prefix": "olx", "max_count": 5},
            headers={"X-Secret": SECRET},
            timeout=25
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("images"):
                return res["images"]
    except Exception as e:
        log(f"Media server download error: {e}")
    # Fallback to original URLs if media server is initializing
    return img_urls[:5]

def extract_ads_from_html(html_text):
    ads = []
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_text, re.DOTALL)
    if not match:
        return ads

    try:
        data = json.loads(match.group(1))
        initial_state = data.get('props', {}).get('pageProps', {}).get('initialState', {})
        items = initial_state.get('items', {}).get('elements', [])
        
        for item in items:
            title = item.get('title')
            if not title:
                continue

            ad_id = str(item.get('id', ''))
            price = item.get('price', {}).get('value', {}).get('raw', 0)
            description = item.get('description', title)
            
            raw_user_name = item.get('user', {}).get('name') if isinstance(item.get('user'), dict) else None
            seller_name = clean_seller_name(raw_user_name, ad_id)
            seller_id = str(item.get('user', {}).get('id') if isinstance(item.get('user'), dict) else ad_id)
            
            h = int(hashlib.md5(ad_id.encode()).hexdigest(), 16)
            prefix = PAK_PREFIXES[h % len(PAK_PREFIXES)]
            phone_num = prefix + str(h % 9000000 + 1000000).zfill(7)
            
            # Location
            loc_data = item.get('location', {})
            city = 'Pakistan'
            state = 'Punjab'
            subarea = ''
            if isinstance(loc_data, dict):
                loc_list = loc_data.get('list', [])
                if len(loc_list) >= 3:
                    state = loc_list[0].get('name', 'Punjab')
                    city = loc_list[1].get('name', 'Pakistan')
                    subarea = loc_list[2].get('name', '')
                elif len(loc_list) == 2:
                    state = loc_list[0].get('name', 'Punjab')
                    city = loc_list[1].get('name', 'Pakistan')
                elif len(loc_list) == 1:
                    city = loc_list[0].get('name', 'Pakistan')
                    
            coords = loc_data.get('coordinates', {}) if isinstance(loc_data, dict) else {}
            lat = coords.get('lat') if isinstance(coords, dict) else 30.674387
            lng = coords.get('lon') if isinstance(coords, dict) else 73.083372
            
            # Category
            cat_data = item.get('category', {})
            cat_name = 'General'
            if isinstance(cat_data, dict):
                cat_name = cat_data.get('name', 'General')

            # Images
            raw_img_urls = []
            for photo in item.get('photos', []):
                if isinstance(photo, dict) and photo.get('full'):
                    raw_img_urls.append(photo['full'])
                elif isinstance(photo, dict) and photo.get('thumbnail'):
                    raw_img_urls.append(photo['thumbnail'])

            # SAVE ON RENDER PERSISTENT DISK
            render_images = save_images_to_render(raw_img_urls)

            ads.append({
                "title": title,
                "description": description,
                "price": price,
                "category_name": cat_name,
                "seller_name": seller_name,
                "seller_id": seller_id,
                "contact": phone_num,
                "city": city,
                "state": state,
                "subarea": subarea,
                "country": "Pakistan",
                "country_code": "PK",
                "latitude": lat,
                "longitude": lng,
                "images": render_images
            })
            
    except Exception as e:
        log(f"JSON parsing error: {e}")
        
    return ads

def post_to_backend(ads):
    if not ads:
        return 0
    try:
        r = requests.post(
            IMPORTER_URL,
            json={"ads": ads},
            headers={"X-Import-Secret": SECRET, "Content-Type": "application/json"},
            timeout=40
        )
        if r.status_code == 200:
            res = r.json()
            log(f"Import success! Added: {res.get('imported', 0)}, Skipped/Exists: {res.get('skipped', 0)}")
            return res.get('imported', 0)
        else:
            log(f"Backend returned status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log(f"Backend post error: {e}")
    return 0

def run_olx_cycle():
    total_added = 0
    for stream_name, url in PAKISTAN_STREAMS:
        try:
            log(f"Scanning {stream_name}...")
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                ads = extract_ads_from_html(r.text)
                if ads:
                    added = post_to_backend(ads)
                    total_added += added
            time.sleep(3)
        except Exception as e:
            log(f"Stream error on {stream_name}: {e}")
            time.sleep(2)
    return total_added

if __name__ == "__main__":
    run_olx_cycle()
