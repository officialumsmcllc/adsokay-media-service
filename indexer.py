import requests
import json
import time
import datetime

INDEXNOW_KEY = "adsokay99482710492817294820"
HOST = "adsokay.com"
KEY_LOCATION = f"https://adsokay.com/{INDEXNOW_KEY}.txt"

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [CLOUD-INDEXER] {msg}", flush=True)

def fetch_active_ad_urls(max_pages=20):
    all_urls = [
        "https://adsokay.com/",
        "https://adsokay.com/ads",
        "https://adsokay.com/blogs",
        "https://adsokay.com/about-us",
        "https://adsokay.com/contact-us",
        "https://adsokay.com/faqs",
    ]
    
    url = "https://admin.adsokay.com/api/get-item-slug?page=1"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            data = r.json()
            last_page = data.get("data", {}).get("last_page", 1)
            target_pages = min(last_page, max_pages)
            
            for page in range(1, target_pages + 1):
                p_url = f"https://admin.adsokay.com/api/get-item-slug?page={page}"
                res = requests.get(p_url, timeout=15)
                if res.status_code == 200:
                    p_data = res.json()
                    items = p_data.get("data", {}).get("data", [])
                    for it in items:
                        slug = it.get("slug") or it.get("id")
                        if slug:
                            all_urls.append(f"https://adsokay.com/ad-details/{slug}")
                time.sleep(0.1)
    except Exception as e:
        log(f"Error fetching active slugs: {e}")

    return all_urls

def submit_to_indexnow(urls):
    if not urls:
        return 0

    endpoint = "https://api.indexnow.org/indexnow"
    chunk_size = 500
    successful_batches = 0

    for i in range(0, len(urls), chunk_size):
        chunk = urls[i:i+chunk_size]
        payload = {
            "host": HOST,
            "key": INDEXNOW_KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": chunk
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=25)
            if resp.status_code == 200:
                successful_batches += 1
        except Exception as e:
            log(f"IndexNow batch error: {e}")
        time.sleep(0.2)

    return successful_batches

def run_cloud_indexing():
    try:
        log("=== Starting Cloud Auto-Indexing Run on Render ===")
        urls = fetch_active_ad_urls(max_pages=20)
        log(f"Collected {len(urls)} URLs from live database.")
        batches = submit_to_indexnow(urls)
        log(f"Successfully submitted {len(urls)} URLs in {batches} batches to IndexNow (Bing/Yahoo/Yandex/Partners).")
        log("=== Cloud Auto-Indexing Completed Successfully ===")
    except Exception as e:
        log(f"Cloud indexing error: {e}")

if __name__ == "__main__":
    run_cloud_indexing()
