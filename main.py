import os
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, MessageIdInvalidError
from telethon.tl.types import DocumentAttributeVideo
from telethon.tl.functions.messages import ImportChatInviteRequest

# 🔐 API & Session Config
api_id = 28832952
api_hash = 'e7400f07893872b8dd3942841ca78c0c'
session_name = 'session_name'

# 📌 Channel Info
source_channel_id = 2692271337
target_channel_link = "https://t.me/+qXqhA2ePsoI1NjMx"
start_message = 2600
end_message = 12000

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    # Bergabung ke channel tujuan jika belum
    if '+qXqhA2ePsoI1NjMx' in target_channel_link:
        try:
            await client(ImportChatInviteRequest(target_channel_link.split('+')[1]))
        except Exception:
            pass  # Sudah join atau invite expired

    # Ambil entity dari ID dan link
    source = await client.get_entity(source_channel_id)
    target = await client.get_entity(target_channel_link)

    for msg_id in range(start_message, end_message + 1):
        try:
            message = await client.get_messages(source, ids=msg_id)

            if not message or not message.video:
                print(f"⏩ {msg_id} bukan video.")
                continue

            # Kirim ulang tanpa caption, dengan thumbnail jika ada
            await client.send_file(
                entity=target,
                file=message.video,
                thumb=message.file.thumb if message.file and message.file.thumb else None,
                attributes=[DocumentAttributeVideo(
                    duration=0, w=0, h=0, supports_streaming=True
                )],
                caption='',  # Tanpa caption
                force_document=False,
                video_note=False
            )

            print(f"✅ Terkirim: video ID {msg_id}")

        except FloodWaitError as e:
            print(f"⏳ FloodWait {e.seconds} detik... menunggu.")
            await asyncio.sleep(e.seconds)
        except MessageIdInvalidError:
            print(f"❌ Message ID tidak valid: {msg_id}")
        except Exception as e:
            print(f"❌ Gagal kirim ID {msg_id}: {e}")

        await asyncio.sleep(1.5)  # Delay aman

    print("🎉 Semua video selesai dikirim!")

if __name__ == '__main__':
    asyncio.run(main())
