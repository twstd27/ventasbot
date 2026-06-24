"""Envío de mensajes salientes vía la WhatsApp Cloud API (Meta Graph API).

El bot genera la respuesta en `engine.py`; aquí la mandamos de vuelta al cliente.
Endpoint: POST https://graph.facebook.com/{version}/{phone_number_id}/messages
Doc: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
"""

import httpx

from app.config import settings

GRAPH_BASE = "https://graph.facebook.com"


async def send_whatsapp_text(phone_number_id: str, to: str, text: str) -> dict:
    """Envía un mensaje de texto al número `to` desde el `phone_number_id` dado.

    `to` es el número del cliente (wa_id) tal como llega en el webhook (`message.from`).
    Devuelve el JSON de Meta (incluye el message id) o levanta si no hay token.
    """
    if not settings.meta_access_token:
        raise RuntimeError(
            "META_ACCESS_TOKEN no configurado: no se puede enviar la respuesta de WhatsApp."
        )

    url = f"{GRAPH_BASE}/{settings.meta_graph_version}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.meta_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        # Meta devuelve detalle del error en el body; lo propagamos para verlo en logs.
        raise httpx.HTTPStatusError(
            f"WhatsApp send falló ({resp.status_code}): {resp.text}",
            request=resp.request,
            response=resp,
        )
    return resp.json()
