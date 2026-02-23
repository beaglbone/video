# from playwright.sync_api import sync_playwright
# import subprocess
# import os
# import time
# import requests

# LINKS_FILE = "links.txt"
# VIDEO_FOLDER = "videos"
# TARGET_HEIGHT = 480   # change to 720 / 480 / 360

# # =========================
# # Create videos folder
# # =========================
# if not os.path.exists(VIDEO_FOLDER):
#     os.makedirs(VIDEO_FOLDER)

# # =========================
# # Read links safely
# # =========================
# def read_links():
#     if not os.path.exists(LINKS_FILE):
#         return []
#     with open(LINKS_FILE, "r") as f:
#         return [line.strip() for line in f if line.strip()]

# # =========================
# # Select correct quality from master m3u8
# # =========================
# def get_quality_stream(master_url):
#     try:
#         response = requests.get(master_url, timeout=10)
#         content = response.text.splitlines()

#         streams = []
#         for i in range(len(content)):
#             if "RESOLUTION=" in content[i]:
#                 line = content[i]
#                 resolution = line.split("RESOLUTION=")[1].split(",")[0]
#                 height = int(resolution.split("x")[1])
#                 stream_url = content[i + 1]

#                 if not stream_url.startswith("http"):
#                     base = master_url.rsplit("/", 1)[0]
#                     stream_url = base + "/" + stream_url

#                 streams.append((height, stream_url))

#         # sort by closest to TARGET_HEIGHT
#         streams.sort(key=lambda x: abs(x[0] - TARGET_HEIGHT))

#         if streams:
#             print(f"🎯 Selected {streams[0][0]}p stream")
#             return streams[0][1]

#         return master_url

#     except Exception as e:
#         print("⚠ Could not parse quality, using original stream.")
#         return master_url

# # =========================
# # Fast download (no re-encode)
# # =========================
# def download_stream(stream_url, title):

#     safe_title = "".join(c for c in title if c.isalnum() or c in " _-")
#     video_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.mp4")
#     meta_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.txt")

#     # Select proper quality
#     stream_url = get_quality_stream(stream_url)

#     # command = [
#         # "ffmpeg",
#         # "-threads", "0",
#         # "-http_persistent", "1",
#         # "-multiple_requests", "1",
#         # "-buffer_size", "50M",
#         # "-i", stream_url,
#         # "-c", "copy",
#         # video_path
#     # ]
    
#     command = [
#     "ffmpeg",
#     "-threads", "0",
#     "-i", stream_url,
#     "-c", "copy",
#     "-bsf:a", "aac_adtstoasc",
#     video_path
#     ]

#     print(f"\n⬇️ Downloading: {safe_title}")
#     subprocess.run(command)

#     with open(meta_path, "w", encoding="utf-8") as f:
#         f.write(f"Title: {title}\n")
#         f.write(f"Stream URL: {stream_url}\n")
#         f.write(f"Selected Height: {TARGET_HEIGHT}p\n")

#     print(f"✅ Saved: {video_path}")

# # =========================
# # Process link safely
# # =========================
# def process_link(page, link):

#     detected = False

#     def handle_response(response):
#         nonlocal detected
#         if detected:
#             return

#         if ".m3u8" in response.url:
#             detected = True
#             print("🔥 Stream Found")
#             title = page.title()
#             download_stream(response.url, title)

#     page.on("response", handle_response)

#     try:
#         page.goto(link, wait_until="domcontentloaded", timeout=120000)
#         page.wait_for_timeout(10000)

#         # ✅ ADD THIS BLOCK RIGHT HERE
#         if not detected:
#             print("⚠ No .m3u8 stream detected for this link")

#     except Exception as e:
#         print(f"⚠ Failed loading: {link}")
#         print(e)
# # =========================
# # Main runner
# # =========================
# def run():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         context = browser.new_context(ignore_https_errors=True)

#         links = read_links()
#         for link in links:
#             print(f"Processing: {link}")
#             page = context.new_page()
#             process_link(page, link)
#             page.close()

#         browser.close()


# if __name__ == "__main__":

#     run()



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
def get_quality_stream(master_url):
    try:
        response = requests.get(master_url, timeout=15)
        content = response.text.splitlines()

        streams = []
        for i in range(len(content)):
            if "RESOLUTION=" in content[i]:
                resolution = content[i].split("RESOLUTION=")[1].split(",")[0]
                height = int(resolution.split("x")[1])
                stream_url = content[i + 1]

                if not stream_url.startswith("http"):
                    base = master_url.rsplit("/", 1)[0]
                    stream_url = f"{base}/{stream_url}"

                streams.append((height, stream_url))

        streams.sort(key=lambda x: abs(x[0] - TARGET_HEIGHT))

        if streams:
            print(f"🎯 Selected {streams[0][0]}p stream")
            return streams[0][1]

        return master_url

    except Exception as e:
        print("⚠ Quality parse failed, using original stream")
        return master_url

# =========================
# Download stream using ffmpeg
# =========================
def download_stream(stream_url, title):
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:200]
    video_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.mp4")
    meta_path = os.path.join(VIDEO_FOLDER, f"{safe_title}.txt")

    stream_url = get_quality_stream(stream_url)

    command = [
        "ffmpeg",
        "-y",
        "-threads", "0",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-i", stream_url,
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

# =========================
# Process single link (ROBUST)
# =========================
def process_link(page, link):
    detected = False
    detected_url = None

    def handle_response(response):
        nonlocal detected, detected_url
        if detected:
            return

        if ".m3u8" in response.url:
            detected = True
            detected_url = response.url
            print("🔥 .m3u8 stream detected")

    page.on("response", handle_response)

    try:
        page.goto(link, wait_until="domcontentloaded", timeout=120000)

        waited = 0
        while waited < MAX_WAIT_SECONDS:
            if detected:
                break
            page.wait_for_timeout(CHECK_INTERVAL * 1000)
            waited += CHECK_INTERVAL

        if not detected:
            print("⚠ No stream detected within timeout")
            return

        title = page.title()
        download_stream(detected_url, title)

    except Exception as e:
        print(f"⚠ Page load failed: {e}")

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
            process_link(page, link)
            page.close()

        browser.close()

# =========================
# Entry point
# =========================
if __name__ == "__main__":
    run()
