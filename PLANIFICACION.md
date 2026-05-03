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
- [x] Panel admin para el comerciante
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
                               │
┌──────────────────────────────▼──────────────────────────┐
│                   BACKEND PRINCIPAL                     │
│                  Python + FastAPI                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ Bot Engine  │  │  Stock API  │  │  Payment API   │  │
│  │ (IA + flow) │  │  (consulta) │  │  (QR Bolivia)  │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                   BASE DE DATOS                         │
│    PostgreSQL (stock, pedidos, clientes, config)        │
│    Redis (contexto de conversaciones activas)           │
└─────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                   PANEL ADMIN                           │
│              Next.js + shadcn/ui                       │
│    (cargar catálogo, ver conversaciones, pedidos)       │
└─────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Backend
- **Lenguaje**: Python 3.12+
- **Framework**: FastAPI
- **Base de datos**: PostgreSQL (Supabase para MVP)
- **Caché / sesiones**: Redis
- **IA**: Claude API (Anthropic) con function calling — el bot llama la API de stock como herramienta

### Frontend (Panel Admin)
- **Framework**: Next.js 14 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **Auth**: Supabase Auth

### Mensajería
- **WhatsApp**: Meta Cloud API (WhatsApp Business Platform)
  - Cada comerciante conecta su propio número via **Embedded Signup**
  - Cada uno tiene su propia WABA (WhatsApp Business Account)
  - Evita baneos cruzados y cumple con políticas de Meta
- **Messenger**: Meta Webhooks (directo, sin costo adicional)

### Infraestructura (MVP)
- **Backend**: Railway o Render
- **Frontend**: Vercel
- **DB**: Supabase
- **Costo estimado MVP**: ~$30-50 USD/mes

---

## WhatsApp: Un Número por Comerciante

Esta es la decisión correcta por varias razones:

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

## Pagos en Bolivia

### Panorama de pagos QR en Bolivia

Bolivia tiene un ecosistema QR maduro e interoperable desde 2021, impulsado por el BCB.

### Opciones de integración (en orden de recomendación)

#### 1. OpenBCB (prioritario)
- Plataforma de pagos del Banco Central de Bolivia
- **Gratis** para integración
- QR interoperable con todos los bancos y billeteras del país
- Lanzado en 2025, orientado a desarrolladores
- Contacto: https://www.bcb.gob.bo (sección Sistema de Pagos → OPEN BCB)

#### 2. $imple (ASOBAN)
- Sistema QR de la Asociación de Bancos Privados de Bolivia
- Interoperable entre todos los bancos privados
- Muy adoptado en comercios físicos

#### 3. Tigo Money
- Billetera móvil dominante en Bolivia
- Tiene API (requiere partnership directo)
- Librería PHP disponible en GitHub: `saulmoralespa/tigo-money-api-php`
- Muy usado en zonas rurales y por personas sin cuenta bancaria

#### 4. dLocal
- Gateway internacional que opera en Bolivia
- Documentación: https://docs.dlocal.com/docs/bolivia
- Soporta QR, tarjetas y pagos instantáneos
- Buena opción si queremos expandirnos a otros países después

#### 5. EBANX + Pagosnet
- Integración con Sintesis (55% del comercio digital boliviano usa sus centros de pago)
- Soporta QR y más de 1,600 puntos de pago en efectivo

### Flujo de pago QR en el bot

```
Cliente: "Quiero comprar 2 unidades de X"
Bot: Confirma disponibilidad en stock → genera QR de cobro → envía imagen QR por WhatsApp
Cliente: Escanea QR con app bancaria / Tigo Money
Sistema: Webhook de confirmación de pago → bot notifica al comerciante y al cliente
Bot: "¡Pago confirmado! Tu pedido #123 está siendo preparado."
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
Cliente hace consulta (texto libre en español)
        │
        ▼
IA interpreta intención:
  ├── Consulta de stock → llama Stock API → responde con disponibilidad y precio
  ├── Intención de compra → inicia flujo de pedido
  ├── Pregunta sobre horarios/ubicación → responde con datos del negocio
  └── No entiende → ofrece hablar con humano
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

## Panel Admin (Funcionalidades)

### MVP
- [ ] Cargar/editar catálogo de productos (nombre, precio, stock, imagen)
- [ ] Ver conversaciones activas
- [ ] Ver pedidos recibidos y su estado
- [ ] Configurar datos del negocio (nombre, horario, ubicación, mensaje de bienvenida)
- [ ] Conectar número de WhatsApp (Embedded Signup)
- [ ] Ver historial de pagos

### v2
- [ ] Tomar conversaciones manualmente (handoff humano)
- [ ] Reportes básicos (ventas por día, productos más consultados)
- [ ] Importar catálogo por CSV
- [ ] Múltiples usuarios del panel (dueño + empleados)

---

## Modelo de Negocio

### Precios (en BOB para Bolivia)

| Plan | Precio | Conversaciones/mes | Incluye |
|------|--------|---------------------|---------|
| **Gratis** | Bs. 0 | 100 | Solo Messenger |
| **Básico** | Bs. 130/mes (~$19) | 500 | WhatsApp + Messenger, catálogo hasta 50 productos |
| **Pro** | Bs. 340/mes (~$49) | 2,000 | Todo lo anterior + handoff humano, catálogo ilimitado, reportes |

### Principios del modelo de pago
- Precio predecible (por mes, no por mensaje)
- El costo de la IA y WhatsApp API está absorbido en el precio
- Trial de 14 días sin tarjeta de crédito
- Pago vía QR Bolivia (el cliente también puede pagar con QR)

### Estimación de costos por comerciante (plan Básico, 500 conversaciones)
- Claude API (~500 llamadas): ~$3-5 USD
- WhatsApp Cloud API (conversaciones iniciadas por usuario: gratuitas en su mayoría): ~$2-4 USD
- Infraestructura prorrateada: ~$3 USD
- **Costo total estimado**: ~$8-12 USD → precio $19 USD → margen ~40-50%

---

## Cosas Importantes No Obvias

### Técnicas
- **Contexto de conversación**: Cada conversación necesita memoria del historial reciente para que el bot sea coherente. Redis es ideal para esto con TTL de ~24h.
- **Rate limits de Meta**: WhatsApp tiene límites de mensajes por tier. Los números nuevos empiezan en Tier 1 (1,000 conversaciones únicas/día) y escalan con el tiempo.
- **Webhooks de pago**: La confirmación de pago QR es asíncrona. El sistema tiene que manejar bien los estados (pendiente → confirmado → fallido).
- **Imágenes del catálogo**: WhatsApp soporta envío de imágenes, pero tienen límites de tamaño. Las imágenes del catálogo deben estar optimizadas.

### De negocio
- **Onboarding guiado**: El comerciante promedio en Bolivia no es técnico. El proceso de configurar WhatsApp + cargar catálogo tiene que ser de menos de 15 minutos.
- **Soporte en español boliviano**: Los templates de WhatsApp y los mensajes del bot deben sonar naturales para Bolivia (no genérico).
- **Verificación de negocio de Meta**: Para usar WhatsApp Business API, Meta puede pedir verificación del negocio. Hay que guiar al comerciante en este proceso.
- **Prueba con comerciantes reales**: Antes de lanzar, validar con 3-5 comerciantes reales (almacenes, tiendas de ropa, licorerías, etc.)

---

## Lo que NO vamos a hacer (por ahora)

- App móvil
- Integración con ERPs o sistemas de facturación complejos
- Soporte para más de 2 canales
- Analytics avanzado
- Multiidioma
- Pagos con tarjeta de crédito (el mercado es QR)
- Voz o notas de audio

---

## Hoja de Ruta

### Fase 1 — MVP (estimado: 10-12 semanas)
- [ ] Backend FastAPI + PostgreSQL + Redis
- [ ] Integración WhatsApp Cloud API (multi-tenant)
- [ ] Bot con IA (Claude API + function calling para stock)
- [ ] Panel admin básico (Next.js)
- [ ] Integración pago QR (OpenBCB o dLocal)
- [ ] 1-2 comerciantes piloto reales en Bolivia

### Fase 2 — Producto (estimado: +8 semanas)
- [ ] Handoff humano (el comerciante toma la conversación)
- [ ] Messenger como canal adicional
- [ ] Importación de catálogo por CSV
- [ ] Reportes básicos de ventas
- [ ] Sistema de suscripción y cobro automático

### Fase 3 — Escala
- [ ] Onboarding self-service completo
- [ ] Integración con Tienda Nube / WooCommerce
- [ ] Expansión a otros países de Latam
- [ ] Marketplace de plantillas de respuesta

---

## Preguntas Abiertas

- [ ] ¿Qué gateway QR vamos a integrar primero? (OpenBCB requiere registro directo con el BCB)
- [ ] ¿El comerciante usa un número que ya tiene, o VentaBot provee el número?
- [ ] ¿Cómo manejamos el inventario cuando el stock llega a 0 mid-conversación?
- [ ] ¿Quién maneja el soporte al comerciante cuando algo falla?

---

## Repositorio y Estructura del Proyecto

```
ventasbot/
├── backend/          # FastAPI
│   ├── app/
│   │   ├── bot/      # Lógica del bot e IA
│   │   ├── api/      # Endpoints REST
│   │   ├── models/   # Modelos de BD
│   │   └── integrations/
│   │       ├── whatsapp/
│   │       ├── messenger/
│   │       └── payments/
│   └── tests/
├── frontend/         # Next.js (panel admin)
│   ├── app/
│   └── components/
├── PLANIFICACION.md  # Este documento
└── README.md
```

---

*VentaBot — Hecho para los que venden, no para los que programan.*
