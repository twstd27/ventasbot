"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight, ShoppingCart } from "lucide-react";
import { formatBs } from "@/lib/utils";
import { orderStatusMeta } from "@/lib/status";
import type { Order } from "@/lib/types";

function shortId(id: string) {
  return id.slice(0, 8);
}

function formatDate(iso: string) {
  // Fecha legible sin depender de locale del server.
  const d = new Date(iso);
  return d.toLocaleString("es-BO", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function channelLabel(ch?: string) {
  if (ch === "whatsapp") return "WhatsApp";
  if (ch === "messenger") return "Messenger";
  return ch ?? "—";
}

export function OrderList({ orders }: { orders: Order[] }) {
  const [open, setOpen] = useState<string | null>(null);

  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-zinc-800 py-16 text-center">
        <ShoppingCart className="h-10 w-10 text-zinc-600" />
        <p className="text-zinc-400">Aún no hay pedidos.</p>
        <p className="max-w-sm text-xs text-zinc-500">
          Los pedidos aparecen aquí automáticamente cuando el bot cierra una
          venta por WhatsApp o Messenger.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900 text-left text-zinc-400">
          <tr>
            <th className="px-4 py-3 font-medium">Pedido</th>
            <th className="px-4 py-3 font-medium">Cliente</th>
            <th className="px-4 py-3 font-medium">Fecha</th>
            <th className="px-4 py-3 font-medium">Total</th>
            <th className="px-4 py-3 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800">
          {orders.map((o) => {
            const meta = orderStatusMeta(o.status);
            const isOpen = open === o.id;
            return (
              <Fragment key={o.id}>
                <tr
                  onClick={() => setOpen(isOpen ? null : o.id)}
                  className="cursor-pointer hover:bg-zinc-900/50"
                >
                  <td className="px-4 py-3 font-mono text-xs text-zinc-300">
                    <span className="inline-flex items-center gap-1">
                      {isOpen ? (
                        <ChevronDown className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5" />
                      )}
                      #{shortId(o.id)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-200">
                    {o.conversation?.customer_name ?? "Cliente"}
                    <span className="ml-1 text-xs text-zinc-500">
                      · {channelLabel(o.conversation?.channel)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {formatDate(o.created_at)}
                  </td>
                  <td className="px-4 py-3 font-medium text-zinc-100">
                    {formatBs(o.total_amount)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        "rounded-full px-2.5 py-0.5 text-xs font-medium " +
                        meta.className
                      }
                    >
                      {meta.label}
                    </span>
                  </td>
                </tr>
                {isOpen && (
                  <tr className="bg-zinc-950/60">
                    <td colSpan={5} className="px-4 py-3">
                      <div className="space-y-2 pl-5">
                        <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                          Items
                        </p>
                        <ul className="space-y-1">
                          {o.items.map((it) => (
                            <li
                              key={it.id}
                              className="flex justify-between text-sm text-zinc-300"
                            >
                              <span>
                                {it.quantity}× {it.product?.name ?? "Producto"}
                              </span>
                              <span className="text-zinc-400">
                                {formatBs(it.unit_price)} c/u
                              </span>
                            </li>
                          ))}
                        </ul>
                        {o.payment_reference && (
                          <p className="pt-1 text-xs text-zinc-500">
                            Ref. de pago: {o.payment_reference}
                          </p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
