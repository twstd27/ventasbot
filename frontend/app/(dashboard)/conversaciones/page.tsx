import { createClient } from "@/lib/supabase/server";
import { getCurrentMerchant } from "@/lib/merchant";
import type { Conversation } from "@/lib/types";
import { ConversationView } from "./conversation-view";

export const dynamic = "force-dynamic";

export default async function ConversacionesPage() {
  const merchant = await getCurrentMerchant();
  if (!merchant) return null;

  const supabase = createClient();
  const { data, error } = await supabase
    .from("conversations")
    .select("*, messages(*)")
    .eq("merchant_id", merchant.id)
    .order("updated_at", { ascending: false })
    .order("created_at", { ascending: true, foreignTable: "messages" });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Conversaciones</h1>
        <p className="text-sm text-zinc-400">
          Hilos de tus clientes con el bot
        </p>
      </div>

      {error ? (
        <p className="text-sm text-red-400">
          Error cargando conversaciones: {error.message}
        </p>
      ) : (
        <ConversationView
          conversations={(data ?? []) as Conversation[]}
        />
      )}
    </div>
  );
}
