from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.workers.tasks import process_whatsapp_message, process_messenger_message

router = APIRouter(tags=["webhooks"])


# ── WhatsApp ──────────────────────────────────────────────────────────────────

@router.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request) -> PlainTextResponse:
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")

    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return PlainTextResponse(hub_challenge)
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
async def messenger_verify(request: Request) -> PlainTextResponse:
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")

    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        return PlainTextResponse(hub_challenge)
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
