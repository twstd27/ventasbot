"""Siembra datos de prueba en la base — Fase 2.

Crea (de forma idempotente) un merchant demo con un catálogo de productos,
para poder probar el bot con consultas reales.

Uso (desde backend/):
    uv run python scripts/seed.py
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models import Merchant, Product  # noqa: E402

DEMO_EMAIL = "demo@ventabot.bo"

DEMO_PRODUCTS = [
    # (nombre, descripción, precio Bs, stock)
    ("Zapatilla deportiva Nike Air", "Zapatilla running, tallas 38-44, negro/blanco", "450.00", 12),
    ("Zapatilla urbana Adidas", "Zapatilla casual, tallas 39-43, varios colores", "380.00", 8),
    ("Polera básica algodón", "Polera unisex 100% algodón, tallas S-XL", "75.00", 30),
    ("Pantalón jean clásico", "Jean azul corte recto, tallas 28-36", "180.00", 15),
    # Casaca a propósito sin stock (0) para probar el caso de no disponibilidad.
    ("Casaca impermeable", "Casaca para lluvia con capucha, tallas M-XL", "320.00", 0),
    ("Gorra deportiva", "Gorra ajustable, talla única", "60.00", 25),
    ("Mochila urbana 20L", "Mochila resistente al agua, compartimento laptop", "240.00", 6),
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        # Merchant demo (idempotente por email)
        result = await session.execute(select(Merchant).where(Merchant.email == DEMO_EMAIL))
        merchant = result.scalar_one_or_none()

        if merchant is None:
            merchant = Merchant(
                name="Tienda Demo",
                email=DEMO_EMAIL,
                plan="basic",
                business_name="Tienda Demo Bolivia",
                business_hours="Lunes a sábado de 9:00 a 19:00",
                business_location="Av. Ballivián #123, Cochabamba",
                welcome_message="¡Hola! Bienvenido a Tienda Demo. ¿En qué puedo ayudarte?",
                whatsapp_phone_number_id="1070720369462226",  # coincide con el .env para pruebas
            )
            session.add(merchant)
            await session.flush()
            print(f"+ Merchant creado: {merchant.business_name} ({merchant.id})")
        else:
            print(f"= Merchant ya existía: {merchant.business_name} ({merchant.id})")

        # Productos (idempotente por nombre dentro del merchant)
        existing = await session.execute(
            select(Product.name).where(Product.merchant_id == merchant.id)
        )
        existing_names = {row[0] for row in existing}

        added = 0
        for name, desc, price, stock in DEMO_PRODUCTS:
            if name in existing_names:
                continue
            session.add(
                Product(
                    merchant_id=merchant.id,
                    name=name,
                    description=desc,
                    price=Decimal(price),
                    stock=stock,
                )
            )
            added += 1

        await session.commit()
        print(f"+ {added} productos agregados ({len(DEMO_PRODUCTS) - added} ya existían)")
        print(f"\nMerchant ID para pruebas: {merchant.id}")
        print(f"whatsapp_phone_number_id: {merchant.whatsapp_phone_number_id}")


if __name__ == "__main__":
    asyncio.run(main())
