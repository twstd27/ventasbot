"""Motor del bot: orquesta el loop de conversación con tool-calling.

Flujo: cargar merchant -> cargar historial -> llamar al LLM -> ejecutar tools
si las pide -> volver a llamar -> devolver respuesta final. El historial se
persiste en Postgres (tablas conversations / messages).
"""

import json
import re
from functools import lru_cache
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.tool_handlers import ToolContext, dispatch_tool
from app.bot.tools import TOOLS
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Conversation, Merchant, Message

MAX_HISTORY = 20
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """Eres un asistente de ventas para {business_name}.
Ayudas a los clientes a consultar productos, verificar disponibilidad y realizar pedidos.
Responde siempre en español boliviano, de forma amable y concisa.

FORMATO DE LOS MENSAJES (muy importante): escribes por WhatsApp/Messenger, que NO
entienden Markdown. Nunca uses tablas, ni asteriscos dobles (**), ni almohadillas (#),
ni barras (|). Escribe como en un chat real: natural, cálido y breve. Para listar
productos usa una línea por producto con una viñeta simple, por ejemplo:
• Zapatilla Nike Air — Bs 450 (9 disponibles)
Puedes usar emojis con moderación. Mantén los mensajes cortos y fáciles de leer en el celular.

Usa la herramienta consultar_stock para verificar precios y disponibilidad antes de
afirmar que algo existe — nunca inventes productos, precios ni stock. Si el cliente
pregunta en general qué hay, llama a consultar_stock sin 'query' para ver el catálogo.
Si el resultado indica que hay más productos de los mostrados (hay_mas) o un total
grande, NO los listes todos: muestra unos pocos y pregúntale al cliente qué tipo o
categoría busca para acotar la búsqueda.

Antes de usar crear_pedido, muestra al cliente un resumen (productos, cantidades y
total) y espera su confirmación explícita en un mensaje aparte. Crea el pedido una
sola vez; si ya lo creaste en esta conversación, no lo vuelvas a crear.
Si te preguntan por horario, ubicación o datos del negocio, usa obtener_info_negocio.
Cuando no puedas ayudar con algo, ofrece comunicar al dueño del negocio."""


def format_for_channel(text: str, channel: str) -> str:
    """Red de seguridad: limpia Markdown que el LLM pueda colar, según el canal.

    WhatsApp usa *un asterisco* para negrita; Messenger no soporta formato, se quita.
    Ni WhatsApp ni Messenger renderizan encabezados (#) ni negrita doble (**).
    """
    if not text:
        return text
    # Quitar encabezados Markdown (#, ##, ...).
    text = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]*", "", text, flags=re.MULTILINE)
    # Tablas Markdown: quitar filas separadoras (|---|:--:|) y convertir filas
    # "| a | b | c |" en texto natural "a — b — c".
    text = re.sub(r"^[ \t]*\|?[ \t]*[:\- ]*-[:\- |]*$", "", text, flags=re.MULTILINE)

    def _table_row(m: re.Match[str]) -> str:
        cells = [c.strip() for c in m.group(0).strip().strip("|").split("|")]
        return " — ".join(c for c in cells if c)

    text = re.sub(r"^[ \t]*\|.+\|[ \t]*$", _table_row, text, flags=re.MULTILINE)
    # Negrita doble -> WhatsApp: *texto*; otros canales: sin marca.
    bold = r"*\1*" if channel == "whatsapp" else r"\1"
    text = re.sub(r"\*\*(.+?)\*\*", bold, text)
    text = re.sub(r"__(.+?)__", bold, text)
    # Colapsar líneas en blanco de más.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@lru_cache
def get_client() -> AsyncOpenAI:
    """Cliente async compatible con la API de OpenAI (OpenAI, Groq, Gemini...)."""
    return AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


# ── Carga de datos ──────────────────────────────────────────────────────────

async def load_merchant_by_channel(
    session: AsyncSession, channel: str, channel_id: str
) -> Merchant | None:
    if channel == "whatsapp":
        stmt = select(Merchant).where(Merchant.whatsapp_phone_number_id == channel_id)
    else:  # messenger
        stmt = select(Merchant).where(Merchant.messenger_page_id == channel_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_or_create_conversation(
    session: AsyncSession, merchant: Merchant, channel: str, external_id: str
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.merchant_id == merchant.id,
        Conversation.channel == channel,
        Conversation.external_id == external_id,
    )
    conv = (await session.execute(stmt)).scalar_one_or_none()
    if conv is None:
        conv = Conversation(merchant_id=merchant.id, channel=channel, external_id=external_id)
        session.add(conv)
        await session.flush()
    return conv


async def load_history(
    session: AsyncSession, conversation: Conversation, limit: int = MAX_HISTORY
) -> list[dict[str, str]]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed((await session.execute(stmt)).scalars().all()))
    return [{"role": m.role, "content": m.content} for m in rows]


# ── Loop de conversación ────────────────────────────────────────────────────

async def run_conversation(
    session: AsyncSession,
    merchant: Merchant,
    conversation: Conversation,
    history: list[dict[str, Any]],
    user_message: str,
) -> str:
    """Ejecuta el ciclo LLM <-> tools y devuelve la respuesta final en texto."""
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(business_name=merchant.business_name or merchant.name),
        },
        *history,
        {"role": "user", "content": user_message},
    ]

    ctx = ToolContext(session=session, merchant=merchant, conversation=conversation)
    client = get_client()

    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        # Registrar la intención de usar tools y ejecutarlas.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = await dispatch_tool(tc.function.name, args, ctx)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    # Si se agotaron las rondas, una última respuesta sin tools.
    response = await client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=1024,
        messages=messages,
    )
    return response.choices[0].message.content or ""


async def reply_to_customer(
    session: AsyncSession,
    merchant: Merchant,
    channel: str,
    external_id: str,
    user_text: str,
) -> str:
    """Punto único de entrada: maneja conversación + persistencia del historial."""
    conv = await get_or_create_conversation(session, merchant, channel, external_id)
    history = await load_history(session, conv)
    reply = await run_conversation(session, merchant, conv, history, user_text)

    session.add(Message(conversation_id=conv.id, role="user", content=user_text))
    session.add(Message(conversation_id=conv.id, role="assistant", content=reply))
    await session.commit()
    return reply


# ── Entrada desde webhooks (vía Celery) ─────────────────────────────────────

async def handle_message(channel: str, channel_id: str, message: dict[str, Any]) -> None:
    if channel == "whatsapp":
        text = message.get("text", {}).get("body", "")
        sender_id = message.get("from", "")
    else:  # messenger
        text = message.get("message", {}).get("text", "")
        sender_id = message.get("sender", {}).get("id", "")

    if not text:
        return

    async with AsyncSessionLocal() as session:
        merchant = await load_merchant_by_channel(session, channel, channel_id)
        if merchant is None:
            print(f"[{channel}] Sin merchant para channel_id={channel_id!r}; mensaje ignorado.")
            return

        reply = await reply_to_customer(session, merchant, channel, sender_id, text)
        print(f"[{channel}] {sender_id} -> {text!r}")
        print(f"[{channel}] bot  -> {reply!r}")

        # Enviar la respuesta de vuelta al cliente (limpia Markdown según el canal).
        if not reply:
            return
        reply = format_for_channel(reply, channel)
        if channel == "whatsapp":
            from app.services.whatsapp import send_whatsapp_text

            try:
                await send_whatsapp_text(phone_number_id=channel_id, to=sender_id, text=reply)
                print(f"[{channel}] respuesta enviada a {sender_id}.")
            except Exception as exc:  # no romper el webhook si Meta falla
                print(f"[{channel}] ERROR al enviar respuesta: {exc}")
        else:  # messenger: envío pendiente (requiere page access token)
            print(f"[{channel}] envío saliente aún no implementado; respuesta no enviada.")
