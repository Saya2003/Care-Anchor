import { useEffect, useRef, useState, type RefObject } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageBubble } from "@/components/message-bubble";
import { Send, ShieldAlert } from "lucide-react";

type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type PendingState = {
  user: string;
  assistantStream: string;
};

type Props = {
  messages: Msg[];
  pending: PendingState | null;
  agentState: string | null;
  busy: boolean;
  criticalAlert: { reason: string } | null;
  inputRef: RefObject<HTMLTextAreaElement | null>;
  scrollRef: RefObject<HTMLDivElement | null>;
  onSend: (text: string) => void;
  onDraftChange: (text: string) => void;
  draft: string;
};

export function ChatPanel({
  messages,
  pending,
  agentState,
  busy,
  criticalAlert,
  inputRef,
  scrollRef,
  onSend,
  onDraftChange,
  draft,
}: Props) {
  useEffect(() => {
    inputRef.current?.focus();
  }, [inputRef]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending?.assistantStream, scrollRef]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend(draft);
    }
  }

  return (
    <section className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border/60 px-6 py-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Conversation
          </div>
          <div className="text-sm">Post-discharge check-in</div>
        </div>
        {agentState && (
          <Badge variant="secondary" className="gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
            </span>
            {agentState}
          </Badge>
        )}
      </header>

      {criticalAlert && (
        <div className="border-b border-destructive/30 bg-destructive/10 px-6 py-3 text-sm text-destructive-foreground">
          <div className="flex items-center gap-2 text-destructive">
            <ShieldAlert className="h-4 w-4" />
            <span className="font-medium">Human-in-the-loop escalation:</span>
            <span>{criticalAlert.reason}</span>
          </div>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && !pending && (
            <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              Tell CareAnchor how you&apos;re feeling. Try:{" "}
              <em>&ldquo;My pain is 4/10, I took my metformin, and I feel a little dizzy.&rdquo;</em>
            </div>
          )}
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} content={m.content} />
          ))}
          {pending && (
            <>
              <MessageBubble role="user" content={pending.user} />
              <MessageBubble
                role="assistant"
                content={pending.assistantStream || "\u2026"}
                streaming
              />
            </>
          )}
        </div>
      </div>

      <div className="border-t border-border/60 bg-card/40 px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          <Textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="How are you feeling? Pain level, meds, vitals \u2014 anything."
            className="min-h-[52px] max-h-40 resize-none"
            disabled={busy}
          />
          <Button
            onClick={() => onSend(draft)}
            disabled={busy || !draft.trim()}
            className="h-[52px] px-4"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">
          Research prototype \u2014 not a substitute for medical care.
        </p>
      </div>
    </section>
  );
}
