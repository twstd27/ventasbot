# VentaBot — Planificación del Proyecto

> Documento vivo. Se actualiza a medida que avanza la planificación.
> Última actualización: 2026-05-03

---

## Visión General

**VentaBot** es una plataforma SaaS que permite a micro y pequeños comerciantes de Bolivia (y eventualmente Latam) tener un bot de ventas impulsado por IA, conectado a su stock en tiempo real, accesible por sus clientes vía **WhatsApp** y **Messenger**.

El comerciante no necesita saber de tecnología. Carga su catálogo, conecta su número de WhatsApp, y el bot empieza a vender.

---

## Contexto de Mercado

### Competencia existente

| Producto | Enfoque | Debilidad para nuestro nicho |
|----------|---------|------------------------------|
| ManyChat | Messenger/Instagram | Sin IA real, caro para pequeños |
| WATI | WhatsApp empresarial | Orientado a medianas empresas |
| Treble.ai | WhatsApp Latam | Sin gestión de stock |
| Botmaker | Latam enterprise | Demasiado caro |
| Tidio | E-commerce web | Sin WhatsApp/Messenger nativo |

**Oportunidad**: Nadie está bien posicionado para el micro/pequeño comerciante boliviano con un producto simple, barato, en español, con pagos QR locales.

---

## Decisiones de Producto (confirmadas)

- [x] WhatsApp desde el inicio (no es opcional, es el canal principal en Bolivia)
- [x] **Un número de WhatsApp por comerciante** (no número compartido)
- [x] Messenger como canal secundario
- [x] IA con acceso a stock en tiempo real
- [x] Panel admin PWA (no app nativa — webapp responsiva instalable desde el navegador)
- [x] Pagos QR (el método dominante en Bolivia)
- [x] Mercado inicial: Bolivia

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTES FINALES                     │
│              WhatsApp        Messenger                  │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │
┌──────────────────▼──────────────────▼───────────────────┐
│                  CAPA DE MENSAJERÍA                     │
│         Meta Cloud API (WhatsApp Business Platform)     │
│               Meta Webhooks (Messenger)                 │
└──────────────────────────────┬──────────────────────────┘
                               │ webhook POST
┌──────────────────────────────▼──────────────────────────┐
│              FastAPI — responde 200 en <100ms           │
│                     encola en Redis                     │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                   CELERY WORKER                         │
│   Claude API (tool use) → Stock / Pedidos / QR         │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│  PostgreSQL (Supabase) — RLS por merchant_id            │
│  Redis — cola Celery + contexto de conversaciones 24h   │
│  Supabase Storage — imágenes de catálogo                │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│  Next.js 14 PWA (Vercel) + shadcn/ui + Tailwind         │
│  Panel admin — mobile-first, instalable sin App Store   │
└─────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Backend
- **Lenguaje**: Python 3.12+
- **Framework**: FastAPI — monolito modular (no microservicios en MVP)
- **Base de datos**: PostgreSQL (Supabase) — schema compartido + `merchant_id` en todas las tablas + RLS
- **Caché / sesiones**: Redis — doble uso: contexto de conversaciones (TTL 24h) + cola de tareas Celery
- **Cola de tareas**: Celery + Redis — webhooks responden 200 inmediatamente, workers procesan en async
- **IA**: Claude API (`claude-sonnet-4-6`) con tool use nativo — sin LangChain
- **Almacenamiento de imágenes**: Supabase Storage (MVP) → Cloudinary en Fase 2
- **Gestor de dependencias**: `uv` + `pyproject.toml`

### Frontend (Panel Admin)
- **Framework**: Next.js 14 (App Router) — **PWA** (manifest + service worker en Fase 2)
- **UI**: shadcn/ui + Tailwind CSS
- **Auth**: Supabase Auth
- **Instalación**: El comerciante la agrega al home de su celular desde el navegador, sin App Store

### Mensajería
- **WhatsApp**: Meta Cloud API (WhatsApp Business Platform)
  - Cada comerciante conecta su propio número via **Embedded Signup**
  - Cada uno tiene su propia WABA (WhatsApp Business Account)
  - Evita baneos cruzados y cumple con políticas de Meta
- **Messenger**: Meta Webhooks + Page Access Token por página (OAuth, sin contraseña)

### Infraestructura (MVP)
- **Backend**: Railway (soporte nativo para workers Celery)
- **Frontend**: Vercel
- **DB**: Supabase
- **Costo estimado MVP**: ~$30-50 USD/mes

---

## Decisión: Proveedor de IA — Claude vs ChatGPT (OpenAI)

### Comparativa de costos

| Modelo | Input ($/MTok) | Output ($/MTok) | Costo est. 500 conv/mes |
|--------|----------------|-----------------|--------------------------|
| **GPT-4o mini** (OpenAI) | $0.15 | $0.60 | **~$0.80 USD** |
| Claude Haiku 4.5 (Anthropic) | $0.80 | $4.00 | ~$5.00 USD |
| GPT-4o (OpenAI) | $2.50 | $10.00 | ~$15.00 USD |
| Claude Sonnet 4.6 (Anthropic) | $3.00 | $15.00 | ~$20.00 USD |

> Estimación: 8 turnos/conversación × ~500 tokens input + ~200 tokens output por turno.

### Recomendación: **GPT-4o mini para el MVP**

**GPT-4o mini es ~6x más barato que Claude Haiku** para el mismo volumen. Para un bot de ventas con tool use simple (consultar stock, crear pedido, info del negocio), GPT-4o mini es completamente suficiente:

- ✅ Function calling / tool use: excelente
- ✅ Español natural: muy bueno
- ✅ Latencia: rápida (~1–2s)
- ✅ Contexto: 128K tokens
- ✅ API confiable con alta disponibilidad

**Impacto en el margen (plan Básico, 500 conv/mes):**

| Modelo | Costo IA | Costo total est. | Precio | Margen |
|--------|----------|-----------------|--------|--------|
| GPT-4o mini | ~$0.80 | ~$5–7 USD | $19 USD | **~60–70%** |
| Claude Haiku 4.5 | ~$5.00 | ~$10–12 USD | $19 USD | ~40–50% |

### Cuándo subir de modelo

- Alta tasa de malentendidos o respuestas incorrectas del bot en producción
- Catálogos muy grandes (>300 productos) donde el contexto crece mucho
- Necesidad de razonamiento complejo en pedidos con múltiples condiciones

En ese caso, subir a **GPT-4o** o **Claude Sonnet 4.6** — ambos similares en calidad; elegir según precio en ese momento.

### Si preferís quedarte en el ecosistema Anthropic

Usar **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) — no Sonnet. La diferencia de calidad para consultas de ventas simples es mínima y es el Claude más económico. Cambiar el modelo es una línea de código, así que la decisión no es irreversible:

```python
# bot/engine.py
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
# Alternativas: "claude-haiku-4-5-20251001", "gpt-4o", "claude-sonnet-4-6"
```

---

## Por qué Supabase

Sí, Supabase es la elección correcta para VentaBot. Aquí el razonamiento concreto.

### Lo que reemplaza en un solo servicio

| Necesidad | Con Supabase | Sin Supabase |
|-----------|-------------|--------------|
| PostgreSQL | ✅ incluido | RDS / PlanetScale → +$15–30/mes |
| Auth (JWT, OAuth, magic link) | ✅ incluido | Auth0 / Clerk → +$25/mes |
| Storage de imágenes (catálogo) | ✅ incluido | S3 → costos variables |
| RLS multi-tenant | ✅ nativo en Postgres | Filtrar manualmente en cada query del backend |
| Realtime (updates en panel admin) | ✅ incluido | Socket.io / Pusher → +$25/mes |

**El free tier cubre todo el desarrollo y los primeros comerciantes piloto sin costo.**

### El killer feature: RLS por merchant_id

VentaBot es multi-tenant — todos los comerciantes comparten la misma base de datos pero cada uno solo puede ver sus propios datos. Con RLS de Supabase, esto se implementa **una sola vez** a nivel de base de datos:

```sql
-- Una política protege todos los datos de un comerciante automáticamente
CREATE POLICY "aislamiento_por_comerciante" ON products
  FOR ALL USING (merchant_id = (auth.jwt() ->> 'merchant_id')::uuid);
```

Sin RLS, hay que agregar `WHERE merchant_id = ?` en **cada query del backend** — docenas de puntos donde un bug puede filtrar datos de otro comerciante. Es un riesgo de seguridad real en un SaaS multi-tenant.

### Costos de Supabase

| Tier | Precio | DB | Storage | Cuándo usarlo |
|------|--------|----|---------|-|
| Free | $0/mes | 500 MB | 1 GB | Desarrollo + pilotos |
| Pro | $25/mes | 8 GB | 100 GB + backups diarios | Cuando haya comerciantes pagando |

El Pro ($25/mes) ya está contemplado en el estimado de infraestructura de $30–50/mes.

### Consideraciones importantes

- **Vendor lock-in**: Supabase Auth y Storage crean dependencia. Migrar en el futuro tiene costo, pero es manejable. Para el MVP no es un problema real.
- **Redis sigue siendo necesario**: Supabase no reemplaza Redis. Redis hace dos cosas distintas: cola de tareas Celery + contexto de conversaciones con TTL 24h.
- **Connection pooling**: En producción activar **PgBouncer** (incluido en el plan Pro de Supabase) para pooling de conexiones — importante con múltiples Celery workers.
- **Realtime para pedidos**: Los updates en tiempo real de nuevos pedidos en el panel admin se pueden implementar con Supabase Realtime sin infraestructura adicional.

### Veredicto

Sí, usar Supabase. Simplifica el stack, el free tier es generoso para el MVP, y el RLS por `merchant_id` es exactamente lo que necesita un SaaS multi-tenant. La única alternativa sería gestionar Postgres + Auth + Storage por separado, lo cual agrega complejidad y costo sin beneficios reales en esta etapa.

---

## Cómo correr el proyecto localmente

### Requisitos previos
- Python 3.12+ (instalar con `uv python install 3.12`)
- Node.js 18+ y npm
- Docker Desktop (para Redis en desarrollo)
- `uv` instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Backend
```bash
cd backend
cp .env.example .env        # completar variables
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"

# Terminal 1 — API
uvicorn app.main:app --reload

# Terminal 2 — Worker
celery -A app.workers.celery_app worker --loglevel=info

# O todo junto con Docker
cd .. && docker compose up
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local   # completar variables
npm install
npm run dev                         # corre en http://localhost:3000
```

### Exponer webhook para desarrollo
```bash
# Instalar ngrok si no lo tienes
brew install ngrok
ngrok http 8000
# Copiar la URL https://xxxx.ngrok.io y configurarla en Meta Developer Console
```

---

## WhatsApp: Un Número por Comerciante

1. **Aislamiento de reputación**: Si un comerciante tiene problemas con Meta, no afecta a los demás
2. **Identidad de marca**: El número pertenece al negocio, no a VentaBot
3. **Cumplimiento de políticas**: Meta requiere que cada WABA represente un negocio real
4. **Escalabilidad**: La Meta Cloud API soporta multi-tenant nativamente

### Flujo de onboarding de WhatsApp
```
1. Comerciante entra al panel admin
2. Inicia "Embedded Signup" de Meta (OAuth-like, directo en nuestro panel)
3. Conecta su número existente o registra uno nuevo
4. VentaBot obtiene el token de acceso de esa WABA
5. El bot ya puede recibir y enviar mensajes desde ese número
```

---

## Requisitos Meta Business Platform

### Lo que VentaBot necesita hacer (una sola vez como plataforma)

#### Paso 1 — Verificación de negocio de Meta ⚠️ pendiente empresa
- Crear cuenta en Meta Business Manager (business.facebook.com)
- Documentos: registro legal de la empresa, dirección física, teléfono del negocio
- Meta acepta empresas de Bolivia y Latam
- **Tiempo**: 1-5 días hábiles — **bloquea el lanzamiento, iniciar en cuanto haya empresa**

#### Paso 2 — Meta App de desarrollo (se puede hacer ya)
- Crear app en developers.facebook.com → tipo "Business"
- Agregar productos: WhatsApp + Messenger
- Usar el número de prueba gratuito de Meta para sandbox
- Configurar webhook con ngrok mientras se desarrolla

#### Paso 3 — Permisos avanzados (requieren app verificada)

| Canal | Permiso | Para qué |
|-------|---------|---------|
| WhatsApp | `whatsapp_business_management` | Embedded Signup de comerciantes |
| WhatsApp | `whatsapp_business_messaging` | Enviar/recibir mensajes |
| Messenger | `pages_messaging` | Mensajes en páginas de terceros |

> Revisión de Meta: descripción del caso de uso + video demo + política de privacidad pública.

### Pricing WhatsApp Cloud API

| Tipo de conversación | Costo |
|---------------------|-------|
| Iniciada por el usuario (service) | Gratis primer mes; luego ~$0.01-0.06 |
| Iniciada por el negocio (marketing/utility) | ~$0.05-0.08 por conversación |

### Tiers de mensajes (números nuevos)

| Tier | Conversaciones únicas/día |
|------|--------------------------|
| 1 (inicio) | 1,000 |
| 2 | 10,000 |
| 3 | 100,000 |

---

## Guía: Crear Cuenta Meta Business (paso a paso)

Estos son los pasos concretos para configurar VentaBot como plataforma en Meta. Hay cosas que podés hacer hoy mismo y otras que requieren empresa legal.

### Requisitos previos
- Cuenta de Facebook personal activa (la del fundador del proyecto)
- Nombre del negocio, dirección, teléfono y sitio web (puede ser el futuro landing de VentaBot)
- Documentos de la empresa **cuando esté constituida**: NIT boliviano + FUNDEMPRESA, extracto bancario o factura de servicios a nombre de la empresa

### Paso 1 — Crear la Meta Business Account *(hacer hoy)*
1. Ir a **business.facebook.com** → "Crear cuenta"
2. Completar: nombre del negocio, tu nombre completo, email de trabajo
3. Agregar método de pago (tarjeta o banco) — necesario para pagar conversaciones de WhatsApp en producción
4. Verificar el dominio del sitio web de VentaBot (meta tag HTML o registro DNS TXT)

### Paso 2 — Crear la Meta App de desarrollo *(hacer hoy)*
1. Ir a **developers.facebook.com** → "Mis apps" → "Crear app"
2. Tipo de app: **Business**
3. Vincular a la Meta Business Account recién creada
4. Agregar productos dentro de la app:
   - **WhatsApp** → para WhatsApp Cloud API
   - **Messenger** → para Messenger API
5. En WhatsApp → "Comenzar":
   - Copiar el **número de prueba gratuito** (para sandbox)
   - Copiar el **token de acceso temporal** (válido 24h — renovar manualmente durante desarrollo)
   - Copiar el **Phone Number ID** y el **WhatsApp Business Account ID**
6. Guardar en `.env`:
   ```
   META_APP_ID=...
   META_APP_SECRET=...
   WHATSAPP_TOKEN=...
   WHATSAPP_PHONE_NUMBER_ID=...
   WHATSAPP_WABA_ID=...
   WEBHOOK_VERIFY_TOKEN=una-cadena-secreta-que-tu-defines
   ```

### Paso 3 — Configurar el webhook *(hacer mientras se desarrolla)*
1. En la app de Meta → WhatsApp → Configuración → Webhooks
2. URL del webhook: `https://tu-ngrok-url/api/v1/webhooks/whatsapp`
3. Token de verificación: el `WEBHOOK_VERIFY_TOKEN` de tu `.env`
4. Suscribir a los eventos: `messages`, `message_deliveries`, `message_reads`, `message_reactions`
5. Meta hace un GET al endpoint con un `hub.challenge` — FastAPI debe responderlo:
   ```python
   @router.get("/webhooks/whatsapp")
   def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
       if hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
           return PlainTextResponse(hub_challenge)
       raise HTTPException(403)
   ```

### Paso 4 — Verificar el negocio en Meta *(requiere empresa legal constituida)*
1. En Meta Business Manager → Configuración → Información del negocio → "Verificar"
2. Documentos aceptados para Bolivia:
   - Registro de empresa FUNDEMPRESA o licencia de funcionamiento municipal
   - Extracto bancario a nombre de la empresa
   - Factura de servicios (luz, teléfono, internet) a nombre de la empresa
3. Proceso: 1–5 días hábiles
4. ⚠️ Sin esta verificación no se puede lanzar a producción ni habilitar Embedded Signup

### Paso 5 — Habilitar Embedded Signup *(requiere negocio verificado)*
Embedded Signup permite que tus comerciantes conecten su propio número de WhatsApp desde el panel admin de VentaBot, sin salir de la app.

1. En la app de Meta → WhatsApp → Configuración → "Embedded Signup"
2. Habilitar el flujo
3. Los permisos que deberás solicitar al comerciante:
   - `whatsapp_business_management`
   - `whatsapp_business_messaging`
4. Implementar el botón de Embedded Signup en el panel admin (es un botón de Facebook que abre el flujo OAuth de Meta directamente en tu UI)

### Paso 6 — Solicitar permisos avanzados para producción *(requiere app verificada)*
1. En Meta App → "Revisión de app" → "Permisos y funciones"
2. Solicitar:
   - `whatsapp_business_management` — para gestionar WABAs de comerciantes
   - `whatsapp_business_messaging` — para enviar/recibir mensajes en producción
   - `pages_messaging` — para Messenger
3. Por cada permiso adjuntar:
   - Descripción detallada del caso de uso
   - Video screencast del flujo completo (grabación de pantalla)
   - Enlace a la política de privacidad pública de VentaBot
4. Tiempo de aprobación: 3–7 días hábiles

### Resumen de tiempos

| Paso | Prerequisito | ¿Cuándo hacerlo? |
|------|--------------|------------------|
| Crear Meta Business Account | Solo cuenta de Facebook | **Hoy** |
| Crear Meta App de desarrollo | Meta Business Account | **Hoy** |
| Sandbox WhatsApp (número de prueba) | Meta App | **Hoy** |
| Verificación del negocio | Empresa legal (NIT + FUNDEMPRESA) | Cuando esté constituida |
| Embedded Signup habilitado | Negocio verificado | Post-verificación |
| Aprobación de permisos avanzados | App + negocio verificados | Post-verificación (3–7 días) |

> **Acción inmediata**: Los pasos 1, 2 y 3 se pueden hacer hoy mismo para empezar a codificar con el sandbox de Meta. La verificación del negocio se gestiona en paralelo cuando esté lista la empresa.

---

## Pagos en Bolivia

### Prioridad de integración

1. **dLocal** → MVP
2. **Tigo Money** → negociar partnership en paralelo al desarrollo
3. **OpenBCB / $imple** → post-MVP

### Requisitos por pasarela

#### 1. dLocal *(MVP)*
- Acepta empresas bolivianas y extranjeras
- **Sandbox**: disponible desde el día 1
- **Aprobación**: días
- **Costo**: ~2-3% por transacción
- **Ventaja**: cubre Latam completo para la expansión futura

#### 2. Tigo Money *(negociar ya)*
- Requiere empresa boliviana con NIT + contrato con Tigo Bolivia
- Proceso comercial: semanas o meses → contactar cuanto antes

#### 3. OpenBCB *(post-MVP)*
- Requiere NIT boliviano + registro directo con el BCB
- API no pública aún, proceso burocrático indeterminado
- Gratis, interoperable con todos los bancos

#### 4. $imple / ASOBAN *(post-MVP)*
- Acceso a través de banco miembro (Unión, BCP, Bisa)
- Sin API pública directa

### Flujo de pago QR en el bot
```
Cliente confirma pedido
→ Bot genera QR de cobro vía dLocal
→ Envía imagen QR por WhatsApp
→ Cliente escanea con app bancaria / Tigo Money
→ dLocal dispara webhook de confirmación
→ Bot notifica a comerciante y cliente
→ Estado del pedido: pending → paid
```

---

## Flujo de Conversación (Bot)

```
Cliente inicia conversación
        │
        ▼
Bot saluda + muestra categorías del catálogo
        │
        ▼
Claude interpreta mensaje (tool use):
  ├── consultar_stock     → disponibilidad y precio
  ├── crear_pedido        → inicia flujo de compra
  ├── obtener_info_negocio → horarios, ubicación
  └── sin tool            → respuesta conversacional
        │
        ▼
Flujo de pedido:
  1. Confirmación de productos y cantidades
  2. Datos de entrega (si aplica)
  3. Generación de QR de pago
  4. Confirmación de pago vía webhook
  5. Notificación a comerciante + cliente
```

---

## Modelos de Base de Datos

| Tabla | Descripción |
|-------|-------------|
| `merchants` | Comerciantes — credenciales Meta, config del negocio, plan |
| `products` | Catálogo — nombre, precio, stock, imagen |
| `conversations` | Hilo por cliente por canal (whatsapp / messenger) |
| `messages` | Historial de mensajes por conversación |
| `orders` | Pedidos — estado (pending → paid → delivering) |
| `order_items` | Ítems por pedido |

Todas las tablas tienen `merchant_id` + RLS en Supabase.

---

## Panel Admin (Funcionalidades)

### MVP
- [ ] Cargar/editar catálogo (nombre, precio, stock, imagen)
- [ ] Ver conversaciones activas
- [ ] Ver pedidos y su estado
- [ ] Configurar datos del negocio (nombre, horario, ubicación, bienvenida)
- [ ] Conectar número de WhatsApp (Embedded Signup)
- [ ] Ver historial de pagos
- [ ] Diseño responsivo mobile-first

### PWA (Fase 2)
- [ ] Web App Manifest
- [ ] Service Worker (caché, funciona con conexión lenta)
- [ ] Push notifications para nuevos pedidos

### v2
- [ ] Handoff humano (comerciante toma la conversación)
- [ ] Reportes básicos de ventas
- [ ] Importar catálogo por CSV
- [ ] Múltiples usuarios del panel

---

## Modelo de Negocio

| Plan | Precio | Conversaciones/mes | Incluye |
|------|--------|---------------------|---------|
| **Gratis** | Bs. 0 | 100 | Solo Messenger |
| **Básico** | Bs. 130/mes (~$19) | 500 | WhatsApp + Messenger, catálogo hasta 50 productos |
| **Pro** | Bs. 340/mes (~$49) | 2,000 | Todo + handoff humano, catálogo ilimitado, reportes |

### Estimación de costos (plan Básico, 500 conversaciones)
- Claude API (~500 llamadas): ~$3-5 USD
- WhatsApp Cloud API: ~$2-4 USD
- Infraestructura prorrateada: ~$3 USD
- **Costo total**: ~$8-12 USD → precio $19 USD → margen ~40-50%

---

## Cosas Importantes No Obvias

### Técnicas
- **Contexto de conversación**: Redis con TTL 24h — el bot mantiene coherencia entre mensajes
- **Webhook debe responder en <5s**: por eso Celery — FastAPI responde 200 inmediatamente
- **Rate limits de Meta**: Tier 1 = 1,000 conversaciones únicas/día, escala automático
- **Webhooks de pago asincrónicos**: estados `pending → paid → failed` — hay que manejarlos bien
- **Imágenes del catálogo**: límite 5MB en WhatsApp — optimizar antes de enviar

### De negocio
- **Onboarding en <15 minutos**: el comerciante boliviano promedio no es técnico
- **Español boliviano**: los mensajes del bot deben sonar naturales, no genéricos
- **Verificación Meta**: hay que guiar al comerciante en el proceso de verificación de su negocio
- **Pilotos reales**: validar con 3-5 comerciantes antes del lanzamiento público

---

## Lo que NO vamos a hacer (por ahora)

- App móvil nativa
- Integración con ERPs
- Más de 2 canales de mensajería
- Analytics avanzado
- Multiidioma
- Pagos con tarjeta de crédito
- Voz o notas de audio

---

## Hoja de Ruta

### Fase 1 — MVP (estimado: 10-12 semanas)
- [x] Planificación y decisiones de arquitectura
- [x] Scaffold del proyecto (backend + frontend)
- [ ] Empresa legal constituida en Bolivia
- [ ] Meta App de desarrollo configurada + webhook funcionando
- [ ] Esquema de BD en Supabase + migraciones Alembic
- [ ] Bot mínimo: recibe mensaje → Claude responde → respuesta al usuario
- [ ] Tool `consultar_stock` funcionando con BD real
- [ ] Tool `crear_pedido` + generación de QR dLocal
- [ ] Panel admin: catálogo, pedidos, conversaciones
- [ ] Auth con Supabase
- [ ] Embedded Signup de WhatsApp
- [ ] 1-2 comerciantes piloto reales en Bolivia

### Fase 2 — Producto (estimado: +8 semanas)
- [ ] Handoff humano
- [ ] Messenger como canal adicional
- [ ] Importación de catálogo por CSV
- [ ] Reportes básicos de ventas
- [ ] Sistema de suscripción y cobro automático
- [ ] PWA: manifest + service worker + push notifications
- [ ] Cloudinary para optimización de imágenes

### Fase 3 — Escala
- [ ] Onboarding self-service completo
- [ ] OpenBCB / Tigo Money integrados
- [ ] Integración con Tienda Nube / WooCommerce
- [ ] Expansión a otros países de Latam
- [ ] Marketplace de plantillas de respuesta

---

## Preguntas Abiertas

- [ ] ¿El comerciante usa un número que ya tiene, o VentaBot provee el número?
- [ ] ¿Cómo manejamos el inventario cuando el stock llega a 0 mid-conversación?
- [ ] ¿Quién maneja el soporte al comerciante cuando algo falla?
- [ ] ¿Cuándo constituir la empresa legal? (necesaria para Meta + dLocal)

---

## Repositorio y Estructura del Proyecto

```
ventasbot/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Variables de entorno (pydantic-settings)
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── api/v1/
│   │   │   └── webhooks.py       # Endpoints WhatsApp + Messenger
│   │   ├── bot/
│   │   │   ├── engine.py         # Claude API + tool use
│   │   │   └── tools.py          # Definición de tools (stock, pedido, info)
│   │   ├── models/
│   │   │   ├── merchant.py
│   │   │   ├── product.py
│   │   │   ├── conversation.py   # Conversation + Message
│   │   │   └── order.py          # Order + OrderItem
│   │   └── workers/
│   │       ├── celery_app.py     # Configuración Celery
│   │       └── tasks.py          # Tareas async
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/         # Login con Supabase Auth
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/        # Resumen
│   │   │   ├── catalogo/         # Gestión de productos
│   │   │   ├── pedidos/          # Lista de pedidos
│   │   │   └── conversaciones/   # Conversaciones activas
│   │   └── layout.tsx
│   ├── public/manifest.json      # PWA manifest
│   ├── package.json
│   ├── next.config.js
│   └── .env.local.example
├── docker-compose.yml            # Redis + backend + worker
├── .gitignore
└── PLANIFICACION.md
```

---

*VentaBot — Hecho para los que venden, no para los que programan.*
