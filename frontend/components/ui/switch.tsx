"use client";

import * as React from "react";
import { Switch as ArkSwitch } from "@ark-ui/react/switch";
import { cn } from "@/lib/utils";

interface SwitchProps {
  label?: string;
  checked?: boolean;
  defaultChecked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function Switch({
  label,
  onCheckedChange,
  className,
  ...props
}: SwitchProps) {
  return (
    <ArkSwitch.Root
      className={cn("inline-flex items-center gap-2", className)}
      onCheckedChange={(e) => onCheckedChange?.(e.checked)}
      {...props}
    >
      <ArkSwitch.Control className="inline-flex h-5 w-9 cursor-pointer items-center rounded-full bg-muted p-0.5 transition-colors data-[state=checked]:bg-primary">
        <ArkSwitch.Thumb className="h-4 w-4 rounded-full bg-white shadow-sm transition-transform data-[state=checked]:translate-x-4" />
      </ArkSwitch.Control>
      {label ? (
        <ArkSwitch.Label className="cursor-pointer select-none text-sm text-foreground">
          {label}
        </ArkSwitch.Label>
      ) : null}
      <ArkSwitch.HiddenInput />
    </ArkSwitch.Root>
  );
}
