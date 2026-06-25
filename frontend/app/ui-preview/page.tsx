"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { PalettePicker } from "@/components/ui/palette-picker";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogCloseTrigger,
} from "@/components/ui/dialog";
import { Combobox } from "@/components/ui/combobox";

const productos = [
  { label: "Polera negra talla M", value: "p1" },
  { label: "Polera blanca talla L", value: "p2" },
  { label: "Gorra azul", value: "p3" },
  { label: "Mochila urbana", value: "p4" },
  { label: "Zapatillas running 42", value: "p5" },
];

const tokens = [
  { name: "background", className: "bg-background" },
  { name: "card", className: "bg-card" },
  { name: "muted", className: "bg-muted" },
  { name: "primary", className: "bg-primary" },
  { name: "accent", className: "bg-accent" },
  { name: "destructive", className: "bg-destructive" },
  { name: "border", className: "bg-border" },
  { name: "foreground", className: "bg-foreground" },
];

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border bg-card p-6">
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function UiPreviewPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-4xl space-y-8 px-6 py-10">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">VentaBot · UI Preview</h1>
            <p className="text-sm text-muted-foreground">
              Ark UI + tokens semánticos — alterna claro/oscuro con el botón →
            </p>
          </div>
          <div className="flex items-end gap-4">
            <div className="w-44">
              <PalettePicker />
            </div>
            <ThemeToggle />
          </div>
        </header>

        <Section title="Paleta (tokens semánticos)">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {tokens.map((t) => (
              <div key={t.name} className="space-y-1.5">
                <div
                  className={`h-12 w-full rounded-md border border-border ${t.className}`}
                />
                <span className="text-xs text-muted-foreground">{t.name}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Botones">
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary">Crear pedido</Button>
            <Button variant="default">Guardar</Button>
            <Button variant="outline">Cancelar</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="danger">Eliminar</Button>
            <Button variant="primary" size="sm">
              Pequeño
            </Button>
          </div>
        </Section>

        <Section title="Formulario">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Nombre del producto</label>
              <Input placeholder="Ej: Polera negra" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Precio (Bs)</label>
              <Input type="number" placeholder="120" />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-sm font-medium">Descripción</label>
              <Textarea placeholder="Detalles del producto..." />
            </div>
          </div>
          <div className="mt-4">
            <Switch label="Producto activo" defaultChecked />
          </div>
        </Section>

        <Section title="Combobox (Ark) — buscar producto">
          <div className="max-w-sm">
            <Combobox
              items={productos}
              label="Producto"
              placeholder="Escribe para buscar..."
            />
          </div>
        </Section>

        <Section title="Dialog (Ark)">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="primary">Abrir modal</Button>
            </DialogTrigger>
            <DialogContent
              title="Confirmar pedido"
              description="¿Deseas crear este pedido para el cliente?"
            >
              <div className="flex justify-end gap-2">
                <DialogCloseTrigger asChild>
                  <Button variant="outline">Cancelar</Button>
                </DialogCloseTrigger>
                <DialogCloseTrigger asChild>
                  <Button variant="primary">Confirmar</Button>
                </DialogCloseTrigger>
              </div>
            </DialogContent>
          </Dialog>
        </Section>
      </div>
    </div>
  );
}
