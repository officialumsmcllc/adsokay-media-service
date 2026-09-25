import os
import hashlib
import io
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image

app = FastAPI(title="AdsOkay Media & Storage Engine", version="1.0.0")

# Enable CORS for Web and Mobile Apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent disk mount directory or fallback to local ./storage
STORAGE_DIR = os.getenv("STORAGE_DIR", "/var/data/images")
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# Secret token for protected actions
MEDIA_SECRET = os.getenv("MEDIA_SECRET", "adsokay_olx_secret_2026")

# Public domain or render domain for media URLs
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")


class DownloadImagesRequest(BaseModel):
    urls: List[str]
    prefix: Optional[str] = "img"
    max_count: Optional[int] = 5


def process_and_save_image(image_bytes: bytes, filename: str) -> Optional[str]:
    """Compress image to high-efficiency WebP and save on disk"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convert RGBA / P to RGB if needed
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize if image is unreasonably huge
        max_dim = 1600
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        filepath = os.path.join(STORAGE_DIR, filename)
        img.save(filepath, "WEBP", quality=82, method=6)
        return filename
    except Exception as e:
        print(f"Error processing image {filename}: {e}", flush=True)
        return None


@app.get("/")
def health_check():
    files_count = len(os.listdir(STORAGE_DIR)) if os.path.exists(STORAGE_DIR) else 0
    return {
        "status": "online",
        "service": "AdsOkay Media Storage & Scraper Engine",
        "storage_dir": STORAGE_DIR,
        "total_images_stored": files_count
    }


@app.get("/images/{filename}")
def serve_image(filename: str):
    """Direct high-speed media delivery"""
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"})


@app.post("/api/save-remote-images")
def save_remote_images(req: DownloadImagesRequest, x_secret: Optional[str] = Header(None)):
    """Downloads external images (OLX/DubiCars), converts to WebP, and stores permanently on Render disk"""
    if x_secret and x_secret != MEDIA_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    base_url = PUBLIC_URL or ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    saved_urls = []
    for raw_url in req.urls[:req.max_count]:
        try:
            raw_url = raw_url.strip()
            if not raw_url.startswith("http"):
                continue

            # Check if we already have this image cached by URL hash
            url_hash = hashlib.md5(raw_url.encode()).hexdigest()
            filename = f"{req.prefix}_{url_hash}.webp"
            filepath = os.path.join(STORAGE_DIR, filename)

            if not os.path.exists(filepath):
                resp = requests.get(raw_url, headers=headers, timeout=12)
                if resp.status_code == 200 and len(resp.content) > 300:
                    saved = process_and_save_image(resp.content, filename)
                    if not saved:
                        continue
                else:
                    continue

            # Return absolute URL
            file_url = f"{base_url}/images/{filename}" if base_url else f"/images/{filename}"
            saved_urls.append(file_url)

        except Exception as e:
            print(f"Error downloading {raw_url}: {e}", flush=True)

    return {"status": "success", "images": saved_urls}
