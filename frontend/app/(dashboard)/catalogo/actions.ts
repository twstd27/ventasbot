"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { getCurrentMerchant } from "@/lib/merchant";

export interface ProductInput {
  name: string;
  description: string;
  price: number;
  stock: number;
  image_url: string;
  is_active: boolean;
}

export type ActionResult = { ok: true } | { ok: false; error: string };

function validate(input: ProductInput): string | null {
  if (!input.name.trim()) return "El nombre es obligatorio.";
  if (!Number.isFinite(input.price) || input.price < 0)
    return "El precio debe ser un número válido.";
  if (!Number.isInteger(input.stock) || input.stock < 0)
    return "El stock debe ser un entero mayor o igual a 0.";
  return null;
}

export async function createProduct(
  input: ProductInput,
): Promise<ActionResult> {
  const err = validate(input);
  if (err) return { ok: false, error: err };

  const merchant = await getCurrentMerchant();
  if (!merchant) return { ok: false, error: "Sesión no válida." };

  const supabase = createClient();
  const { error } = await supabase.from("products").insert({
    merchant_id: merchant.id,
    name: input.name.trim(),
    description: input.description.trim() || null,
    price: input.price,
    stock: input.stock,
    image_url: input.image_url.trim() || null,
    is_active: input.is_active,
  });

  if (error) return { ok: false, error: error.message };
  revalidatePath("/catalogo");
  return { ok: true };
}

export async function updateProduct(
  id: string,
  input: ProductInput,
): Promise<ActionResult> {
  const err = validate(input);
  if (err) return { ok: false, error: err };

  const merchant = await getCurrentMerchant();
  if (!merchant) return { ok: false, error: "Sesión no válida." };

  const supabase = createClient();
  const { error } = await supabase
    .from("products")
    .update({
      name: input.name.trim(),
      description: input.description.trim() || null,
      price: input.price,
      stock: input.stock,
      image_url: input.image_url.trim() || null,
      is_active: input.is_active,
    })
    .eq("id", id)
    .eq("merchant_id", merchant.id); // scope: sólo productos propios

  if (error) return { ok: false, error: error.message };
  revalidatePath("/catalogo");
  return { ok: true };
}

export async function deleteProduct(id: string): Promise<ActionResult> {
  const merchant = await getCurrentMerchant();
  if (!merchant) return { ok: false, error: "Sesión no válida." };

  const supabase = createClient();
  const { error } = await supabase
    .from("products")
    .delete()
    .eq("id", id)
    .eq("merchant_id", merchant.id);

  if (error) return { ok: false, error: error.message };
  revalidatePath("/catalogo");
  return { ok: true };
}

export async function toggleProductActive(
  id: string,
  isActive: boolean,
): Promise<ActionResult> {
  const merchant = await getCurrentMerchant();
  if (!merchant) return { ok: false, error: "Sesión no válida." };

  const supabase = createClient();
  const { error } = await supabase
    .from("products")
    .update({ is_active: isActive })
    .eq("id", id)
    .eq("merchant_id", merchant.id);

  if (error) return { ok: false, error: error.message };
  revalidatePath("/catalogo");
  return { ok: true };
}
