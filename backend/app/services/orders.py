"""Máquina de estados de pedidos y efectos sobre el stock.

Estados: pending -> paid -> preparing -> delivered
Cualquier estado no terminal puede pasar a cancelled.

El stock se descuenta cuando el pedido pasa a 'paid' (se confirma el pago) y
se restaura si un pedido ya pagado se cancela.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"paid", "cancelled"},
    "paid": {"preparing", "cancelled"},
    "preparing": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}


class InvalidTransition(Exception):
    """Se intentó una transición de estado no permitida."""


async def _adjust_stock(session: AsyncSession, order: Order, sign: int) -> None:
    """Aplica (sign=-1) o revierte (sign=+1) el descuento de stock del pedido."""
    items = (
        await session.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    ).scalars().all()
    for item in items:
        product = await session.get(Product, item.product_id)
        if product is not None:
            product.stock += sign * item.quantity


async def transition_order(session: AsyncSession, order: Order, new_status: str) -> Order:
    """Cambia el estado del pedido validando la transición y ajustando stock.

    No hace commit — eso queda a cargo de quien llama.
    """
    current = order.status
    if new_status == current:
        return order
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"No se puede pasar de '{current}' a '{new_status}'.")

    # Efectos sobre el stock.
    if new_status == "paid":
        await _adjust_stock(session, order, sign=-1)  # descontar
    elif new_status == "cancelled" and current in {"paid", "preparing"}:
        await _adjust_stock(session, order, sign=+1)  # devolver lo descontado

    order.status = new_status
    return order
