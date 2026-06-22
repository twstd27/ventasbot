import { redirect } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { getCurrentMerchant } from "@/lib/merchant";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const merchant = await getCurrentMerchant();

  // El middleware ya exige sesión. Si hay sesión pero el email no corresponde
  // a ningún merchant, mostramos un aviso en vez de un dashboard vacío.
  if (!merchant) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4 text-center">
        <div className="max-w-md space-y-3">
          <h1 className="text-xl font-bold text-white">
            Tu cuenta aún no está vinculada a un negocio
          </h1>
          <p className="text-sm text-zinc-400">
            No encontramos un comercio con tu correo en la base de datos.
            Inicia sesión con el correo del comercio (por ejemplo el merchant
            demo <span className="text-zinc-200">demo@ventabot.bo</span>) o crea
            el registro del comercio con ese email.
          </p>
          <form action="/login">
            <button className="text-sm text-emerald-400 hover:underline">
              Volver a iniciar sesión
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      <Sidebar businessName={merchant.business_name ?? merchant.name} />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
