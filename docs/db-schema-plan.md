# VentaBot — Blueprint del modelo de datos (cimientos)

> Objetivo: definir **de una sola vez** el esquema completo para las features ya conocidas
> (productos enriquecidos, perfil de negocio, escalación, multi-tenant/planes), para no
> re-migrar después. Marcas: **[AHORA]** = parte de los cimientos · **[FUTURO]** = se agrega
> después sin rehacer lo anterior.
>
> Tipos en notación Postgres. Toda tabla nueva lleva `id UUID PK`, `created_at`, `updated_at`
> salvo que se indique. Toda tabla con datos de un negocio lleva `merchant_id UUID FK → merchants.id`
> y su política RLS por dueño (igual que las actuales).

---

## 0. Estado actual (no cambia su esencia)

| Tabla | Resumen |
|---|---|
| `merchants` | negocio + login (email) + config WhatsApp/Messenger + perfil básico + plan |
| `products` | name, description, price, stock, image_url, is_active |
| `orders` | status, total_amount, payment_qr_url, payment_reference |
| `order_items` | product_id, quantity, unit_price (snapshot) |
| `conversations` | channel, external_id, customer_name, status (active/closed/handoff) |
| `messages` | role (user/assistant), content |

---

## 1. Multi-tenant, planes y roles **[AHORA — el cimiento más crítico]**

### 1.1 `merchants` — columnas nuevas
| Campo | Tipo | Default | Por qué |
|---|---|---|---|
| `slug` | VARCHAR(60) UNIQUE | — | identificador para URLs / panel admin |
| `phone` | VARCHAR(30) | NULL | teléfono del negocio (≠ número del bot) |
| `country` | VARCHAR(2) | `'BO'` | multi-país a futuro |
| `currency` | VARCHAR(3) | `'BOB'` | moneda |
| `timezone` | VARCHAR(40) | `'America/La_Paz'` | horarios/métricas correctas |
| `subscription_status` | VARCHAR(20) | `'trialing'` | trialing / active / past_due / canceled |
| `trial_ends_at` | TIMESTAMP | NULL | fin de prueba |
| `plan` | (ya existe) | `'free'` | pasa a referenciar `plans.code` |

### 1.2 `plans` — catálogo de planes (NUEVA) **[AHORA]**
Límites como **datos**, no como código (cambiar un plan no requiere deploy).
| Campo | Tipo | Por qué |
|---|---|---|
| `code` | VARCHAR(20) UNIQUE | free / basic / pro |
| `name` | VARCHAR(60) | nombre visible |
| `price_month` | NUMERIC(10,2) | precio mensual |
| `max_products` | INTEGER | límite de productos |
| `max_conversations_month` | INTEGER | límite de chats/mes |
| `max_users` | INTEGER | usuarios por negocio |
| `channels` | JSONB | `["whatsapp","messenger"]` permitidos |
| `features` | JSONB | flags de features por plan |
| `is_active` | BOOLEAN | visible para alta |

### 1.3 `merchant_members` — usuarios y roles del negocio (NUEVA) **[AHORA]**
Separa **el negocio** del **login**. Permite dueño + vendedores con permisos distintos.
| Campo | Tipo | Por qué |
|---|---|---|
| `merchant_id` | UUID FK | negocio |
| `user_id` | UUID | referencia a `auth.users` de Supabase |
| `email` | VARCHAR(200) | acceso/invitación |
| `name` | VARCHAR(200) | nombre del miembro |
| `phone` | VARCHAR(30) | contacto (útil para vendedores) |
| `role` | VARCHAR(20) | `owner` / `seller` / `viewer` |
| `is_active` | BOOLEAN | alta/baja |
| | | UNIQUE(merchant_id, user_id) |

> Migración: por cada merchant actual se crea un `merchant_members` con rol `owner`
> usando su email. El RLS pasa a basarse en "¿soy miembro de este merchant?".

### 1.4 `platform_admins` — rol desarrollador (NUEVA) **[AHORA, mínimo]**
Para el panel de F (ver/gestionar todos los clientes).
| Campo | Tipo | Por qué |
|---|---|---|
| `user_id` | UUID UNIQUE | admin de la plataforma |
| `email` | VARCHAR(200) | identificación |
| `role` | VARCHAR(20) | `superadmin` / `support` |

---

## 2. Perfil de negocio **[AHORA]** — lo que el bot HOY inventa

### 2.1 `merchants` — columnas nuevas (identidad + entregas + contacto + pagos + bot)
**Dirección estructurada**
| Campo | Tipo | Por qué |
|---|---|---|
| `address_line` | VARCHAR(300) | calle y número |
| `city` | VARCHAR(100) | ciudad |
| `department` | VARCHAR(50) | departamento (La Paz, Santa Cruz…) |
| `address_reference` | VARCHAR(300) | "cómo llegar" / referencia |
| `latitude` | NUMERIC(9,6) | mapa / cálculo de envío [opcional] |
| `longitude` | NUMERIC(9,6) | idem |
| `maps_url` | VARCHAR(500) | link Google Maps |

**Contacto del dueño (escalación)** — desbloquea "el bot avisa al dueño"
| Campo | Tipo | Por qué |
|---|---|---|
| `owner_name` | VARCHAR(200) | a quién se escala |
| `owner_phone` | VARCHAR(30) | WhatsApp del dueño para notificar |
| `owner_email` | VARCHAR(200) | alternativa |
| `notify_on_handoff` | BOOLEAN (def true) | avisar cuando se escala |
| `notify_channel` | VARCHAR(20) | dashboard / whatsapp / email |

**Pagos aceptados** — el bot necesita saberlo
| Campo | Tipo | Por qué |
|---|---|---|
| `accepts_cash` | BOOLEAN | efectivo / contra entrega |
| `accepts_qr` | BOOLEAN | QR (ya integrado) |
| `accepts_transfer` | BOOLEAN | transferencia bancaria |
| `bank_info` | TEXT | datos de cuenta para transferencia |
| `payment_notes` | TEXT | aclaraciones de pago |

**Entregas (config general)**
| Campo | Tipo | Por qué |
|---|---|---|
| `offers_delivery` | BOOLEAN | ¿hace envíos? |
| `offers_pickup` | BOOLEAN | ¿recojo en local? |
| `free_delivery_threshold` | NUMERIC(10,2) NULL | envío gratis desde X Bs |
| `delivery_notes` | TEXT | aclaraciones |

**Config del bot** — alimenta el system prompt (mejora E)
| Campo | Tipo | Por qué |
|---|---|---|
| `bot_enabled` | BOOLEAN (def true) | pausar/activar el bot |
| `bot_instructions` | TEXT | instrucciones a medida del negocio |
| `bot_tone` | VARCHAR(20) | cercano / formal |
| `fallback_message` | TEXT | qué responde si no sabe |
| `welcome_message` | (ya existe) | saludo inicial |

### 2.2 `delivery_zones` — zonas de envío con costo (NUEVA) **[AHORA si manejas zonas]**
| Campo | Tipo | Por qué |
|---|---|---|
| `merchant_id` | UUID FK | negocio |
| `name` | VARCHAR(100) | "Zona Sur", "Centro" |
| `cost` | NUMERIC(10,2) | costo de envío |
| `est_time` | VARCHAR(50) | "30–60 min" |
| `is_active` | BOOLEAN | |
| `sort_order` | INTEGER | orden |

---

## 3. Productos **[AHORA]** — descuentos, mayoreo, variantes, vendedor, categorías

### 3.1 `products` — columnas nuevas
| Campo | Tipo | Default | Por qué |
|---|---|---|---|
| `category_id` | UUID FK → categories | NULL | organizar catálogo / bot |
| `sku` | VARCHAR(60) | NULL | código interno |
| `unit` | VARCHAR(20) | `'unidad'` | unidad / par / docena / kg |
| `compare_at_price` | NUMERIC(10,2) | NULL | precio "normal" (muestra descuento) |
| `has_variants` | BOOLEAN | false | si true, stock/precio viven en variantes |
| `seller_id` | UUID FK → merchant_members | NULL | vendedor a cargo |
| `low_stock_threshold` | INTEGER | 0 | alerta de stock bajo [opcional] |
| `sort_order` | INTEGER | 0 | orden en catálogo [FUTURO] |
| `weight_grams` | INTEGER | NULL | para cálculo de envío [FUTURO] |

> Con variantes: `products.price` pasa a ser "precio desde" y el stock real vive por variante.

### 3.2 `product_variants` — colores/tallas con stock propio (NUEVA) **[DECISIÓN — ver abajo]**
| Campo | Tipo | Por qué |
|---|---|---|
| `product_id` | UUID FK | producto padre |
| `name` | VARCHAR(120) | "Negro / M" |
| `color` | VARCHAR(50) NULL | atributo color |
| `size` | VARCHAR(50) NULL | atributo talla |
| `sku` | VARCHAR(60) NULL | código variante |
| `price` | NUMERIC(10,2) NULL | override (NULL = precio del producto) |
| `stock` | INTEGER (def 0) | stock por variante |
| `image_url` | VARCHAR(500) NULL | foto de la variante |
| `is_active` | BOOLEAN | |
| `sort_order` | INTEGER | |

### 3.3 `price_tiers` — precio por mayor (NUEVA) **[AHORA]**
| Campo | Tipo | Por qué |
|---|---|---|
| `product_id` | UUID FK | (o `variant_id`) |
| `min_qty` | INTEGER | desde cuántas unidades |
| `unit_price` | NUMERIC(10,2) | precio unitario en ese tramo |
| `label` | VARCHAR(60) NULL | "Por mayor (12+)" |
| | | UNIQUE(product_id, min_qty) |

### 3.4 `categories` — categorías de catálogo (NUEVA) **[AHORA, recomendado]**
| Campo | Tipo | Por qué |
|---|---|---|
| `merchant_id` | UUID FK | |
| `name` | VARCHAR(100) | "Poleras", "Gorras" |
| `sort_order` | INTEGER | |
| `is_active` | BOOLEAN | |

---

## 4. Pedidos **[AHORA]** — reflejar descuentos, variantes, vendedor, entrega

### 4.1 `orders` — columnas nuevas
| Campo | Tipo | Default | Por qué |
|---|---|---|---|
| `subtotal` | NUMERIC(10,2) | — | antes de descuento/envío |
| `discount_total` | NUMERIC(10,2) | 0 | descuento aplicado |
| `delivery_method` | VARCHAR(20) | NULL | delivery / pickup |
| `delivery_zone_id` | UUID FK → delivery_zones | NULL | zona elegida |
| `delivery_cost` | NUMERIC(10,2) | 0 | costo de envío |
| `delivery_address` | TEXT | NULL | dirección de entrega |
| `customer_name` | VARCHAR(200) | NULL | snapshot |
| `customer_phone` | VARCHAR(30) | NULL | snapshot |
| `seller_id` | UUID FK → merchant_members | NULL | quién cerró la venta |
| `payment_method` | VARCHAR(20) | NULL | qr / cash / transfer |
| `notes` | TEXT | NULL | observaciones |
| `total_amount` | (ya existe) | | = subtotal − descuento + envío |

### 4.2 `order_items` — columnas nuevas
| Campo | Tipo | Por qué |
|---|---|---|
| `variant_id` | UUID FK → product_variants NULL | variante comprada |
| `product_name` | VARCHAR(200) | snapshot del nombre (sobrevive a borrado) |
| `variant_name` | VARCHAR(120) NULL | snapshot de la variante |
| `discount_amount` | NUMERIC(10,2) def 0 | descuento de la línea |
| `unit_price` | (ya existe) | snapshot de precio |

---

## 5. Escalación / handoff al dueño **[AHORA]**

### 5.1 `conversations` — columnas nuevas
| Campo | Tipo | Por qué |
|---|---|---|
| `assigned_to` | UUID FK → merchant_members NULL | quién tomó el chat |
| `handoff_at` | TIMESTAMP NULL | cuándo se escaló |
| `handoff_reason` | VARCHAR(40) NULL | pidió_humano / reclamo / fuera_de_alcance / pedido_grande |
| `last_message_at` | TIMESTAMP NULL | ordenar "necesita respuesta" |
| `needs_attention` | BOOLEAN def false | bandera para el dashboard |
| `status` | (ya existe) | active / closed / handoff |

### 5.2 `notifications` — avisos al dueño + bandeja del dashboard (NUEVA) **[AHORA]**
| Campo | Tipo | Por qué |
|---|---|---|
| `merchant_id` | UUID FK | destinatario |
| `type` | VARCHAR(30) | handoff / new_order / payment / low_stock |
| `title` | VARCHAR(200) | |
| `body` | TEXT | |
| `conversation_id` | UUID FK NULL | enlace |
| `order_id` | UUID FK NULL | enlace |
| `channel` | VARCHAR(20) | dashboard / whatsapp / email |
| `is_read` | BOOLEAN def false | |
| `sent_at` | TIMESTAMP NULL | si se envió por WhatsApp/email |

---

## 6. Métricas (home del dashboard, G) **[FUTURO — sin esquema nuevo por ahora]**
Las métricas (chats, pedidos, ventas Bs, top productos, conversión) se **calculan**
sobre las tablas existentes (orders, conversations, messages con timestamps).
Solo si el volumen crece se agrega una tabla de rollup diario `daily_stats` **[FUTURO]**.

---

## 7. Decisiones que necesito que confirmes

1. **Variantes de producto** (`product_variants`): ¿tus productos tienen combinaciones con
   **stock propio** (polera negra M, negra L, blanca M…)? → recomiendo **SÍ, tabla de variantes**
   (retrofittear esto después es caro: toca stock y pedidos). Si todos tus productos son de
   stock único, lo dejamos en campos simples.
2. **"Vendedores"**: ¿son **usuarios staff** que atienden/cierran ventas (→ `merchant_members`
   con rol `seller` + `seller_id` en producto/pedido), o solo un **texto** "vendedor a cargo"?
   → recomiendo **usuarios staff** (encaja con roles y comisiones a futuro).
3. **Entregas**: ¿manejas **zonas con costo** (Sur Bs15, Centro Bs10) o es **texto simple**
   ("hacemos delivery, consultar")? → recomiendo **zonas** (`delivery_zones`).
4. **Multi-usuario / roles**: ¿un negocio = **un solo login** (el dueño) o **varios usuarios
   con roles**? → recomiendo **separar usuarios del negocio AHORA** (`merchant_members`); es
   el cimiento más caro de agregar después.
