import os
import ffmpeg
import time
import random
import tempfile
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import PeerChannel, DocumentAttributeVideo
from telethon.tl.functions.channels import JoinChannelRequest

# ✅ Konfigurasi API Telegram
api_id = 28832952
api_hash = 'e7400f07893872b8dd3942841ca78c0c'
session_name = 'session_name'

# ✅ Info Channel
source_channel_id = 2692271337
target_channel_link = "https://t.me/+qXqhA2ePsoI1NjMx"
start_message = 2600
end_message = 12000

MAX_FILE_SIZE_MB = 2000
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
BATCH_SIZE = 10
DELAY = (2.0, 4.5)

async def get_video_metadata(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if video_stream:
            duration = int(float(video_stream.get('duration', 0)))
            width = int(video_stream.get('width', 1280))
            height = int(video_stream.get('height', 720))

            thumb_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            ffmpeg.input(video_path, ss=1).output(thumb_path, vframes=1).run(overwrite_output=True, quiet=True)
            return duration, width, height, thumb_path
    except Exception as e:
        print(f"⚠️ Metadata error: {e}")
    return 0, 1280, 720, None

async def download_and_send_video(message, target, client):
    try:
        if message.file.size > MAX_FILE_SIZE_BYTES:
            print(f"⏭️ {message.id} dilewati (terlalu besar)")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download_media(file=tmp.name)
            file_path = tmp.name

        duration, width, height, thumb_path = await get_video_metadata(file_path)

        await client.send_file(
            target,
            file_path,
            caption=message.text or f"Video {message.id}",
            attributes=[DocumentAttributeVideo(duration=duration, w=width, h=height, supports_streaming=True)],
            thumb=thumb_path if thumb_path else None
        )

        os.remove(file_path)
        if thumb_path:
            os.remove(thumb_path)

        print(f"✅ Video {message.id} terkirim")
        await asyncio.sleep(random.uniform(*DELAY))

    except FloodWaitError as e:
        print(f"⚠️ FloodWait {e.seconds} detik")
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        print(f"❌ Gagal {message.id}: {e}")

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            source_channel = await client.get_entity(PeerChannel(source_channel_id))
            await client(JoinChannelRequest(target_channel_link))
            target_channel = await client.get_entity(target_channel_link)

            tasks = []
            async for msg in client.iter_messages(source_channel, reverse=True,
                                                  offset_id=start_message - 1,
                                                  limit=end_message - start_message + 1):
                if msg.video:
                    tasks.append(download_and_send_video(msg, target_channel, client))
                    if len(tasks) >= BATCH_SIZE:
                        await asyncio.gather(*tasks)
                        tasks = []
            if tasks:
                await asyncio.gather(*tasks)

            print("🎉 Semua video selesai dikirim!")

        except Exception as e:
            print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
