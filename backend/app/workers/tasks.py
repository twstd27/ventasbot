import asyncio
from typing import Any

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_whatsapp_message(self: Any, phone_number_id: str, message: dict[str, Any]) -> None:
    from app.bot.engine import handle_message

    try:
        asyncio.run(handle_message(
            channel="whatsapp",
            channel_id=phone_number_id,
            message=message,
        ))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(bind=True, max_retries=3)
def process_messenger_message(self: Any, page_id: str, messaging: dict[str, Any]) -> None:
    from app.bot.engine import handle_message

    try:
        asyncio.run(handle_message(
            channel="messenger",
            channel_id=page_id,
            message=messaging,
        ))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
