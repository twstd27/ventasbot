"use client";

import { Check } from "lucide-react";
import { usePalette, type Palette } from "@/components/palette-provider";
import { cn } from "@/lib/utils";

const OPTIONS: { value: Palette; label: string; color: string }[] = [
  { value: "slate", label: "Slate", color: "#3e63dd" },
  { value: "sage", label: "Sage", color: "#46a758" },
  { value: "sand", label: "Sand", color: "#ffb224" },
  { value: "mauve", label: "Mauve", color: "#8e4ec6" },
];

export function PalettePicker() {
  const { palette, setPalette } = usePalette();

  return (
    <div className="space-y-1.5">
      <p className="px-1 text-xs font-medium text-muted-foreground">Paleta</p>
      <div className="grid grid-cols-4 gap-1.5">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => setPalette(o.value)}
            aria-label={o.label}
            title={o.label}
            className={cn(
              "relative flex h-8 items-center justify-center rounded-md border transition-colors",
              palette === o.value
                ? "border-foreground"
                : "border-border hover:border-muted-foreground",
            )}
          >
            <span
              className="h-4 w-4 rounded-full"
              style={{ backgroundColor: o.color }}
            />
            {palette === o.value ? (
              <Check className="absolute h-3 w-3 text-white mix-blend-difference" />
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
}
