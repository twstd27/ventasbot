import { createClient } from "@/lib/supabase/server";
import type { Merchant } from "@/lib/types";

// Mapea el usuario autenticado (Supabase Auth) a su fila en `merchants`
// usando el email. El merchant demo del seed es demo@ventabot.bo.
export async function getCurrentMerchant(): Promise<Merchant | null> {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user?.email) return null;

  const { data, error } = await supabase
    .from("merchants")
    .select("*")
    .eq("email", user.email)
    .maybeSingle();

  if (error) {
    console.error("Error cargando merchant:", error.message);
    return null;
  }

  return data as Merchant | null;
}
