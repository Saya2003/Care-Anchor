import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { ChatHistorySidebar } from "@/components/chat-history-sidebar";
import { useAgentChat, type AgentEvent } from "@/hooks/use-agent-chat";
import { Waves } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/app")({
  component: AppPage,
});

function AppPage() {
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [connected, setConnected] = useState(false);
  const [profile, setProfile] = useState<any>({});
  const [messages, setMessages] = useState<Array<{ id: string; role: "user" | "assistant"; content: string }>>([]);
  const [pending, setPending] = useState<{ user: string; assistantStream: string } | null>(null);
  const [agentState, setAgentState] = useState<string | null>(null);
  const [criticalAlert, setCriticalAlert] = useState<{ reason: string } | null>(null);
  const [draft, setDraft] = useState("");
  const [refreshSidebar, setRefreshSidebar] = useState(0);

  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const pendingRef = useRef<{ user: string; assistantStream: string } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Single WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[Frontend] WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as AgentEvent;
        
        console.log('[Frontend] Received event:', event.type);

        switch (event.type) {
          case "session_init":
            setProfile(event.profile);
            if (event.chat_history.length > 0) {
              setMessages(
                event.chat_history.map((m, i) => ({
                  id: String(i),
                  role: m.role as "user" | "assistant",
                  content: m.content,
                }))
              );
            }
            break;
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
            setPending((prev) => {
              const updated = prev ? { ...prev, assistantStream: prev.assistantStream + event.content } : prev;
              pendingRef.current = updated;
              return updated;
            });
            break;
          case "done":
            const userMsg = pendingRef.current?.user ?? "";
            const assistantMsg = event.data?.response ?? "";
            
            console.log('[Frontend] Done - user:', userMsg, 'assistant:', assistantMsg);
            
            setMessages((prev) => [
              ...prev,
              { id: Date.now().toString() + "-user", role: "user", content: userMsg },
              { id: Date.now().toString() + "-assistant", role: "assistant", content: assistantMsg },
            ]);
            setPending(null);
            pendingRef.current = null;
            setAgentState(null);
            if (event.data?.extracted_clinical_data) {
              setProfile((prev: any) => ({ ...prev, ...event.data.extracted_clinical_data }));
            }
            // Refresh sidebar after message is complete
            setRefreshSidebar(prev => prev + 1);
            break;
        }
      } catch (err) {
        console.error('[Frontend] Error parsing message:', err);
      }
    };
    
    ws.onerror = () => {
      console.error('[Frontend] WebSocket error');
      setConnected(false);
    };
    
    ws.onclose = () => {
      console.log('[Frontend] WebSocket closed');
      setConnected(false);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId]);

  const handleSend = useCallback(
    (text: string, files?: Array<{ name: string; type: string; size: number; dataUrl: string }>) => {
      const trimmed = text.trim();
      if (!trimmed && (!files || files.length === 0)) return;

      if (!connected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        toast.error("Backend server not connected", {
          description: "Start the backend server at localhost:8000 to send messages",
        });
        return;
      }

      const newPending = { user: trimmed, assistantStream: "" };
      setPending(newPending);
      pendingRef.current = newPending;
      setDraft("");
      setAgentState("thinking...");
      
      wsRef.current.send(JSON.stringify({ 
        message: trimmed,
        attachments: files || []
      }));
    },
    [connected]
  );

  const handleSessionSelect = useCallback((newSessionId: string) => {
    if (newSessionId === sessionId) return; // Already on this session
    
    // Close existing WebSocket connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Reset all state
    setMessages([]);
    setPending(null);
    pendingRef.current = null;
    setAgentState(null);
    setCriticalAlert(null);
    setDraft("");
    setProfile({});
    setConnected(false);
    
    // Update session ID (this will trigger WebSocket reconnection via useEffect)
    setSessionId(newSessionId);
  }, [sessionId]);

  const handleNewChat = useCallback(() => {
    const newId = crypto.randomUUID();
    handleSessionSelect(newId);
  }, [handleSessionSelect]);

  return (
    <div className="flex h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b border-border/60 bg-background/80 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-6">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Waves className="h-4 w-4" />
            </div>
            <span className="font-semibold tracking-tight">CareAnchor</span>
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <Link 
              to="/dashboard" 
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Dashboard
            </Link>
            <Link 
              to="/app" 
              className="text-sm font-medium text-foreground"
            >
              Chat
            </Link>
            <Link 
              to="/settings" 
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Settings
            </Link>
          </nav>
          <span className="text-xs text-muted-foreground">
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
          <Link to="/logout" className="text-sm text-muted-foreground hover:text-foreground">
            Sign out
          </Link>
        </div>
      </header>

      {/* Main content */}
      <div className="flex w-full pt-14">
        <ChatHistorySidebar
          currentSessionId={sessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          refreshTrigger={refreshSidebar}
        />
        <div className="flex-1 overflow-hidden">
          <ChatPanel
            messages={messages}
            pending={pending}
            agentState={agentState}
            busy={!!pending || !!agentState}
            criticalAlert={criticalAlert}
            inputRef={inputRef}
            scrollRef={scrollRef}
            onSend={handleSend}
            onDraftChange={setDraft}
            draft={draft}
            connected={connected}
          />
        </div>
      </div>
    </div>
  );
}
