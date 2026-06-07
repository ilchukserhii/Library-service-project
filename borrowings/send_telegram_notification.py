import asyncio
import os

from django.utils import timezone
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

def payload_for_overdue(borrow: Borrowing) -> str:
    return (
        f"!!! Overdue borrowing\n"
        f"User: {borrow.user}\n"
        f"Book: {borrow.book}\n"
        f"Borrow date: {borrow.borrow_date}\n"
        f"Expected return: {borrow.expected_return_date}"
    )

def get_overdue_borrowings():
    return Borrowing.objects.filter(
        expected_return_date__lt=timezone.localdate(),
        actual_return_date__isnull=True,
    )


async def send_telegram_message(text: str) -> None:
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await bot.send_message(
        chat_id=os.getenv("CHAT_ID"),
        text=text,
    )

async def send_telegram_notification(borrow: Borrowing) -> None:
    await send_telegram_message(payload(borrow))

def send_overdue_notifications() -> None:
    overdues = get_overdue_borrowings()

    if not overdues.exists():
        asyncio.run(send_telegram_message("No borrowings overdue today!"))
        return

    for borrow in overdues:
        asyncio.run(send_telegram_message(payload_for_overdue(borrow)))