import { createClient } from "@/lib/supabase/server";
import { getCurrentMerchant } from "@/lib/merchant";
import type { Order } from "@/lib/types";
import { OrderList } from "./order-list";

export const dynamic = "force-dynamic";

export default async function PedidosPage() {
  const merchant = await getCurrentMerchant();
  if (!merchant) return null;

  const supabase = createClient();
  const { data, error } = await supabase
    .from("orders")
    .select(
      "*, items:order_items(*, product:products(name)), conversation:conversations(customer_name, channel, external_id)",
    )
    .eq("merchant_id", merchant.id)
    .order("created_at", { ascending: false });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Pedidos</h1>
        <p className="text-sm text-zinc-400">
          Órdenes que el bot generó en tus canales
        </p>
      </div>

      {error ? (
        <p className="text-sm text-red-400">
          Error cargando pedidos: {error.message}
        </p>
      ) : (
        <OrderList orders={(data ?? []) as Order[]} />
      )}
    </div>
  );
}
