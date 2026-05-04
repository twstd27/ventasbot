export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950">
      <div className="w-full max-w-sm space-y-6 rounded-xl border border-zinc-800 bg-zinc-900 p-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-white">VentaBot</h1>
          <p className="text-sm text-zinc-400">Ingresa a tu panel de ventas</p>
        </div>
        {/* Auth form — se implementa con Supabase Auth */}
      </div>
    </main>
  );
}
