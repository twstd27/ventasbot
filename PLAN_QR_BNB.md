# Plan de implementación — Pagos QR con BNB (Banco Nacional de Bolivia)

> Estado: **propuesta / diseño**. Basado en la doc del sandbox del BNB
> (https://www.bnb.com.bo/PortalBNB/Api/Sandbox). Complementa/reemplaza la
> integración dLocal actual (`backend/app/services/payments.py`).

## 1. Por qué BNB y qué cambia respecto a dLocal

| | dLocal (actual) | BNB QR Simple |
|---|---|---|
| Tipo | Agregador internacional | QR bancario boliviano nativo |
| QR | Devuelve **URL** de redirección | Devuelve **imagen** (array de bytes / PNG) |
| Confirmación de pago | **Webhook** (push) | **NO hay webhook** → hay que **consultar estado (polling)** |
| Auth | HMAC-SHA256 por request | **Token** (Bearer) que se obtiene y se cachea |
| Sandbox | Necesita credenciales de comercio | Endpoints Azure públicos → **probable de probar sin acceso al banco** |

**Implicación clave #1:** sin webhook, necesitamos una tarea que **pregunte
periódicamente** por el estado de los QR pendientes (depende del punto verde #3,
Celery). 

**Implicación clave #2:** el QR llega como imagen, no como link; hay que
**guardarla y enviársela al cliente** por WhatsApp (depende del punto verde #2,
respuesta del bot vía Meta API).

## 2. Endpoints del BNB (sandbox)

**Base URLs**
- Auth:  `https://clientauthenticationapiv2.azurewebsites.net/api/v1/`
- QR:    `https://qrsimpleapiv2.azurewebsites.net/api/v1/`

### 2.1 Autenticación — `POST /auth/token`
```json
// request
{ "accountId": "<encriptado por BNB>", "authorizationId": "<encriptado por BNB>" }
// response
{ "success": true, "message": "<TOKEN>" }
```
El `message` trae el token. Se usa como `Authorization: Bearer <token>` en las
siguientes llamadas. Se cachea hasta su expiración.

### 2.2 Generar QR — `POST /main/getQRWithImageAsync`
```json
// request
{
  "currency": "BOB",
  "gloss": "VB-<order_id8>",   // descripción (usamos nuestra referencia de pedido)
  "amount": "150.00",
  "singleUse": "true",          // QR de un solo uso (un pedido)
  "expirationDate": "2026-06-23"
}
// response
{
  "qr": "<array de bytes con la imagen PNG>",
  "qrCode": "<string>",
  "id": "<id del QR>",          // <-- lo guardamos para consultar estado
  "success": true,
  "message": "...",
  "code": "..."
}
```

### 2.3 Consultar estado — `POST /main/getQRStatusAsync`
```json
// request
{ "id": "<id del QR>" }
// response
{ "id": "...", "qrId": 2, "expirationDate": "..." }
```
Códigos de `qrId`: **1 = sin usar**, **2 = usado/pagado**, **3 = expirado**, **4 = error**.

### 2.4 (Opcional) Listar por fecha — `POST /main/getQRbyGenerationDateAsync`
Para conciliación/reportes.

## 3. Cómo encaja en VentaBot

Hoy el flujo es: `crear_pedido` (tool) → `create_payment_qr(order, merchant)` →
guarda `payment_qr_url` + `payment_reference` en `orders`. Mantenemos esa misma
interfaz y agregamos un **proveedor BNB** seleccionable por configuración.

### 3.1 Cambios de datos (`orders`)
- Reutilizar `payment_reference` para el **id del QR de BNB** (lo necesita el polling).
- `payment_qr_url`: guardar la imagen como **data URL base64** (`data:image/png;base64,...`)
  **o** subirla a **Supabase Storage** y guardar la URL pública. (Recomendado:
  Storage, para no inflar la fila ni el contexto del bot.)

### 3.2 Nuevo módulo `backend/app/services/payments_bnb.py`
```
_get_token()           -> token cacheado (con expiración)
create_qr(order)       -> {id, qr_image_bytes, reference, status:"pending"}
get_qr_status(qr_id)   -> "pending" | "paid" | "expired" | "error"
```

### 3.3 Selección de proveedor (`app/config.py`)
```
PAYMENT_PROVIDER = "bnb" | "dlocal" | "simulado"   (default actual: simulado)
BNB_ACCOUNT_ID, BNB_AUTHORIZATION_ID
BNB_AUTH_BASE_URL, BNB_QR_BASE_URL
```
`create_payment_qr` enruta al proveedor según `PAYMENT_PROVIDER`, conservando el
fallback a SIMULADO si algo falla (igual que hoy).

### 3.4 Confirmación de pago (sin webhook) — tarea de polling
Tarea Celery beat `poll_pending_payments` (cada ~30–60 s):
1. Trae órdenes en estado `pending` con `payment_reference` (id de QR BNB).
2. Llama `get_qr_status(id)`.
3. Si `paid` → ejecuta la **state machine** (`app/services/orders.py`) transición
   `pending → paid`, y dispara el aviso al cliente ("¡Pago recibido!").
4. Si `expired` → marca el pedido como cancelado / pide regenerar QR.

> El stock ya se descuenta al **crear** el pedido, así que `paid` no toca stock.

## 4. Plan por pasos (orden sugerido)

| Paso | Qué | Depende de | ¿Probable sin banco? |
|---|---|---|---|
| 1 | Config + `_get_token()` contra sandbox | — | ✅ (sandbox público) |
| 2 | `create_qr()` + persistir imagen (Storage) | 1 | ✅ |
| 3 | Enrutar `create_payment_qr` por `PAYMENT_PROVIDER` | 2 | ✅ |
| 4 | Enviar la imagen del QR al cliente | verde #2 (Meta send) | ⚠️ necesita tokens Meta |
| 5 | `poll_pending_payments` (confirmación) | verde #3 (Celery) | ✅ contra sandbox |
| 6 | Validación end-to-end en producción | credenciales BNB reales | ⛔ necesita banco |

**Lo bueno:** los pasos 1–3 y 5 se pueden construir y validar **ahora** contra el
sandbox del BNB, sin esperar el acceso bancario. Sólo el paso 6 (producción) y las
credenciales reales (`accountId`/`authorizationId` definitivos) dependen del banco.

## 5. Preguntas abiertas / a confirmar con el BNB
- ¿Las credenciales encriptadas del sandbox son compartidas o se solicitan? (probar
  con las del ejemplo de la doc primero).
- ¿Tiempo de expiración del token? (define la estrategia de caché).
- ¿Hay límite de polling / rate limit? (ajustar la frecuencia de la tarea).
- ¿El `amount` admite decimales como string `"150.00"`? (validar formato).
- A futuro: ¿BNB ofrece webhook/notificación para evitar polling? (no documentado).
