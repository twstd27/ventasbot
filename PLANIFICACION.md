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
