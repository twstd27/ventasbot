"""Generación de QR de pago vía dLocal (Bolivia).

Dos modos:
  - SIMULADO: si no hay credenciales de dLocal (pagos aún no habilitados),
    devuelve un QR/reference ficticio para poder probar todo el flujo end-to-end.
  - REAL: si hay credenciales, llama a la API Payins de dLocal con autenticación
    HMAC. Pendiente de validar contra el sandbox real cuando haya credenciales.

La confirmación del pago llega por webhook (ver app/api/v1/webhooks.py).
"""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import settings
from app.models import Merchant, Order

DLOCAL_SANDBOX_URL = "https://sandbox.dlocal.com"
DLOCAL_PROD_URL = "https://api.dlocal.com"


def _reference_for(order: Order) -> str:
    return f"VB-{str(order.id)[:8].upper()}"


def _has_credentials() -> bool:
    return bool(settings.dlocal_api_key and settings.dlocal_secret_key)


def _simulated_qr(order: Order) -> dict[str, Any]:
    reference = _reference_for(order)
    return {
        "simulado": True,
        "reference": reference,
        "qr_url": f"https://pay.ventabot.local/sandbox/{reference}",
        "status": "pending",
        "nota": (
            "QR SIMULADO (dLocal sin credenciales). Sirve para probar el flujo; "
            "reemplazar por el QR real al habilitar pagos."
        ),
    }


def _sign(login: str, x_date: str, body: str) -> str:
    """Firma HMAC-SHA256 que dLocal exige en el header Authorization."""
    message = f"{login}{x_date}{body}".encode()
    secret = settings.dlocal_secret_key.encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


async def _real_qr(order: Order, merchant: Merchant) -> dict[str, Any]:
    base = DLOCAL_SANDBOX_URL if settings.dlocal_sandbox else DLOCAL_PROD_URL
    reference = _reference_for(order)
    x_date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    payload = {
        "amount": float(order.total_amount),
        "currency": "BOB",
        "country": "BO",
        "payment_method_id": "QR",          # método QR para Bolivia
        "payment_method_flow": "REDIRECT",
        "order_id": reference,
        "notification_url": settings.dlocal_notification_url or "",
    }
    body = json.dumps(payload)
    signature = _sign(settings.dlocal_api_key, x_date, body)
    headers = {
        "X-Date": x_date,
        "X-Login": settings.dlocal_api_key,
        "X-Trans-Key": settings.dlocal_secret_key,
        "Content-Type": "application/json",
        "Authorization": f"V2-HMAC-SHA256, Signature: {signature}",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{base}/payments", content=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return {
        "simulado": False,
        "reference": reference,
        "qr_url": data.get("redirect_url") or data.get("qr_url"),
        "status": data.get("status", "pending").lower(),
        "dlocal_id": data.get("id"),
    }


async def create_payment_qr(order: Order, merchant: Merchant) -> dict[str, Any]:
    """Crea (o simula) el QR de pago para un pedido."""
    if not _has_credentials():
        return _simulated_qr(order)
    try:
        return await _real_qr(order, merchant)
    except Exception as exc:  # noqa: BLE001 — degradar a simulado si dLocal falla
        result = _simulated_qr(order)
        result["nota"] = f"dLocal falló ({type(exc).__name__}); se usó QR simulado."
        return result
