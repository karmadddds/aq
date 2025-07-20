import ffmpeg
import tempfile
import os
import time
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, DocumentAttributeVideo
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError, RPCError

# ✅ Konfigurasi API Telegram
api_id = 28832952
api_hash = 'e7400f07893872b8dd3942841ca78c0c'
session_name = 'session_name'

# ✅ Channel
source_channel_id = 2692271337
target_channel_link = "https://t.me/+qXqhA2ePsoI1NjMx"
start_message = 2600
end_message = 12000

# ✅ Batas ukuran & concurrency
MAX_FILE_SIZE_MB = 2000
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
semaphore = asyncio.Semaphore(5)  # Batasi concurrent task

# ✅ Ambil metadata video
async def get_video_metadata(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        duration = int(float(video_stream.get('duration', 1)))
        width = int(video_stream.get('width', 1280))
        height = int(video_stream.get('height', 720))

        fd, thumb_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        ffmpeg.input(video_path, ss=1).output(
            thumb_path, vframes=1, format='image2', vcodec='mjpeg'
        ).run(overwrite_output=True, quiet=True)

        return duration, width, height, thumb_path
    except Exception as e:
        print(f"⚠️ Metadata gagal: {e}")
        return 1, 1280, 720, None

# ✅ Proses download + kirim
async def download_and_send_video(message, target, client):
    async with semaphore:
        file_path = None
        thumb_path = None
        try:
            if message.file.size > MAX_FILE_SIZE_BYTES:
                print(f"⏭️ Video {message.id} dilewati (terlalu besar)")
                return

            fd, file_path = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            await message.download_media(file=file_path)

            duration, width, height, thumb_path = await get_video_metadata(file_path)

            caption = message.text or ""
            caption = caption[:1024]  # Batasi panjang caption

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
                thumb=thumb_path,
                force_document=False
            )

            print(f"✅ Video {message.id} terkirim")
        except FloodWaitError as e:
            print(f"⏸️ Flood wait {e.seconds}s, tunggu...")
            await asyncio.sleep(e.seconds)
        except RPCError as e:
            print(f"❌ RPCError di video {message.id}: {e}")
        except Exception as e:
            print(f"❌ Error video {message.id}: {e}")
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

# ✅ Main loop
async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            source = await client.get_entity(PeerChannel(source_channel_id))
            print(f"📡 Source channel: {source_channel_id}")
            await client(JoinChannelRequest(target_channel_link))
            target = await client.get_entity(target_channel_link)
            print(f"📡 Target channel: {target.title}")

            tasks = []

            async for msg in client.iter_messages(
                source,
                offset_id=start_message - 1,
                limit=end_message - start_message + 1,
                reverse=True
            ):
                if msg.video:
                    task = asyncio.create_task(download_and_send_video(msg, target, client))
                    tasks.append(task)

                    # Optional: delay kecil antar pesan
                    await asyncio.sleep(1)

            # Tunggu semua task selesai
            await asyncio.gather(*tasks)
        except FloodWaitError as e:
            print(f"⏸️ Rate limit global: tunggu {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Kesalahan utama: {e}")

if __name__ == "__main__":
    asyncio.run(main())
