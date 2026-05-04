from fastapi import APIRouter, HTTPException, Query, Request

from app.config import settings
from app.workers.tasks import process_whatsapp_message, process_messenger_message

router = APIRouter(tags=["webhooks"])


# ── WhatsApp ──────────────────────────────────────────────────────────────────

@router.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
) -> int:
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verify token inválido")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> dict[str, str]:
    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                process_whatsapp_message.delay(
                    phone_number_id=value.get("metadata", {}).get("phone_number_id"),
                    message=message,
                )

    return {"status": "ok"}


# ── Messenger ─────────────────────────────────────────────────────────────────

@router.get("/webhook/messenger")
async def messenger_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
) -> int:
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verify token inválido")


@router.post("/webhook/messenger")
async def messenger_webhook(request: Request) -> dict[str, str]:
    payload = await request.json()

    for entry in payload.get("entry", []):
        for messaging in entry.get("messaging", []):
            if "message" in messaging:
                process_messenger_message.delay(
                    page_id=entry.get("id"),
                    messaging=messaging,
                )

    return {"status": "ok"}
