import os
import asyncio
import time
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import InputPeerChannel, InputMediaUploadedDocument, DocumentAttributeVideo

# Ganti dengan milikmu
api_id = 12345678
api_hash = "your_api_hash"
session_name = "session"
target_channel = "https://t.me/namachannel_anda"

# Konfigurasi range video
START_INDEX = 2600
END_INDEX = 12000
VIDEO_FOLDER = "./videos"           # Ganti sesuai lokasi file
THUMBNAIL_FOLDER = "./thumbnails"   # Optional

# Delay antar upload (untuk keamanan)
BASE_DELAY = 1.2  # detik

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        entity = await client.get_entity(target_channel)

        for i in range(START_INDEX, END_INDEX + 1):
            video_path = os.path.join(VIDEO_FOLDER, f"video_{i}.mp4")
            thumb_path = os.path.join(THUMBNAIL_FOLDER, f"video_{i}.jpg")

            if not os.path.isfile(video_path):
                print(f"❌ Video {i} tidak ditemukan: {video_path}")
                continue

            try:
                attributes = [DocumentAttributeVideo(duration=0, w=0, h=0, supports_streaming=True)]

                start = time.time()
                await client.send_file(
                    entity,
                    file=video_path,
                    thumb=thumb_path if os.path.isfile(thumb_path) else None,
                    attributes=attributes,
                    caption=f"Video {i}"
                )
                elapsed = time.time() - start
                print(f"✅ Video {i} terkirim (⏱️ {elapsed:.1f} detik)")

                await asyncio.sleep(BASE_DELAY)

            except FloodWaitError as e:
                print(f"⚠️ FloodWait {e.seconds} detik. Menunggu...")
                await asyncio.sleep(e.seconds + 2)

            except Exception as e:
                print(f"❌ Gagal mengirim video {i}: {e}")
                continue

        print("🎉 Semua video selesai dikirim!")

if __name__ == "__main__":
    asyncio.run(main())
