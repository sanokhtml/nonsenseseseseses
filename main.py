import os
import asyncio
import re
from datetime import timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

load_dotenv()

# Отримуємо токен зі змінних оточення
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у змінних оточення!")

# Регулярний вираз для пошуку будь-яких варіацій слова "нонсенс / nonsenses"
NONSENSE_PATTERN = re.compile(
    r'[нnh][оo0aа][нnh][сsczз][еeєэ3][нnh][сsczз]([еeєэ3][сsczз])?', 
    re.IGNORECASE
)

# Тривалість муту
MUTE_DURATION = timedelta(minutes=5)

# Ініціалізація бота з дефолтним режимом HTML
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def contains_banwords(text: str) -> bool:
    """Перевіряє, чи містить текст варіації забороненого слова за допомогою RegEx."""
    if not text:
        return False
    
    if NONSENSE_PATTERN.search(text):
        return True
        
    return False

@dp.message(
    (F.text | F.caption),
    F.chat.type.in_({"group", "supergroup"})
)
async def handle_group_message(message: Message):
    # Отримуємо текст із звичайного повідомлення або з підпису до фото/відео
    content = message.text or message.caption

    if contains_banwords(content):
        try:
            # 1. Видаляємо повідомлення із банвордом
            await message.delete()

            # 2. Обмежуємо права користувача (мут)
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=MUTE_DURATION
            )

            # 3. Надсилаємо сповіщення в чат
            warning_msg = await message.answer(
                f"Користувач {message.from_user.mention_html()} отримав мут на "
                f"{int(MUTE_DURATION.total_seconds() // 60)} хв за згадку нонсенсів🤢🤮"
            )
            
            # Видаляємо сповіщення бота через 300 секунд (5 хвилин)
            await asyncio.sleep(300)
            await warning_msg.delete()

        except TelegramBadRequest as e:
            # Обробка помилок (наприклад, якщо у бота немає прав або користувач — адмін)
            print(f"Помилка при застосуванні санкцій: {e}")

async def main():
    print("Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())