import asyncio
import os
import re
from datetime import timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

load_dotenv()

# Отримуємо токен зі змінних оточення
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у змінних оточення!")

# Список заборонених слів (у нижньому регістрі)
BAN_WORDS = [
# Кириличні варіації (UA / RU)
    "нонсенс",
    "нонсенси",
    "нонсенсес",
    "нонсенсс",
    "нансенс",
    "нансенсес",
    "нонсенсы",
    "нонсэнс",
    "нонсэнсес",
    "нонсєнс",
    "нонсєнсес",
    
    # Латиниця (ENG / Трансліт)
    "nonsense",
    "nonsenses",
    "nonsens",
    "nonsensez",
    
    # Суміш/Заміна літер (Leet / Спецсимволи / Схожі символи)
    "n0nsense",
    "n0nsenses",
    "hонсенс",
    "hонсенсес",
    "hohcehc",
    "hohcehces",
    "н0нсенс",
    "н0нсенсес",
]

# Тривалість муту
MUTE_DURATION = timedelta(minutes=1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def contains_banwords(text: str) -> bool:
    """Перевіряє, чи містить текст хоча б одне заборонене слово."""
    if not text:
        return False
    
    text_lower = text.lower()
    for word in BAN_WORDS:
        # Регулярний вираз шукає слово як окреме або як частину інших слів
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
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

            # 2. Обмежуємо права користувача (mutes)
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions={"can_send_messages": False},
                until_date=MUTE_DURATION
            )

            # 3. Надсилаємо сповіщення в чат
            warning_msg = await message.answer(
            f"Користувач {message.from_user.mention_html()} отримав мут на "
            f"{int(MUTE_DURATION.total_seconds() // 60)} хв за згадку нонсенсів🤢🤮",
            parse_mode="HTML"  # <-- Додайте цей параметр
        )
            
            # # (Опціонально) Видаляємо сповіщення бота через 10 секунд, щоб не засмічувати чат
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