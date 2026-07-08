import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { ClinicalMemoryViewer } from "@/components/clinical-memory-viewer";
import { useAgentChat, type AgentEvent } from "@/hooks/use-agent-chat";
import { Waves } from "lucide-react";

export const Route = createFileRoute("/_authenticated/app")({
  component: AppPage,
});

function AppPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const { connected, profile, chatHistory, error, send, setProfile, setChatHistory } =
    useAgentChat({ sessionId });

  const [messages, setMessages] = useState<Array<{ id: string; role: "user" | "assistant"; content: string }>>([]);
  const [pending, setPending] = useState<{ user: string; assistantStream: string } | null>(null);
  const [agentState, setAgentState] = useState<string | null>(null);
  const [criticalAlert, setCriticalAlert] = useState<{ reason: string } | null>(null);
  const [draft, setDraft] = useState("");

  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Load chat history on connect
  useEffect(() => {
    if (chatHistory.length > 0 && messages.length === 0) {
      setMessages(
        chatHistory.map((m, i) => ({
          id: String(i),
          role: m.role as "user" | "assistant",
          content: m.content,
        }))
      );
    }
  }, [chatHistory]);

  const handleSend = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !connected) return;

      setPending({ user: trimmed, assistantStream: "" });
      setDraft("");
      setAgentState("thinking...");
      send(trimmed);
    },
    [connected, send]
  );

  // Listen to WebSocket messages for streaming
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as AgentEvent;

        switch (event.type) {
          case "node_start":
            setAgentState(event.node === "respond" ? "responding..." : `processing ${event.node}...`);
            break;
          case "node_end":
            setAgentState(null);
            break;
          case "safety_result":
            if (event.interrupt_triggered) {
              setCriticalAlert({ reason: event.safety_check.alerts.join(", ") });
            }
            break;
          case "token":
            setPending((prev) =>
              prev ? { ...prev, assistantStream: prev.assistantStream + event.content } : prev
            );
            break;
          case "done":
            setMessages((prev) => [
              ...prev,
              { id: Date.now().toString() + "-user", role: "user", content: pending?.user ?? "" },
              { id: Date.now().toString() + "-assistant", role: "assistant", content: event.data.response },
            ]);
            setPending(null);
            setAgentState(null);
            if (event.data.extracted_clinical_data) {
              setProfile((prev) => ({ ...prev, ...event.data.extracted_clinical_data }));
            }
            break;
        }
      } catch {
        // ignore
      }
    };

    return () => ws.close();
  }, [sessionId, pending, setProfile]);

  return (
    <div className="flex h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b border-border/60 bg-background/80 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
            <Waves className="h-4 w-4" />
          </div>
          <span className="font-semibold tracking-tight">CareAnchor</span>
          <span className="ml-2 text-xs text-muted-foreground">
            Session: {sessionId.slice(0, 8)}...
          </span>
        </div>
        <div className="flex items-center gap-3">
          {connected ? (
            <span className="flex items-center gap-1.5 text-xs text-green-600">
              <span className="h-2 w-2 rounded-full bg-green-600" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-muted-foreground" />
              Disconnected
            </span>
          )}
          <Link to="/auth" className="text-sm text-muted-foreground hover:text-foreground">
            Sign out
          </Link>
        </div>
      </header>

      {/* Main content */}
      <div className="flex w-full pt-14">
        <div className="flex-1 overflow-hidden">
          <ChatPanel
            messages={messages}
            pending={pending}
            agentState={agentState}
            busy={!connected}
            criticalAlert={criticalAlert}
            inputRef={inputRef}
            scrollRef={scrollRef}
            onSend={handleSend}
            onDraftChange={setDraft}
            draft={draft}
          />
        </div>
        <aside className="hidden w-80 border-l border-border/60 lg:block">
          <ClinicalMemoryViewer profile={profile} alerts={[]} />
        </aside>
      </div>
    </div>
  );
}
