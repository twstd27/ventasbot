"use client";

import * as React from "react";

export type Palette = "slate" | "sage" | "sand" | "mauve";

const PALETTES: Palette[] = ["slate", "sage", "sand", "mauve"];
const STORAGE_KEY = "ventabot-palette";
const DEFAULT_PALETTE: Palette = "slate";

interface PaletteContextValue {
  palette: Palette;
  setPalette: (p: Palette) => void;
  palettes: Palette[];
}

const PaletteContext = React.createContext<PaletteContextValue>({
  palette: DEFAULT_PALETTE,
  setPalette: () => {},
  palettes: PALETTES,
});

export function PaletteProvider({ children }: { children: React.ReactNode }) {
  const [palette, setPaletteState] = React.useState<Palette>(DEFAULT_PALETTE);

  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Palette | null;
      if (stored && PALETTES.includes(stored)) setPaletteState(stored);
    } catch {
      /* ignore */
    }
  }, []);

  React.useEffect(() => {
    document.documentElement.dataset.palette = palette;
  }, [palette]);

  const setPalette = React.useCallback((p: Palette) => {
    setPaletteState(p);
    try {
      localStorage.setItem(STORAGE_KEY, p);
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <PaletteContext.Provider value={{ palette, setPalette, palettes: PALETTES }}>
      {children}
    </PaletteContext.Provider>
  );
}

export function usePalette() {
  return React.useContext(PaletteContext);
}
