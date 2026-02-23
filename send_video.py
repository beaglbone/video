import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["SESSION"]
chat_id = int(os.environ["CHAT_ID"])

VIDEO_DIR = "videos"

client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash
)

async def main():
    await client.start()

    # 🔑 THIS IS THE IMPORTANT PART
    entity = await client.get_entity(chat_id)

    for file in os.listdir(VIDEO_DIR):
        if file.endswith(".mp4"):
            path = os.path.join(VIDEO_DIR, file)
            print("📤 Sending:", path)

            await client.send_file(
                entity,
                path,
                video=True,
                supports_streaming=True,
                force_document=False
            )

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
