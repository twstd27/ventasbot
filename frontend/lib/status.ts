import type { OrderStatus } from "@/lib/types";

// Etiquetas y colores para los estados de pedido (state machine del backend:
// pending → paid → preparing → delivered / cancelled).
export const ORDER_STATUS: Record<
  OrderStatus,
  { label: string; className: string }
> = {
  pending: { label: "Pendiente", className: "bg-amber-500/15 text-amber-400" },
  paid: { label: "Pagado", className: "bg-emerald-500/15 text-emerald-400" },
  preparing: { label: "Preparando", className: "bg-sky-500/15 text-sky-400" },
  delivered: { label: "Entregado", className: "bg-zinc-500/20 text-zinc-300" },
  cancelled: { label: "Cancelado", className: "bg-red-500/15 text-red-400" },
};

export function orderStatusMeta(status: string) {
  return (
    ORDER_STATUS[status as OrderStatus] ?? {
      label: status,
      className: "bg-zinc-700/40 text-zinc-300",
    }
  );
}
