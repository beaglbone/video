import os
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["SESSION"]
chat_id = int(os.environ["CHAT_ID"])

VIDEO_DIR = "videos"

# ✅ IMPORTANT FIX HERE
client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash
)

async def main():
    await client.start()

    for file in os.listdir(VIDEO_DIR):
        if file.endswith(".mp4"):
            path = os.path.join(VIDEO_DIR, file)
            print("📤 Sending:", path)

            await client.send_file(
                chat_id,
                path,
                video=True,              # compression ON
                supports_streaming=True,
                force_document=False
            )

    await client.disconnect()

with client:
    client.loop.run_until_complete(main())



    

