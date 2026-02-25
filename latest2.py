import re
from playwright.sync_api import sync_playwright
import subprocess
import os
import time
import requests

LINKS_FILE = "links.txt"
VIDEO_FOLDER = "videos"
TARGET_HEIGHT = 480          # 720 / 480 / 360
MAX_WAIT_SECONDS = 90        # ⬅️ increased wait time (IMPORTANT)
CHECK_INTERVAL = 1           # seconds

# =========================
# Create videos folder
# =========================
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# =========================
# Read links safely
# =========================
def read_links():
    if not os.path.exists(LINKS_FILE):
        return []
    with open(LINKS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

# =========================
# Select closest quality stream
# =========================
# def get_quality_stream(master_url):
    # try:
        # response = requests.get(master_url, timeout=15)
        # content = response.text.splitlines()

        # streams = []
        # for i in range(len(content)):
            # if "RESOLUTION=" in content[i]:
                # resolution = content[i].split("RESOLUTION=")[1].split(",")[0]
                # height = int(resolution.split("x")[1])
                # stream_url = content[i + 1]

                # if not stream_url.startswith("http"):
                    # base = master_url.rsplit("/", 1)[0]
                    # stream_url = f"{base}/{stream_url}"

                # streams.append((height, stream_url))

        # streams.sort(key=lambda x: abs(x[0] - TARGET_HEIGHT))

        # if streams:
            # print(f"🎯 Selected {streams[0][0]}p stream")
            # return streams[0][1]

        # return master_url

    # except Exception as e:
        # print("⚠ Quality parse failed, using original stream")
        # return master_url
        
def get_quality_stream(master_url):
    try:
        response = requests.get(master_url, timeout=15)
        content = response.text.splitlines()

        av1_streams = []
        normal_streams = []

        for i in range(len(content)):
            if "RESOLUTION=" in content[i]:
                resolution = content[i].split("RESOLUTION=")[1].split(",")[0]
                height = int(resolution.split("x")[1])
                stream_url = content[i + 1]

                if not stream_url.startswith("http"):
                    base = master_url.rsplit("/", 1)[0]
                    stream_url = f"{base}/{stream_url}"

                # classify
                if "av1" in stream_url.lower():
                    av1_streams.append((height, stream_url))
                else:
                    normal_streams.append((height, stream_url))

        # sort by closest resolution
        normal_streams.sort(key=lambda x: abs(x[0] - TARGET_HEIGHT))
        av1_streams.sort(key=lambda x: abs(x[0] - TARGET_HEIGHT))

        # 🎯 FIRST choice: non-AV1
        if normal_streams:
            print(f"🎯 Selected {normal_streams[0][0]}p (non-AV1)")
            return normal_streams[0][1]

        # fallback: AV1 only if nothing else exists
        if av1_streams:
            print(f"⚠ Only AV1 available: {av1_streams[0][0]}p")
            return av1_streams[0][1]

        return master_url

    except Exception:
        print("⚠ Quality parse failed, using original stream")
        return master_url        
        

# =========================
# Download stream using ffmpeg
# =========================
def download_stream(stream_url, title, page, context):
    # 🔐 Extract browser cookies from Playwright
    cookies = context.cookies()
    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    headers = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
    "Referer: https://www.xhamster.com/\r\n"
    "Origin: https://www.xhamster.com\r\n"
    f"Cookie: {cookie_header}\r\n"
    )
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:200]
    video_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.mp4")
    meta_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.txt")


    # stream_url = get_quality_stream(stream_url)

    # 🔒 FINAL protection check (this was missing)
    # protection = check_protection(stream_url, page, context)
    # if protection == "HIGH_PROTECTION":
        # print("🔒 High-protection quality stream (403) — skipping")
        # return

    command = [
        "ffmpeg",
        "-y",
        "-headers", headers,          # ✅ THIS LINE IS THE FIX
        "-threads", "0",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-i", stream_url,
        "-ss", "10",
        # "-map", "0:v:m:codec:avc",  # 👈 skip AV1
        # "-map", "0:a?",
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        video_path
    ]

    print(f"\n⬇️ Downloading: {safe_title}")
    result = subprocess.run(command)

    if result.returncode != 0:
        print("❌ ffmpeg failed")
        return

    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Stream URL: {stream_url}\n")
        f.write(f"Target Height: {TARGET_HEIGHT}p\n")

    print(f"✅ Saved: {video_path}")
    

def check_protection(m3u8_url, page, context):
    try:
        # get cookies from browser
        cookies = context.cookies()
        cookie_header = "; ".join(
            f"{c['name']}={c['value']}" for c in cookies
        )

        # get real browser UA
        user_agent = page.evaluate("navigator.userAgent")

        headers = {
            "User-Agent": user_agent,
            "Referer": page.url,
            "Cookie": cookie_header
        }

        r = requests.get(
            m3u8_url,
            headers=headers,
            timeout=10,
            stream=True
        )

        if r.status_code == 403:
            return "HIGH_PROTECTION"

        if r.status_code == 200:
            return "OK"

        return f"UNKNOWN_{r.status_code}"

    except Exception as e:
        return f"ERROR_{e}"    
    
    
    
    
    
def force_h264_via_ui(page):
    try:
        print("🎭 Trying to force H.264 via player UI")

        # Click video to ensure player is focused
        page.click("video", timeout=5000)

        page.wait_for_timeout(1000)

        # Try opening settings (this is generic, may vary)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)

        # Try clicking common quality labels
        for label in ["480p", "360p", "720p"]:
            try:
                page.click(f"text={label}", timeout=2000)
                print(f"🎚️ Selected quality: {label}")
                page.wait_for_timeout(2000)
                break
            except:
                continue

    except Exception as e:
        print("⚠ UI interaction failed:", e)    
    

# =========================
# Process single link (ROBUST)
# =========================
def process_link(page, link, context):
    m3u8_urls = set()

    def handle_response(response):
        if ".m3u8" in response.url:
            m3u8_urls.add(response.url)
            print("📡 Found stream:", response.url)

    page.on("response", handle_response)

    try:
        page.goto(link, wait_until="domcontentloaded", timeout=120000)

        # 🔥 NEW: force UI interaction
        force_h264_via_ui(page)

        waited = 0
        while waited < MAX_WAIT_SECONDS:
            page.wait_for_timeout(1000)
            waited += 1

            # stop early if multiple playlists appear
            if len(m3u8_urls) >= 2 and waited >= 5:
                break

        if not m3u8_urls:
            print("⚠ No stream found")
            return

        def score(url):
            return "av1" in url.lower()

        sorted_m3u8 = sorted(m3u8_urls, key=score)
        detected_url = sorted_m3u8[0]

        print(f"🎯 Using master playlist: {detected_url}")

        title = page.title()
        download_stream(detected_url, title, page, context)

    except Exception as e:
        print(f"⚠ Error: {e}")






# =========================
# Main runner (CI SAFE)
# =========================
def run():
    links = read_links()
    if not links:
        print("⚠ No links found")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        for link in links:
            print(f"\n🌐 Processing: {link}")
            page = context.new_page()
            process_link(page, link, context)
            page.close()

        browser.close()

# =========================
# Entry point
# =========================
if __name__ == "__main__":
    run()



