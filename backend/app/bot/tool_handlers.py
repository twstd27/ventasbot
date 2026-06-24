"""Ejecución real de las tools que el LLM puede invocar.

Cada handler recibe un ToolContext (sesión, merchant y conversación actuales)
y devuelve un dict serializable que se envía de vuelta al modelo como
resultado de la tool.

Las definiciones (schema) de estas tools viven en app/bot/tools.py.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Merchant, Order, OrderItem, Product
from app.services.payments import create_payment_qr

# Cuántos productos devolver como máximo por consulta. Con catálogos grandes,
# en vez de listar todo, el bot muestra esta cantidad y pide acotar la búsqueda.
MAX_RESULTS = 8


@dataclass
class ToolContext:
    session: AsyncSession
    merchant: Merchant
    conversation: Conversation


# Palabras que no aportan a la búsqueda de productos.
_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "para", "con",
    "por", "que", "tienen", "tiene", "hay", "quiero", "necesito", "busco",
    "talla", "tallas", "color", "colores", "modelo", "precio", "stock",
}


def _tokenize(query: str) -> list[str]:
    """Divide la consulta en términos útiles, agregando el singular simple.

    Ej: "zapatillas talla 42" -> ["zapatillas", "zapatilla"]  (matchea "Zapatilla ...")
    """
    tokens: list[str] = []
    for word in re.findall(r"\w+", query.lower()):
        if len(word) < 3 or word in _STOPWORDS:
            continue
        tokens.append(word)
        if word.endswith("s") and len(word) > 4:  # plural -> singular aproximado
            tokens.append(word[:-1])
    return list(dict.fromkeys(tokens))  # dedup conservando orden


async def consultar_stock(ctx: ToolContext, *, query: str = "") -> dict[str, Any]:
    """Busca productos del merchant por nombre/descripción.

    Sin `query` (o vacío) devuelve todo el catálogo activo, para responder a
    preguntas generales del tipo "¿qué productos tienes?".
    """
    filters = [
        Product.merchant_id == ctx.merchant.id,
        Product.is_active.is_(True),
    ]

    tokens = _tokenize(query)
    if tokens:
        conditions = []
        for tok in tokens:
            conditions.append(Product.name.ilike(f"%{tok}%"))
            conditions.append(Product.description.ilike(f"%{tok}%"))
        filters.append(or_(*conditions))

    # Total de coincidencias (para saber si hay más de las que mostramos).
    total = (
        await ctx.session.execute(
            select(func.count()).select_from(Product).where(*filters)
        )
    ).scalar() or 0

    # Mostramos solo una página: con catálogos grandes no devolvemos todo,
    # el bot pedirá al cliente que acote la búsqueda (ver hay_mas).
    productos = (
        await ctx.session.execute(
            select(Product).where(*filters).order_by(Product.stock.desc()).limit(MAX_RESULTS)
        )
    ).scalars().all()

    if not productos:
        nota = (
            "El catálogo no tiene productos activos."
            if not query
            else f"No se encontraron productos para '{query}'."
        )
        return {"total_coincidencias": 0, "mostrados": 0, "hay_mas": False, "productos": [], "nota": nota}

    resultado: dict[str, Any] = {
        "total_coincidencias": total,
        "mostrados": len(productos),
        "hay_mas": total > len(productos),
        "productos": [
            {
                "id": str(p.id),
                "nombre": p.name,
                "descripcion": p.description,
                "precio_bs": float(p.price),
                "stock": p.stock,
                "disponible": p.stock > 0,
            }
            for p in productos
        ],
    }
    if resultado["hay_mas"]:
        resultado["nota"] = (
            f"Hay {total} productos en total; se muestran {len(productos)}. "
            "Pídele al cliente que indique qué tipo o categoría busca para acotar."
        )
    return resultado


async def obtener_info_negocio(ctx: ToolContext, **_: Any) -> dict[str, Any]:
    """Devuelve la información pública del negocio."""
    m = ctx.merchant
    return {
        "nombre": m.business_name or m.name,
        "horario": m.business_hours or "No especificado",
        "ubicacion": m.business_location or "No especificada",
    }


async def crear_pedido(ctx: ToolContext, *, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Crea un pedido con los items confirmados, valida stock y calcula el total.

    No descuenta stock hasta que el pago se confirme (queda en estado 'pending').
    """
    if not items:
        return {"error": "No se recibieron items para el pedido."}

    # Validar y cargar cada producto.
    resueltos: list[tuple[Product, int]] = []
    for item in items:
        raw_id = item.get("product_id")
        cantidad = item.get("quantity")

        if not isinstance(cantidad, int) or cantidad <= 0:
            return {"error": f"Cantidad inválida para el producto {raw_id}."}

        try:
            pid = UUID(str(raw_id))
        except (ValueError, TypeError):
            return {"error": f"product_id inválido: {raw_id!r}."}

        producto = (
            await ctx.session.execute(
                select(Product).where(
                    Product.id == pid,
                    Product.merchant_id == ctx.merchant.id,
                    Product.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()

        if producto is None:
            return {"error": f"Producto {raw_id} no existe o no está disponible."}
        if producto.stock < cantidad:
            return {
                "error": "stock_insuficiente",
                "producto": producto.name,
                "solicitado": cantidad,
                "disponible": producto.stock,
            }
        resueltos.append((producto, cantidad))

    total = sum((p.price * c for p, c in resueltos), Decimal("0"))

    order = Order(
        merchant_id=ctx.merchant.id,
        conversation_id=ctx.conversation.id,
        status="pending",
        total_amount=total,
    )
    ctx.session.add(order)
    await ctx.session.flush()  # obtiene order.id

    for producto, cantidad in resueltos:
        ctx.session.add(
            OrderItem(
                order_id=order.id,
                product_id=producto.id,
                quantity=cantidad,
                unit_price=producto.price,
            )
        )

    # Generar (o simular) el QR de pago y guardarlo en el pedido.
    pago = await create_payment_qr(order, ctx.merchant)
    order.payment_reference = pago.get("reference")
    order.payment_qr_url = pago.get("qr_url")

    return {
        "pedido_id": str(order.id),
        "estado": order.status,
        "total_bs": float(total),
        "items": [
            {
                "nombre": p.name,
                "cantidad": c,
                "precio_unitario_bs": float(p.price),
                "subtotal_bs": float(p.price * c),
            }
            for p, c in resueltos
        ],
        "pago": {
            "qr_url": pago.get("qr_url"),
            "referencia": pago.get("reference"),
            "simulado": pago.get("simulado", False),
        },
        "nota": "Comparte el qr_url con el cliente para que realice el pago.",
    }


# Registro nombre-de-tool -> handler.
TOOL_HANDLERS: dict[str, Any] = {
    "consultar_stock": consultar_stock,
    "obtener_info_negocio": obtener_info_negocio,
    "crear_pedido": crear_pedido,
}


async def dispatch_tool(
    name: str,
    arguments: dict[str, Any],
    ctx: ToolContext,
) -> dict[str, Any]:
    """Ejecuta la tool pedida por el modelo y devuelve su resultado."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Tool desconocida: {name}"}
    try:
        return await handler(ctx, **arguments)
    except TypeError as exc:
        return {"error": f"Argumentos inválidos para {name}: {exc}"}
