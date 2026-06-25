"use client";

import * as React from "react";
import { Combobox as ArkCombobox } from "@ark-ui/react/combobox";
import { createListCollection } from "@ark-ui/react/collection";
import { Portal } from "@ark-ui/react/portal";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ComboboxOption {
  label: string;
  value: string;
}

interface ComboboxProps {
  items: ComboboxOption[];
  label?: string;
  placeholder?: string;
  className?: string;
  onValueChange?: (value: string[]) => void;
}

export function Combobox({
  items,
  label,
  placeholder = "Buscar...",
  className,
  onValueChange,
}: ComboboxProps) {
  const [filtered, setFiltered] = React.useState(items);
  const collection = React.useMemo(
    () => createListCollection({ items: filtered }),
    [filtered],
  );

  const handleInput = (details: { inputValue: string }) => {
    const q = details.inputValue.toLowerCase();
    setFiltered(items.filter((i) => i.label.toLowerCase().includes(q)));
  };

  return (
    <ArkCombobox.Root
      collection={collection}
      onInputValueChange={handleInput}
      onValueChange={(e) => onValueChange?.(e.value)}
      className={cn("w-full", className)}
    >
      {label ? (
        <ArkCombobox.Label className="mb-1.5 block text-sm font-medium text-foreground">
          {label}
        </ArkCombobox.Label>
      ) : null}
      <ArkCombobox.Control className="relative">
        <ArkCombobox.Input
          placeholder={placeholder}
          className="h-9 w-full rounded-md border border-input bg-card px-3 pr-9 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <ArkCombobox.Trigger className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
          <ChevronsUpDown className="h-4 w-4" />
        </ArkCombobox.Trigger>
      </ArkCombobox.Control>
      <Portal>
        <ArkCombobox.Positioner>
          <ArkCombobox.Content className="z-50 max-h-60 w-[var(--reference-width)] overflow-y-auto rounded-md border border-border bg-card p-1 shadow-lg focus:outline-none">
            {filtered.length === 0 ? (
              <div className="px-2 py-1.5 text-sm text-muted-foreground">
                Sin resultados
              </div>
            ) : (
              filtered.map((item) => (
                <ArkCombobox.Item
                  key={item.value}
                  item={item}
                  className="flex cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-sm text-foreground data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground"
                >
                  <ArkCombobox.ItemText>{item.label}</ArkCombobox.ItemText>
                  <ArkCombobox.ItemIndicator>
                    <Check className="h-4 w-4 text-primary" />
                  </ArkCombobox.ItemIndicator>
                </ArkCombobox.Item>
              ))
            )}
          </ArkCombobox.Content>
        </ArkCombobox.Positioner>
      </Portal>
    </ArkCombobox.Root>
  );
}
