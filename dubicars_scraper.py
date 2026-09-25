import requests
from bs4 import BeautifulSoup
import re
import json
import time
import datetime
import sys
import os

IMPORTER_URL = os.getenv("IMPORTER_URL", "https://admin.adsokay.com/olx_importer_backend.php")
SECRET = os.getenv("IMPORTER_SECRET", "adsokay_olx_secret_2026")
MEDIA_SERVER_URL = os.getenv("MEDIA_SERVER_URL", "http://127.0.0.1:8000")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [DubiCars] {msg}", flush=True)

def save_images_to_render(img_urls):
    if not img_urls:
        return []
    try:
        r = requests.post(
            f"{MEDIA_SERVER_URL}/api/save-remote-images",
            json={"urls": img_urls, "prefix": "dubi", "max_count": 5},
            headers={"X-Secret": SECRET},
            timeout=25
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("images"):
                return res["images"]
    except Exception as e:
        log(f"Media server download error: {e}")
    return img_urls[:5]

def get_all_dealer_urls():
    dealers = []
    for page in range(1, 10):
        url = f"https://www.dubicars.com/dealers?page={page}" if page > 1 else "https://www.dubicars.com/dealers"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, 'html.parser')
            page_dealers = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/dealers/' in href and href != '/dealers' and not href.endswith('/dealers'):
                    if not href.startswith('http'):
                        href = 'https://www.dubicars.com' + href
                    if href not in dealers:
                        dealers.append(href)
                        page_dealers.append(href)
            if not page_dealers:
                break
            time.sleep(1)
        except Exception as e:
            log(f"Error fetching dealer page {page}: {e}")
            break
    return dealers

def scrape_and_import_dealer(dealer_url, max_cars_per_dealer=10):
    try:
        r = requests.get(dealer_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return 0
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Dealer Name
        h1 = soup.find('h1')
        raw_name = h1.get_text(strip=True) if h1 else "UAE Motors Showroom"
        dealer_name = raw_name.split("-")[0].strip()
        
        dealer_id_match = re.search(r'/dealers/([^/]+)', dealer_url)
        seller_id = dealer_id_match.group(1) if dealer_id_match else "dubicars_dealer"
        
        # Location inference
        city = "Dubai"
        d_lower = dealer_url.lower() + " " + raw_name.lower()
        if 'sharjah' in d_lower:
            city = "Sharjah"
        elif 'abu-dhabi' in d_lower or 'abu dhabi' in d_lower:
            city = "Abu Dhabi"
        elif 'ajman' in d_lower:
            city = "Ajman"
        elif 'ras-al-khaimah' in d_lower or 'ras al khaimah' in d_lower:
            city = "Ras Al Khaimah"
            
        # Car listing links
        car_urls = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.search(r'-\d+\.html', href) and '/dealers/' not in href and '/news/' not in href:
                if not href.startswith('http'):
                    href = 'https://www.dubicars.com' + href
                if href not in car_urls:
                    car_urls.append(href)
                    
        if not car_urls:
            return 0
            
        ads_payload = []
        
        for idx, curl in enumerate(car_urls[:max_cars_per_dealer]):
            try:
                rcar = requests.get(curl, headers=HEADERS, timeout=15)
                if rcar.status_code != 200:
                    continue
                
                csoup = BeautifulSoup(rcar.text, 'html.parser')
                
                # Title
                ctitle_tag = csoup.find('h1')
                if not ctitle_tag:
                    continue
                title = ctitle_tag.get_text(strip=True)
                
                # Price (AED)
                pmatch = re.search(r'AED\s*([\d,]+)', rcar.text)
                price = float(pmatch.group(1).replace(',', '')) if pmatch else 0
                    
                # Images extraction
                car_imgs = []
                for img in csoup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy') or ''
                    if 'dubicars.com/images/' in src and ('w_' in src or '960x' in src or '1300x' in src):
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            src = 'https://' + src.lstrip('/')
                        if src not in car_imgs:
                            car_imgs.append(src)
                            
                if len(car_imgs) < 2:
                    raw_dubi_imgs = re.findall(r'(?:https?:)?//(?:www\.)?dubicars\.com/images/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', rcar.text)
                    for im in raw_dubi_imgs:
                        if im.startswith('//'):
                            im = 'https:' + im
                        if 'w_' in im or '960x' in im or '1300x' in im:
                            if im not in car_imgs:
                                car_imgs.append(im)
                                
                # Save to Render Persistent Disk
                render_images = save_images_to_render(car_imgs[:5])
                        
                # Specifications
                specs = []
                for row in csoup.find_all(['li', 'div', 'tr', 'p']):
                    txt = row.get_text(separator=': ', strip=True)
                    if any(k in txt.lower() for k in ['kilometers', 'model year', 'year', 'specs', 'gearbox', 'fuel type', 'color', 'number of doors', 'cylinders', 'engine capacity', 'horsepower']):
                        parts = [p.strip() for p in txt.split(':') if p.strip()]
                        if len(parts) == 2 and len(parts[0]) < 25 and len(parts[1]) < 35:
                            spec_line = f"- {parts[0]}: {parts[1]}"
                            if spec_line not in specs:
                                specs.append(spec_line)
                                
                full_description = f"{title}\n\nVehicle Specifications:\n" + "\n".join(specs) + f"\n\nAvailable at {dealer_name} showroom ({city}, UAE)."
                
                # Contact
                phone_match = re.search(r'(?:\+?971|00971|0)?\s*(5[024568]\d{7})', rcar.text)
                contact = f"+971{phone_match.group(1)}" if phone_match else "+971501234567"
                
                ad_item = {
                    "title": title,
                    "description": full_description,
                    "price": price,
                    "category_name": "Cars",
                    "seller_name": dealer_name,
                    "seller_id": seller_id,
                    "contact": contact,
                    "city": city,
                    "state": city,
                    "country": "United Arab Emirates",
                    "country_code": "AE",
                    "latitude": 25.2048 if city == "Dubai" else 25.3573,
                    "longitude": 55.2708 if city == "Dubai" else 55.4033,
                    "images": render_images
                }
                ads_payload.append(ad_item)
                time.sleep(1)
            except Exception as e:
                log(f"Car extraction error: {e}")
                
        if ads_payload:
            rpost = requests.post(
                IMPORTER_URL,
                json={"ads": ads_payload},
                headers={"X-Import-Secret": SECRET, "Content-Type": "application/json"},
                timeout=40
            )
            if rpost.status_code == 200:
                res = rpost.json()
                log(f"Dealer {dealer_name} imported: {res.get('imported', 0)} new cars")
                return res.get('imported', 0)
                
    except Exception as e:
        log(f"Dealer error {dealer_url}: {e}")
    return 0

def run_dubicars_cycle():
    dealers = get_all_dealer_urls()
    log(f"Found {len(dealers)} UAE DubiCars dealers to process")
    total = 0
    for idx, durl in enumerate(dealers):
        log(f"[{idx+1}/{len(dealers)}] Processing dealer {durl}...")
        added = scrape_and_import_dealer(durl, max_cars_per_dealer=8)
        total += added
        time.sleep(3)
    return total

if __name__ == "__main__":
    run_dubicars_cycle()
