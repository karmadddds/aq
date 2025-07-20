import ffmpeg
import tempfile
import os
import time
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, DocumentAttributeVideo
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError

# ✅ API credentials
api_id = 28832952  # Ganti dengan milikmu
api_hash = 'e7400f07893872b8dd3942841ca78c0c'
session_name = 'session_name'

# ✅ Source dan target channel
source_channel_id = 2692271337
target_channel_link = "https://t.me/+qXqhA2ePsoI1NjMx"
start_message = 2600
end_message = 12000

# ✅ Ukuran maksimal video (MB)
MAX_FILE_SIZE_MB = 2000
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

async def get_video_metadata(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)

        duration = int(float(video_stream.get('duration', 1)))
        width = int(video_stream.get('width', 1280))
        height = int(video_stream.get('height', 720))

        # Generate thumbnail
        fd, thumb_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        (
            ffmpeg.input(video_path, ss=1)
            .output(thumb_path, vframes=1, format='image2', vcodec='mjpeg')
            .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        )
        return duration, width, height, thumb_path
    except Exception as e:
        print(f"⚠️ Gagal ambil metadata: {e}")
        return 1, 1280, 720, None

async def download_and_send_video(message, target, client):
    try:
        if message.file.size > MAX_FILE_SIZE_BYTES:
            print(f"⏭️ Video {message.id} dilewati (terlalu besar)")
            return

        fd, file_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)

        await message.download_media(file=file_path)

        duration, width, height, thumb_path = await get_video_metadata(file_path)

        # Tangani caption
        caption = message.text if isinstance(message.text, str) else " "
        if len(caption) > 1024:
            caption = caption[:1024]

        await client.send_file(
            target,
            file_path,
            caption=caption,
            attributes=[DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                supports_streaming=True
            )],
            thumb=thumb_path
        )

        print(f"✅ Video {message.id} terkirim")

    except Exception as e:
        print(f"❌ Error video {message.id}: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            source_channel = await client.get_entity(PeerChannel(source_channel_id))
            print(f"📌 Terhubung ke channel source ID: {source_channel_id}")
            await client(JoinChannelRequest(target_channel_link))
            target_channel = await client.get_entity(target_channel_link)
            print(f"📌 Terhubung ke channel target: {target_channel.title}")

            messages = []
            async for message in client.iter_messages(
                source_channel,
                offset_id=start_message - 1,
                limit=end_message - start_message + 1,
                reverse=True
            ):
                if message.video:
                    messages.append(message)

            # Urutkan berdasarkan ID
            messages.sort(key=lambda m: m.id)

            for message in messages:
                await download_and_send_video(message, target_channel, client)

        except FloodWaitError as e:
            print(f"⚠️ Rate limit: menunggu {e.seconds} detik...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Error utama: {e}")

if __name__ == "__main__":
    asyncio.run(main())
