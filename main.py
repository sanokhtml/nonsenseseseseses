import os
import asyncio
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у змінних оточення!")

NONSENSE_PATTERN = re.compile(
    r'[нnh][оo0aа][нnh][сsczз][еeєэ3][нnh][сsczз]([еeєэ3][сsczз])?', 
    re.IGNORECASE
)

# Для автоматичного муту через Telegram минимальний термін має бути від 30 секунд.
# Використовуємо 35 секунд, щоб перекрити розсинхрон серверного часу Render та Telegram.
MUTE_SECONDS = 35

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def contains_banwords(text: str) -> bool:
    if not text:
        return False
    return bool(NONSENSE_PATTERN.search(text))

@dp.message(
    (F.text | F.caption),
    F.chat.type.in_({"group", "supergroup"})
)
async def handle_group_message(message: Message):
    content = message.text or message.caption

    if contains_banwords(content):
        try:
            # 1. Видаляємо повідомлення
            await message.delete()

            # 2. Розраховуємо точний час закінчення муту в UTC
            until_date = datetime.now(timezone.utc) + timedelta(seconds=MUTE_SECONDS)

            # 3. Передаємо until_date напряму в Telegram (роботу з розмуту повністю бере на себе Telegram)
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )

            # 4. Надсилаємо сповіщення в чат
            warning_msg = await message.answer(
                f"Користувач {message.from_user.mention_html()} отримав мут на "
                f"{MUTE_SECONDS} сек за згадку нонсенсів🤢🤮"
            )
            
            # 5. Видаляємо сповіщення бота через 15 секунд
            await asyncio.sleep(35)
            await warning_msg.delete()

        except TelegramBadRequest as e:
            print(f"Помилка при застосуванні санкцій: {e}")

# --- Web-сервер для Uptime Robot та Render ---
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    print("Бот та веб-сервер успішно запущені...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())