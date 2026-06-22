"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  MessageSquare,
  LogOut,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Inicio", icon: LayoutDashboard },
  { href: "/catalogo", label: "Catálogo", icon: Package },
  { href: "/pedidos", label: "Pedidos", icon: ShoppingCart },
  { href: "/conversaciones", label: "Conversaciones", icon: MessageSquare },
];

export function Sidebar({ businessName }: { businessName: string }) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="flex w-60 flex-col border-r border-zinc-800 bg-zinc-900">
      <div className="border-b border-zinc-800 p-4">
        <p className="text-lg font-bold text-white">VentaBot</p>
        <p className="truncate text-xs text-zinc-400">{businessName}</p>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-emerald-600/15 text-emerald-400"
                  : "text-zinc-300 hover:bg-zinc-800 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800 p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white"
        >
          <LogOut className="h-4 w-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
