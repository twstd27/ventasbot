-- VentaBot — Políticas RLS (Row Level Security) para Supabase
-- ============================================================
-- Punto verde #1 del plan: cerrar el acceso directo de la `anon key`.
--
-- Modelo de propiedad: el usuario autenticado (Supabase Auth) es dueño del
-- merchant cuyo email coincide con el email de su JWT. (El frontend ya mapea
-- usuario -> merchant por email; el merchant demo es demo@ventabot.bo.)
--
-- IMPORTANTE: el backend (FastAPI) se conecta con el rol `postgres` vía
-- DATABASE_URL, que IGNORA RLS (BYPASSRLS). Por eso el bot sigue creando
-- pedidos/productos sin problema; RLS sólo afecta al acceso por la API
-- (PostgREST) que usa el frontend con la anon/authenticated key.
--
-- Cómo aplicar: Supabase -> SQL Editor -> pegar y ejecutar. Es idempotente.
-- ============================================================

-- 0) Asegurar que el rol `authenticated` puede alcanzar las tablas.
--    (RLS gobierna QUÉ filas; los GRANT gobiernan el acceso base.)
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.products      to authenticated;
grant select                         on public.orders         to authenticated;
grant select                         on public.order_items    to authenticated;
grant select                         on public.conversations  to authenticated;
grant select                         on public.messages       to authenticated;
grant select, update                 on public.merchants      to authenticated;

-- 1) Habilitar RLS en todas las tablas del dominio.
alter table public.merchants      enable row level security;
alter table public.products       enable row level security;
alter table public.orders         enable row level security;
alter table public.order_items    enable row level security;
alter table public.conversations  enable row level security;
alter table public.messages       enable row level security;

-- 2) merchants: el usuario ve y edita SU propia fila.
drop policy if exists "merchant_self_select" on public.merchants;
create policy "merchant_self_select" on public.merchants
  for select to authenticated
  using (email = (select auth.jwt() ->> 'email'));

drop policy if exists "merchant_self_update" on public.merchants;
create policy "merchant_self_update" on public.merchants
  for update to authenticated
  using (email = (select auth.jwt() ->> 'email'))
  with check (email = (select auth.jwt() ->> 'email'));

-- 3) products: CRUD completo, pero sólo de productos del merchant propio.
drop policy if exists "products_owner_all" on public.products;
create policy "products_owner_all" on public.products
  for all to authenticated
  using (
    merchant_id in (
      select id from public.merchants
      where email = (select auth.jwt() ->> 'email')
    )
  )
  with check (
    merchant_id in (
      select id from public.merchants
      where email = (select auth.jwt() ->> 'email')
    )
  );

-- 4) orders: sólo lectura (el bot las crea por el backend, que ignora RLS).
drop policy if exists "orders_owner_select" on public.orders;
create policy "orders_owner_select" on public.orders
  for select to authenticated
  using (
    merchant_id in (
      select id from public.merchants
      where email = (select auth.jwt() ->> 'email')
    )
  );

-- 5) order_items: visibles si su orden pertenece al merchant propio.
drop policy if exists "order_items_owner_select" on public.order_items;
create policy "order_items_owner_select" on public.order_items
  for select to authenticated
  using (
    order_id in (
      select o.id
      from public.orders o
      join public.merchants m on m.id = o.merchant_id
      where m.email = (select auth.jwt() ->> 'email')
    )
  );

-- 6) conversations: sólo lectura de las conversaciones propias.
drop policy if exists "conversations_owner_select" on public.conversations;
create policy "conversations_owner_select" on public.conversations
  for select to authenticated
  using (
    merchant_id in (
      select id from public.merchants
      where email = (select auth.jwt() ->> 'email')
    )
  );

-- 7) messages: visibles si su conversación pertenece al merchant propio.
drop policy if exists "messages_owner_select" on public.messages;
create policy "messages_owner_select" on public.messages
  for select to authenticated
  using (
    conversation_id in (
      select c.id
      from public.conversations c
      join public.merchants m on m.id = c.merchant_id
      where m.email = (select auth.jwt() ->> 'email')
    )
  );

-- ============================================================
-- Verificación rápida (opcional): listar políticas creadas.
--   select schemaname, tablename, policyname, cmd
--   from pg_policies where schemaname = 'public' order by tablename;
-- ============================================================
