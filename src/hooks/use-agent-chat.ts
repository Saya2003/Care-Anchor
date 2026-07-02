import { useCallback, useEffect, useRef, useState } from "react";
import type { ClinicalProfile } from "@/components/clinical-memory-viewer";

export type SafetyCheck = {
  breached: boolean;
  alerts: string[];
};

export type AgentEvent =
  | { type: "session_init"; profile: ClinicalProfile; chat_history: Array<{ role: string; content: string }> }
  | { type: "node_end"; node: string }
  | { type: "safety_result"; extracted_clinical_data: Partial<ClinicalProfile>; safety_check: SafetyCheck; interrupt_triggered: boolean }
  | { type: "node_start"; node: string }
  | { type: "token"; content: string }
  | { type: "done"; data: { response: string; extracted_clinical_data: Partial<ClinicalProfile>; safety_check: SafetyCheck; interrupt_triggered: boolean } }
  | { type: "error"; detail: string };

type UseAgentChatOptions = {
  sessionId: string;
  wsBaseUrl?: string;
};

export function useAgentChat({ sessionId, wsBaseUrl }: UseAgentChatOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [profile, setProfile] = useState<ClinicalProfile>({});
  const [chatHistory, setChatHistory] = useState<Array<{ role: string; content: string }>>([]);
  const [error, setError] = useState<string | null>(null);

  const baseUrl = wsBaseUrl ?? (import.meta.env.VITE_API_WS_URL as string | undefined) ?? "ws://localhost:8000";

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${baseUrl}/ws/chat/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => {
      setError("WebSocket connection failed");
      setConnected(false);
    };

    return ws;
  }, [baseUrl, sessionId]);

  useEffect(() => {
    const ws = connect();
    if (!ws) return;

    const handleMessage = (e: MessageEvent) => {
      try {
        const event = JSON.parse(e.data) as AgentEvent;
        if (event.type === "session_init") {
          setProfile(event.profile);
          setChatHistory(event.chat_history);
        }
      } catch {
        // ignore malformed
      }
    };

    ws.addEventListener("message", handleMessage);
    return () => {
      ws.removeEventListener("message", handleMessage);
      ws.close();
      wsRef.current = null;
      setConnected(false);
    };
  }, [connect]);

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message }));
    } else {
      setError("Not connected to agent");
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  return { connected, profile, chatHistory, error, send, disconnect, setProfile, setChatHistory };
}
