import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "./themes.css";
import { ThemeProvider } from "@/components/theme-provider";
import { PaletteProvider } from "@/components/palette-provider";

const inter = Inter({ subsets: ["latin"] });

// Evita el "flash" de paleta: aplica la elegida desde localStorage antes de pintar.
const paletteScript = `(function(){try{var p=localStorage.getItem('ventabot-palette');if(p){document.documentElement.dataset.palette=p;}}catch(e){}})();`;

export const metadata: Metadata = {
  title: "VentaBot",
  description: "Tu bot de ventas con IA para WhatsApp y Messenger",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "VentaBot" },
};

export const viewport: Viewport = {
  themeColor: "#18181b",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" data-palette="slate" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: paletteScript }} />
      </head>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <PaletteProvider>{children}</PaletteProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
