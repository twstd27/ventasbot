import json
from typing import Any

from openai import OpenAI

from app.bot.tools import TOOLS
from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """Eres un asistente de ventas para {business_name}.
Ayudas a los clientes a consultar productos, verificar disponibilidad y realizar pedidos.
Responde siempre en español boliviano, de forma amable y concisa.
Cuando no puedas ayudar con algo, ofrece comunicar al dueño del negocio."""


async def handle_message(channel: str, channel_id: str, message: dict[str, Any]) -> None:
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
    # TODO: procesar tool calls (consultar_stock, crear_pedido, etc.)
    # TODO: enviar respuesta al cliente via Meta API

    print(f"[{channel}] Mensaje de {sender_id}: {text}")


def call_ai(
    merchant_name: str,
    history: list[dict[str, Any]],
    user_message: str,
) -> tuple[str, list[dict[str, Any]]]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(business_name=merchant_name)},
        *history,
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    ai_message = response.choices[0].message

    tool_calls = []
    if ai_message.tool_calls:
        tool_calls = [
            {"name": tc.function.name, "input": json.loads(tc.function.arguments)}
            for tc in ai_message.tool_calls
        ]

    return ai_message.content or "", tool_calls
