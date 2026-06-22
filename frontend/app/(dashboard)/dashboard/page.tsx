import Link from "next/link";
import { Package, ShoppingCart } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { getCurrentMerchant } from "@/lib/merchant";

export const dynamic = "force-dynamic";

export default async function DashboardHome() {
  const merchant = await getCurrentMerchant();
  if (!merchant) return null;

  const supabase = createClient();
  const [{ count: productCount }, { count: orderCount }] = await Promise.all([
    supabase
      .from("products")
      .select("*", { count: "exact", head: true })
      .eq("merchant_id", merchant.id),
    supabase
      .from("orders")
      .select("*", { count: "exact", head: true })
      .eq("merchant_id", merchant.id),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          Hola, {merchant.business_name ?? merchant.name}
        </h1>
        <p className="text-sm text-zinc-400">Resumen de tu negocio</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Link
          href="/catalogo"
          className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 transition-colors hover:border-zinc-700"
        >
          <div className="flex items-center gap-3">
            <Package className="h-5 w-5 text-emerald-400" />
            <span className="text-sm text-zinc-400">Productos</span>
          </div>
          <p className="mt-2 text-3xl font-bold">{productCount ?? 0}</p>
        </Link>

        <Link
          href="/pedidos"
          className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 transition-colors hover:border-zinc-700"
        >
          <div className="flex items-center gap-3">
            <ShoppingCart className="h-5 w-5 text-emerald-400" />
            <span className="text-sm text-zinc-400">Pedidos</span>
          </div>
          <p className="mt-2 text-3xl font-bold">{orderCount ?? 0}</p>
        </Link>
      </div>
    </div>
  );
}
