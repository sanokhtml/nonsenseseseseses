import os
import asyncio
import re
from datetime import timedelta
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

# Регулярний вираз для пошуку будь-яких варіацій слова "нонсенс / nonsenses"
NONSENSE_PATTERN = re.compile(
    r'[нnh][оo0aа][нnh][сsczз][еeєэ3][нnh][сsczз]([еeєэ3][сsczз])?', 
    re.IGNORECASE
)

MUTE_DURATION = timedelta(minutes=5)

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
            await message.delete()

            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=MUTE_DURATION
            )

            warning_msg = await message.answer(
                f"Користувач {message.from_user.mention_html()} отримав мут на "
                f"{int(MUTE_DURATION.total_seconds() // 60)} хв за згадку нонсенсів🤢🤮"
            )
            
            await asyncio.sleep(300)
            await warning_msg.delete()

        except TelegramBadRequest as e:
            print(f"Помилка при застосуванні санкцій: {e}")

# --- Фейковий веб-сервер для фрі-тарифу Render ---
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматично передає порт у змінну PORT
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # Запускаємо веб-сервер для Health Check від Render
    await start_web_server()
    print("Бот та веб-сервер успішно запущені...")
    
    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())