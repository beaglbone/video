import os
from telethon import TelegramClient

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session = os.environ["SESSION"]
chat_id = int(os.environ["CHAT_ID"])

VIDEO_DIR = "videos"

client = TelegramClient(session, api_id, api_hash)

async def main():
    await client.start()

    for file in os.listdir(VIDEO_DIR):
        if file.endswith(".mp4"):
            path = os.path.join(VIDEO_DIR, file)
            print("Sending:", path)
            await client.send_file(
                chat_id,
                path,
                supports_streaming=True
            )

    await client.disconnect()

with client:
    client.loop.run_until_complete(main())
