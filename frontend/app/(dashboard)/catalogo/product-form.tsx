"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import type { Product } from "@/lib/types";
import {
  createProduct,
  updateProduct,
  type ProductInput,
} from "./actions";

interface Props {
  product: Product | null; // null = creando
  onClose: () => void;
  onSaved: () => void;
}

export function ProductForm({ product, onClose, onSaved }: Props) {
  const [name, setName] = useState(product?.name ?? "");
  const [description, setDescription] = useState(product?.description ?? "");
  const [price, setPrice] = useState(product?.price ?? "");
  const [stock, setStock] = useState(String(product?.stock ?? 0));
  const [imageUrl, setImageUrl] = useState(product?.image_url ?? "");
  const [isActive, setIsActive] = useState(product?.is_active ?? true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);

    const input: ProductInput = {
      name,
      description,
      price: Number(price),
      stock: Number(stock),
      image_url: imageUrl,
      is_active: isActive,
    };

    const result = product
      ? await updateProduct(product.id, input)
      : await createProduct(input);

    setSaving(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    onSaved();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">
            {product ? "Editar producto" : "Nuevo producto"}
          </h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="Nombre">
            <Input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Zapatilla deportiva"
            />
          </Field>

          <Field label="Descripción">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detalles, tallas, colores..."
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Precio (Bs)">
              <Input
                type="number"
                step="0.01"
                min="0"
                required
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="150.00"
              />
            </Field>
            <Field label="Stock">
              <Input
                type="number"
                step="1"
                min="0"
                required
                value={stock}
                onChange={(e) => setStock(e.target.value)}
                placeholder="10"
              />
            </Field>
          </div>

          <Field label="URL de imagen (opcional)">
            <Input
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://..."
            />
          </Field>

          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 accent-emerald-600"
            />
            Activo (visible para el bot)
          </label>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Guardando..." : "Guardar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm text-zinc-300">{label}</label>
      {children}
    </div>
  );
}
