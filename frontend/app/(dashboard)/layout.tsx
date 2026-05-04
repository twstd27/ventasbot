export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      {/* Sidebar — se implementa con shadcn/ui */}
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
