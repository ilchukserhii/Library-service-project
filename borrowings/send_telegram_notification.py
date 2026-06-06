import asyncio
import os

from telegram import Bot
from dotenv import load_dotenv

from borrowings.models import Borrowing

load_dotenv()

def payload(borrow: Borrowing) -> str:
    return (
        f"📚 New borrowing\n"
        f"User: {borrow.user}\n"
        f"Book: {borrow.book}\n"
        f"Borrow date: {borrow.borrow_date}\n"
        f"Expected return: {borrow.expected_return_date}"
    )


async def send_telegram_notification(borrow: Borrowing) -> None:
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    # Send the message
    await bot.send_message(
        chat_id=os.getenv("CHAT_ID"),
        text=payload(borrow),
    )
