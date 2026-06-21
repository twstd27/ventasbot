from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Order
from app.services.orders import InvalidTransition, transition_order
from app.workers.tasks import process_messenger_message, process_whatsapp_message

router = APIRouter(tags=["webhooks"])

# Estados de dLocal que consideramos "pagado".
_DLOCAL_PAID = {"PAID", "AUTHORIZED"}


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


# ── Confirmación de pago (dLocal) ───────────────────────────────────────────

@router.post("/webhook/payment")
async def payment_webhook(request: Request) -> dict[str, str]:
    """Recibe la notificación de dLocal y marca el pedido como pagado.

    dLocal envía (entre otros) order_id (nuestra referencia) y status.
    TODO (al habilitar pagos): verificar la firma HMAC del webhook.
    """
    payload = await request.json()
    reference = payload.get("order_id") or payload.get("reference")
    status = str(payload.get("status", "")).upper()

    if not reference:
        raise HTTPException(status_code=400, detail="Falta order_id/reference")

    if status not in _DLOCAL_PAID:
        # Otros estados (PENDING, REJECTED, etc.) no cambian el pedido por ahora.
        return {"status": "ignored", "payment_status": status}

    async with AsyncSessionLocal() as session:
        order = (
            await session.execute(select(Order).where(Order.payment_reference == reference))
        ).scalar_one_or_none()

        if order is None:
            raise HTTPException(status_code=404, detail=f"Pedido {reference} no encontrado")

        try:
            await transition_order(session, order, "paid")
        except InvalidTransition:
            # Ya estaba pagado u otro estado: idempotente, no es error.
            return {"status": "noop", "order_status": order.status}

        await session.commit()

    return {"status": "ok", "reference": reference}
