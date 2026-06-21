"""Chat de prueba del bot desde la terminal — Fases 1-3.

Simula un cliente conversando por WhatsApp con el merchant demo. Usa la base
real (Supabase), tool-calling real e historial persistido.

Uso (desde backend/):
    uv run python scripts/chat.py

Requiere:
  - LLM_API_KEY en .env (Groq gratis: https://console.groq.com)
  - haber corrido scripts/seed.py para tener el merchant demo
"""

import asyncio
import sys
from pathlib import Path

# La consola de Windows usa cp1252 por defecto y rompe con acentos/emojis.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.bot.engine import reply_to_customer  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models import Merchant  # noqa: E402

DEMO_EMAIL = "demo@ventabot.bo"
CLIENTE_TEST = "591700000000"  # teléfono ficticio del cliente


async def main() -> None:
    if not settings.llm_api_key:
        print("⚠️  Falta LLM_API_KEY en backend/.env (Groq gratis: https://console.groq.com)")
        return

    async with AsyncSessionLocal() as session:
        merchant = (
            await session.execute(select(Merchant).where(Merchant.email == DEMO_EMAIL))
        ).scalar_one_or_none()

    if merchant is None:
        print("⚠️  No existe el merchant demo. Corré primero: uv run python scripts/seed.py")
        return

    print(f"VentaBot — chat de prueba con '{merchant.business_name}'")
    print(f"(proveedor: {settings.llm_base_url} | modelo: {settings.llm_model})")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            user = input("Tú:  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user.lower() in {"salir", "exit", "quit"}:
            break
        if not user:
            continue

        async with AsyncSessionLocal() as session:
            reply = await reply_to_customer(
                session, merchant, "whatsapp", CLIENTE_TEST, user
            )
        print(f"Bot: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())
