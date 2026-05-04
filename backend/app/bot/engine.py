import json
from typing import Any

import anthropic

from app.bot.tools import TOOLS
from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Eres un asistente de ventas para {business_name}.
Ayudas a los clientes a consultar productos, verificar disponibilidad y realizar pedidos.
Responde siempre en español boliviano, de forma amable y concisa.
Cuando no puedas ayudar con algo, ofrece comunicar al dueño del negocio."""


async def handle_message(channel: str, channel_id: str, message: dict[str, Any]) -> None:
    # Extraer texto del mensaje según el canal
    if channel == "whatsapp":
        text = message.get("text", {}).get("body", "")
        sender_id = message.get("from", "")
    else:  # messenger
        text = message.get("message", {}).get("text", "")
        sender_id = message.get("sender", {}).get("id", "")

    if not text:
        return

    # TODO: cargar merchant desde BD usando channel_id
    # TODO: cargar historial de conversación desde Redis
    # TODO: llamar a Claude con el historial + texto nuevo
    # TODO: procesar tool calls (consultar_stock, crear_pedido, etc.)
    # TODO: enviar respuesta al cliente via Meta API

    # Placeholder — flujo completo se implementa en el siguiente sprint
    print(f"[{channel}] Mensaje de {sender_id}: {text}")


async def call_claude(
    merchant_name: str,
    history: list[dict[str, Any]],
    user_message: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Llama a Claude con el historial y retorna (respuesta, tool_calls)."""
    messages = [*history, {"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT.format(business_name=merchant_name),
        tools=TOOLS,
        messages=messages,
    )

    tool_calls = [
        {"name": block.name, "input": block.input}
        for block in response.content
        if block.type == "tool_use"
    ]

    text_response = " ".join(
        block.text for block in response.content if block.type == "text"
    )

    return text_response, tool_calls
