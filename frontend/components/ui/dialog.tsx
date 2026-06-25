"use client";

import * as React from "react";
import { Dialog as ArkDialog } from "@ark-ui/react/dialog";
import { Portal } from "@ark-ui/react/portal";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = ArkDialog.Root;
export const DialogTrigger = ArkDialog.Trigger;
export const DialogCloseTrigger = ArkDialog.CloseTrigger;

interface DialogContentProps {
  title?: string;
  description?: string;
  className?: string;
  children?: React.ReactNode;
}

export function DialogContent({
  title,
  description,
  className,
  children,
}: DialogContentProps) {
  return (
    <Portal>
      <ArkDialog.Backdrop className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
      <ArkDialog.Positioner className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <ArkDialog.Content
          className={cn(
            "relative w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-xl focus:outline-none",
            className,
          )}
        >
          {title ? (
            <ArkDialog.Title className="text-lg font-semibold">
              {title}
            </ArkDialog.Title>
          ) : null}
          {description ? (
            <ArkDialog.Description className="mt-1 text-sm text-muted-foreground">
              {description}
            </ArkDialog.Description>
          ) : null}
          <div className="mt-4">{children}</div>
          <ArkDialog.CloseTrigger className="absolute right-4 top-4 rounded-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <X className="h-4 w-4" />
            <span className="sr-only">Cerrar</span>
          </ArkDialog.CloseTrigger>
        </ArkDialog.Content>
      </ArkDialog.Positioner>
    </Portal>
  );
}
