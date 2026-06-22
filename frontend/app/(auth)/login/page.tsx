"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setLoading(true);
    const supabase = createClient();

    if (mode === "signin") {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setError(error.message);
        setLoading(false);
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } else {
      const { data, error } = await supabase.auth.signUp({ email, password });
      if (error) {
        setError(error.message);
        setLoading(false);
        return;
      }
      // Si la confirmación por email está desactivada, ya hay sesión.
      if (data.session) {
        router.push("/dashboard");
        router.refresh();
      } else {
        setInfo("Cuenta creada. Revisa tu correo para confirmar el acceso.");
        setMode("signin");
        setLoading(false);
      }
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
      <div className="w-full max-w-sm space-y-6 rounded-xl border border-zinc-800 bg-zinc-900 p-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-white">VentaBot</h1>
          <p className="text-sm text-zinc-400">
            {mode === "signin"
              ? "Ingresa a tu panel de ventas"
              : "Crea tu cuenta de comerciante"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm text-zinc-300" htmlFor="email">
              Correo
            </label>
            <Input
              id="email"
              type="email"
              required
              autoComplete="email"
              placeholder="demo@ventabot.bo"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm text-zinc-300" htmlFor="password">
              Contraseña
            </label>
            <Input
              id="password"
              type="password"
              required
              minLength={6}
              autoComplete={
                mode === "signin" ? "current-password" : "new-password"
              }
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}
          {info && <p className="text-sm text-emerald-400">{info}</p>}

          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={loading}
          >
            {loading
              ? "Procesando..."
              : mode === "signin"
                ? "Ingresar"
                : "Crear cuenta"}
          </Button>
        </form>

        <p className="text-center text-sm text-zinc-400">
          {mode === "signin" ? "¿No tienes cuenta? " : "¿Ya tienes cuenta? "}
          <button
            type="button"
            className="text-emerald-400 hover:underline"
            onClick={() => {
              setMode(mode === "signin" ? "signup" : "signin");
              setError(null);
              setInfo(null);
            }}
          >
            {mode === "signin" ? "Crear una" : "Ingresar"}
          </button>
        </p>
      </div>
    </main>
  );
}
