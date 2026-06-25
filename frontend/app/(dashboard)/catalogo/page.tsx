import { createClient } from "@/lib/supabase/server";
import { getCurrentMerchant } from "@/lib/merchant";
import type { Product } from "@/lib/types";
import { ProductList } from "./product-list";

export const dynamic = "force-dynamic";

export default async function CatalogoPage() {
  const merchant = await getCurrentMerchant();
  if (!merchant) return null; // el layout ya maneja este caso

  const supabase = createClient();
  const { data, error } = await supabase
    .from("products")
    .select("*")
    .eq("merchant_id", merchant.id)
    .order("created_at", { ascending: false });

  if (error) {
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Catálogo</h1>
        <p className="text-sm text-destructive">
          Error cargando productos: {error.message}
        </p>
      </div>
    );
  }

  return <ProductList products={(data ?? []) as Product[]} />;
}
