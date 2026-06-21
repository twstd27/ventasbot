# VentaBot — Diagnóstico y Plan de Continuación

> Documento generado el 2026-06-17 como punto de partida para retomar el proyecto.
> Contexto: el proyecto fue iniciado con ayuda de ChatGPT pero quedó incompleto.
> A partir de aquí se continúa con Claude Code.

---

## 0. Retomar el proyecto en otra máquina (Windows ↔ macOS)

El repo es portable. La base de datos vive en Supabase (nube), así que es la misma
desde cualquier máquina. Lo único que **no** está en git (por seguridad) es `.env`
(secretos) y `.venv` (se regenera).

```bash
git clone https://github.com/twstd27/ventasbot.git
cd ventasbot/backend
uv sync                       # recrea el entorno desde uv.lock
cp .env.example .env          # luego llenar con los valores reales (ver abajo)
uv run alembic upgrade head   # idempotente: el schema ya está en Supabase
uv run python scripts/seed.py # opcional: datos demo (idempotente)
uv run python scripts/chat.py # probar el bot
```

**Pasar el `.env` a la otra máquina a mano** (AirDrop / gestor de contraseñas /
copy-paste — NUNCA por git). Variables a completar: `DATABASE_URL` (usar el Session
Pooler IPv4, ver comentario en `.env.example`), `LLM_API_KEY`, `META_*`,
`WHATSAPP_*`, `SUPABASE_*`, `SECRET_KEY`.

En macOS instalar `uv` con `brew install uv` (o el instalador oficial) y Python 3.12.

---

## 1. Estado actual del proyecto

### Completado (~10-15% de implementación real)

| Área | Estado | Detalle |
|------|--------|---------|
| Planificación | ✅ Completo | `PLANIFICACION.md` con visión, stack, arquitectura, modelo de negocio |
| Modelos ORM | ✅ Completo | Merchant, Product, Conversation, Message, Order, OrderItem |
| Configuración | ✅ Completo | `config.py` con pydantic-settings, `.env.example` |
| Estructura de proyecto | ✅ Completo | FastAPI + Next.js App Router + Docker Compose |
| Webhooks | ✅ Scaffolded | Endpoints de WhatsApp y Messenger registrados, pero solo encolan |
| Celery + Redis | ✅ Scaffolded | Configurado y conectado, pero las tasks no hacen nada |
| Lógica del bot | ❌ Vacío | `engine.py` tiene solo `TODO` comments |
| Tool execution | ❌ Vacío | Las tools están definidas en `tools.py` pero no ejecutadas |
| Respuesta a Meta API | ❌ Vacío | No hay código que envíe mensajes de vuelta |
| Migraciones Alembic | ❌ No existe | La DB solo existe como modelos Python |
| Frontend | ❌ Vacío | 4 páginas con JSX stub, sin lógica, sin componentes |
| Tests | ❌ No existe | pyproject.toml los define pero no hay archivos |

### Problemas de código identificados

1. **CORS demasiado abierto**: `allow_origins=["*"]` en `main.py` — aceptable en desarrollo, debe restringirse en producción.
2. **shadcn/ui no instalado**: el plan lo requiere pero no está en `package.json` del frontend.
3. **Sin migraciones**: el schema de base de datos nunca fue aplicado a ninguna DB real.
4. **Sin variables de entorno reales**: los `.env.example` existen pero nunca se llenaron.

---

## 2. Por qué se eligió este stack (razonamiento)

### Backend: FastAPI + Celery + Redis

El motivo principal es un **requisito técnico de Meta**: los webhooks de WhatsApp Business deben responder con HTTP 200 en menos de 100ms. Una llamada a OpenAI toma 2-4 segundos. Por eso el flujo es obligatoriamente:

```
Meta envía mensaje
    → FastAPI responde 200 inmediatamente (< 100ms)
    → Encola mensaje en Redis
    → Celery Worker procesa async
        → Llama a OpenAI
        → Ejecuta tools (consultar DB)
        → Envía respuesta de vuelta a Meta
```

Si se intentara procesar el AI call dentro del webhook handler, Meta marcaría el webhook como fallido y dejaría de enviar mensajes.

### Base de datos: Supabase (PostgreSQL)

Elegido por tres razones concretas para este proyecto:
- **RLS (Row-Level Security)**: permite aislar datos de merchants sin escribir middleware de auth manualmente
- **Auth incluido**: no hay que construir sistema de login
- **Storage incluido**: para imágenes de productos

### Frontend: Next.js en Vercel

Hosting gratuito para MVP + optimización automática de imágenes de Supabase Storage. No hay razón técnica sofisticada — es el camino de menor fricción.

### AI: GPT-4o-mini (no Claude)

Decisión documentada en `PLANIFICACION.md` basada en costo:
- GPT-4o-mini: ~$0.80 USD / 500 conversaciones/mes
- Claude Haiku: ~$5 USD / 500 conversaciones/mes

Para el margen del plan Basic (Bs. 130 / ~$19 USD), la diferencia es significativa. La calidad es equivalente para tareas de ventas simples.

### Infraestructura: Railway para backend

Railway soporta múltiples procesos en el mismo deploy (FastAPI server + Celery worker) sin configuración extra. Otras opciones (Render, Fly.io) requieren más trabajo para Celery.

---

## 3. Por qué el proyecto se detuvo

ChatGPT construyó el proyecto **de arriba hacia abajo**: primero la arquitectura completa, luego el scaffolding de todos los archivos. Esto produce un proyecto que "se ve completo" visualmente pero no hace nada.

El problema no fue la arquitectura — fue el orden de construcción. Cuando llegó el momento de implementar la lógica real (ejecutar tool calls, hacer queries a la DB, enviar respuestas a Meta), la complejidad acumulada era demasiada para abordar sin entender cada pieza.

---

## 4. Plan de continuación (enfoque bottom-up)

El enfoque nuevo es **de abajo hacia arriba**: cada fase termina con algo que funciona y se puede probar antes de avanzar.

### Fase 1 — Bot mínimo funcionando en local
**Objetivo**: recibir un mensaje de texto y responder con OpenAI. Sin Docker, sin Celery, sin base de datos.

- [x] Configurar entorno local (Windows, Python 3.12, uv, variables de entorno)
- [x] Escribir lógica básica en `engine.py`: recibir texto → llamar LLM → retornar respuesta
- [x] Testear con un script simple (`scripts/chat.py`, sin webhook real de Meta todavía)
- [ ] Usar [ngrok](https://ngrok.com) para exponer local y probar con WhatsApp real

**Criterio de éxito**: recibir un WhatsApp y ver la respuesta del bot en el teléfono.

> Nota: en vez de OpenAI (pagos bloqueados hasta el lunes) se usa un proveedor
> compatible y gratis (Groq, modelo `openai/gpt-oss-120b`). El código es agnóstico:
> migrar a OpenAI es cambiar `LLM_*` en el `.env`. La prueba se hace por terminal
> en vez de teléfono, que es más rápido para iterar.

---

### Fase 2 — Bot conectado a base de datos
**Objetivo**: el bot puede consultar el catálogo real de productos.

- [x] Crear migraciones Alembic y aplicarlas a Supabase
- [x] Implementar `consultar_stock` tool: query real a `products` table
- [x] Implementar `obtener_info_negocio` tool: query a `merchants` table
- [x] Cargar y guardar historial de conversación (en Postgres, no Redis — ver nota)
- [x] Sembrar datos de prueba (`scripts/seed.py`: merchant demo con 7 productos)

**Criterio de éxito**: ✅ "¿tienen zapatillas talla 42?" devuelve Nike Air y Adidas con
precio y stock reales desde Supabase.

> Nota: el historial se persiste en Postgres (tablas `conversations`/`messages`) en
> lugar de Redis. Es más simple, una sola fuente de verdad y sirve para el dashboard
> de la Fase 4. Redis queda reservado para Celery (Fase 5).

---

### Fase 3 — Flujo de pedido completo
**Objetivo**: el bot puede crear un pedido y generar un QR de pago.

- [x] Implementar `crear_pedido` tool: insertar en `orders` + `order_items`
- [x] Integrar dLocal (sandbox) para generar QR de pago (modo SIMULADO sin credenciales)
- [x] Implementar state machine de orden: pending → paid → preparing → delivered/cancelled
- [x] Webhook de confirmación de pago de dLocal (`POST /api/v1/webhook/payment`)

**Criterio de éxito**: ✅ pedido creado (orden + items en DB), QR generado, webhook de pago
marca la orden como `paid` y descuenta stock.

> Pendiente al habilitar pagos (lunes): poner credenciales dLocal reales, validar el
> request real contra el sandbox de dLocal y verificar la firma HMAC del webhook
> entrante. El camino real ya está implementado en `app/services/payments.py` detrás
> del chequeo de credenciales; hoy corre en modo simulado.

---

### Fase 4 — Dashboard mínimo (frontend)
**Objetivo**: el merchant puede ver sus pedidos y gestionar su catálogo.

- [ ] Instalar y configurar shadcn/ui
- [ ] Integrar Supabase Auth (login con email)
- [ ] Página de catálogo: listar, crear, editar productos
- [ ] Página de pedidos: listar órdenes con estado
- [ ] Página de conversaciones: ver hilos activos

**Criterio de éxito**: un merchant puede logearse, agregar un producto, y verlo disponible en el bot.

---

### Fase 5 — Despliegue y Celery
**Objetivo**: el sistema corre en producción con el flujo async correcto.

- [ ] Activar Celery + Redis en el flujo de webhooks
- [ ] Desplegar backend en Railway (server + worker)
- [ ] Desplegar frontend en Vercel
- [ ] Configurar dominio y webhook real de Meta en producción
- [ ] Configurar RLS de Supabase correctamente

**Criterio de éxito**: un pilot merchant real usando el bot en producción.

---

## 5. Reglas de trabajo para este proyecto

1. **Entender antes de avanzar**: no se sube código que no se entiende.
2. **Cada fase debe funcionar antes de empezar la siguiente**.
3. **No agregar complejidad antes de necesitarla**: Celery se activa en Fase 5, no antes.
4. **Probar con datos reales** desde Fase 2 en adelante — no mocks.
5. **Un commit por feature** con mensaje descriptivo.

---

## 6. Archivos clave para orientarse

```
ventabot/
├── PLANIFICACION.md          # Visión completa del producto y decisiones de diseño
├── DIAGNOSTICO.md            # Este archivo — punto de partida para la continuación
├── backend/
│   ├── app/
│   │   ├── main.py           # Entry point de FastAPI
│   │   ├── config.py         # Variables de entorno (pydantic-settings)
│   │   ├── database.py       # Conexión async a PostgreSQL
│   │   ├── api/v1/
│   │   │   └── webhooks.py   # Endpoints de WhatsApp y Messenger
│   │   ├── bot/
│   │   │   ├── engine.py     # ← EMPEZAR AQUÍ (lógica del bot, todos los TODOs)
│   │   │   └── tools.py      # Definición de tools para OpenAI function calling
│   │   ├── models/           # ORM models (no tocar por ahora)
│   │   └── workers/
│   │       ├── celery_app.py # Configuración de Celery (activar en Fase 5)
│   │       └── tasks.py      # Tasks async (activar en Fase 5)
│   ├── pyproject.toml        # Dependencias Python
│   └── .env.example          # Variables de entorno necesarias
└── frontend/
    ├── app/
    │   ├── (auth)/login/     # Login page (Fase 4)
    │   └── (dashboard)/      # Dashboard pages (Fase 4)
    └── package.json
```

---

## 7. Próximo paso inmediato

Antes de escribir una línea de código, verificar el entorno en macOS:

```bash
# Verificar Python
python3 --version  # debe ser 3.12+

# Verificar uv (package manager)
uv --version  # si no existe: brew install uv

# Instalar dependencias del backend
cd backend
uv sync

# Copiar variables de entorno
cp .env.example .env
# Editar .env con: OPENAI_API_KEY real
```

El primer objetivo es que `uvicorn app.main:app --reload` levante sin errores.
