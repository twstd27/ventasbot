"use client";

import { useState } from "react";
import { MessageSquare, Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  active: "Activa",
  closed: "Cerrada",
  handoff: "Atención humana",
};

function channelLabel(ch: string) {
  if (ch === "whatsapp") return "WhatsApp";
  if (ch === "messenger") return "Messenger";
  return ch;
}

export function ConversationView({
  conversations,
}: {
  conversations: Conversation[];
}) {
  const [selectedId, setSelectedId] = useState<string | null>(
    conversations[0]?.id ?? null,
  );

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-zinc-800 py-16 text-center">
        <MessageSquare className="h-10 w-10 text-zinc-600" />
        <p className="text-zinc-400">Aún no hay conversaciones.</p>
        <p className="max-w-sm text-xs text-zinc-500">
          Cuando un cliente escriba a tu bot por WhatsApp o Messenger, el hilo
          aparecerá aquí.
        </p>
      </div>
    );
  }

  const selected = conversations.find((c) => c.id === selectedId) ?? null;

  return (
    <div className="grid h-[70vh] grid-cols-1 gap-4 md:grid-cols-[280px_1fr]">
      {/* Lista de hilos */}
      <div className="overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900">
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedId(c.id)}
            className={cn(
              "flex w-full flex-col gap-0.5 border-b border-zinc-800 px-4 py-3 text-left transition-colors",
              c.id === selectedId ? "bg-zinc-800" : "hover:bg-zinc-800/50",
            )}
          >
            <span className="text-sm font-medium text-white">
              {c.customer_name ?? c.external_id}
            </span>
            <span className="text-xs text-zinc-500">
              {channelLabel(c.channel)} · {STATUS_LABEL[c.status] ?? c.status}
            </span>
          </button>
        ))}
      </div>

      {/* Mensajes del hilo seleccionado */}
      <div className="flex flex-col overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
        {selected ? (
          <>
            <div className="border-b border-zinc-800 px-4 py-3">
              <p className="font-medium text-white">
                {selected.customer_name ?? selected.external_id}
              </p>
              <p className="text-xs text-zinc-500">
                {channelLabel(selected.channel)} · {selected.external_id}
              </p>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {selected.messages.length === 0 ? (
                <p className="text-sm text-zinc-500">Sin mensajes.</p>
              ) : (
                selected.messages.map((m) => {
                  const isBot = m.role === "assistant";
                  return (
                    <div
                      key={m.id}
                      className={cn(
                        "flex gap-2",
                        isBot ? "flex-row" : "flex-row-reverse",
                      )}
                    >
                      <div
                        className={cn(
                          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                          isBot
                            ? "bg-emerald-600/20 text-emerald-400"
                            : "bg-zinc-700 text-zinc-300",
                        )}
                      >
                        {isBot ? (
                          <Bot className="h-4 w-4" />
                        ) : (
                          <User className="h-4 w-4" />
                        )}
                      </div>
                      <div
                        className={cn(
                          "max-w-[75%] rounded-lg px-3 py-2 text-sm",
                          isBot
                            ? "bg-zinc-800 text-zinc-100"
                            : "bg-emerald-600 text-white",
                        )}
                      >
                        {m.content}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-zinc-500">
            Selecciona una conversación
          </div>
        )}
      </div>
    </div>
  );
}
