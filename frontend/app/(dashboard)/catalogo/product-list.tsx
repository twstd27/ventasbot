"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatBs } from "@/lib/utils";
import type { Product } from "@/lib/types";
import { ProductForm } from "./product-form";
import { deleteProduct, toggleProductActive } from "./actions";

export function ProductList({ products }: { products: Product[] }) {
  const router = useRouter();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(product: Product) {
    setEditing(product);
    setFormOpen(true);
  }

  function onSaved() {
    setFormOpen(false);
    setEditing(null);
    router.refresh();
  }

  async function onDelete(product: Product) {
    if (!confirm(`¿Eliminar "${product.name}"? Esta acción no se puede deshacer.`))
      return;
    setBusyId(product.id);
    const result = await deleteProduct(product.id);
    setBusyId(null);
    if (!result.ok) {
      alert(result.error);
      return;
    }
    router.refresh();
  }

  async function onToggle(product: Product) {
    setBusyId(product.id);
    await toggleProductActive(product.id, !product.is_active);
    setBusyId(null);
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Catálogo</h1>
          <p className="text-sm text-zinc-400">
            {products.length} producto{products.length === 1 ? "" : "s"} · lo que
            el bot puede vender
          </p>
        </div>
        <Button variant="primary" onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Agregar producto
        </Button>
      </div>

      {products.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-zinc-800 py-16 text-center">
          <Package className="h-10 w-10 text-zinc-600" />
          <p className="text-zinc-400">Aún no tienes productos.</p>
          <Button variant="primary" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Agregar el primero
          </Button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-left text-zinc-400">
              <tr>
                <th className="px-4 py-3 font-medium">Producto</th>
                <th className="px-4 py-3 font-medium">Precio</th>
                <th className="px-4 py-3 font-medium">Stock</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {products.map((p) => (
                <tr key={p.id} className="hover:bg-zinc-900/50">
                  <td className="px-4 py-3">
                    <p className="font-medium text-white">{p.name}</p>
                    {p.description && (
                      <p className="line-clamp-1 max-w-xs text-xs text-zinc-500">
                        {p.description}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-zinc-200">
                    {formatBs(p.price)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        p.stock === 0 ? "text-red-400" : "text-zinc-200"
                      }
                    >
                      {p.stock}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onToggle(p)}
                      disabled={busyId === p.id}
                      className={
                        "rounded-full px-2.5 py-0.5 text-xs font-medium " +
                        (p.is_active
                          ? "bg-emerald-600/15 text-emerald-400"
                          : "bg-zinc-700/40 text-zinc-400")
                      }
                    >
                      {p.is_active ? "Activo" : "Inactivo"}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openEdit(p)}
                        aria-label="Editar"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onDelete(p)}
                        disabled={busyId === p.id}
                        aria-label="Eliminar"
                      >
                        <Trash2 className="h-4 w-4 text-red-400" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {formOpen && (
        <ProductForm
          product={editing}
          onClose={() => setFormOpen(false)}
          onSaved={onSaved}
        />
      )}
    </div>
  );
}
