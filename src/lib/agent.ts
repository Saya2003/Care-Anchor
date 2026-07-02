import type { AgentEvent } from "@/hooks/use-agent-chat";

const WS_BASE = (import.meta.env.VITE_API_WS_URL as string) ?? "ws://localhost:8000";

/** Opens a WebSocket to the FastAPI backend for the given session and yields events. */
export async function* runAgent(
  sessionId: string,
  userMessage: string,
): AsyncGenerator<AgentEvent> {
  const ws = new WebSocket(`${WS_BASE}/ws/chat/${sessionId}`);
  const queue: AgentEvent[] = [];
  let done = false;
  let resolve: (() => void) | null = null;

  ws.onmessage = (e) => {
    try {
      const parsed = JSON.parse(e.data) as AgentEvent;
      queue.push(parsed);
      resolve?.();
    } catch {
      // skip malformed frames
    }
  };

  ws.onclose = () => {
    done = true;
    resolve?.();
  };

  ws.onerror = () => {
    done = true;
    resolve?.();
  };

  await new Promise<void>((r) => {
    ws.onopen = () => r();
  });

  ws.send(JSON.stringify({ message: userMessage }));

  while (!done || queue.length > 0) {
    if (queue.length === 0) {
      await new Promise<void>((r) => {
        resolve = r;
      });
    }
    while (queue.length > 0) {
      yield queue.shift()!;
    }
  }

  ws.close();
}
