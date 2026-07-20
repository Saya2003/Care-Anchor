/**
 * Netlify Edge Function for WebSocket proxy
 * This function handles WebSocket connections for real-time chat
 */

import { Context } from "https://edge.netlify.com";

export default async (request: Request, context: Context) => {
  // Only handle WebSocket upgrade requests
  if (request.headers.get("upgrade") !== "websocket") {
    return new Response("Expected WebSocket", { status: 426 });
  }

  // Extract session ID from URL
  const url = new URL(request.url);
  const sessionId = url.pathname.split('/').pop();

  if (!sessionId) {
    return new Response("Session ID required", { status: 400 });
  }

  try {
    // For now, return a basic WebSocket upgrade response
    // In a full implementation, you'd proxy to your backend WebSocket server
    
    const { socket, response } = Deno.upgradeWebSocket(request);
    
    socket.onopen = () => {
      console.log(`WebSocket connected for session: ${sessionId}`);
      socket.send(JSON.stringify({
        type: "connection_established",
        session_id: sessionId,
        message: "Connected to CareAnchor chat"
      }));
    };
    
    socket.onmessage = (event) => {
      console.log(`Message received: ${event.data}`);
      
      try {
        const data = JSON.parse(event.data);
        
        // Echo back for now - in production, this would forward to your AI backend
        socket.send(JSON.stringify({
          type: "ai_response",
          message: `I received your message: "${data.message}". This is a demo response from Netlify Edge Functions.`,
          timestamp: new Date().toISOString()
        }));
        
      } catch (error) {
        socket.send(JSON.stringify({
          type: "error",
          message: "Invalid message format",
          timestamp: new Date().toISOString()
        }));
      }
    };
    
    socket.onclose = () => {
      console.log(`WebSocket disconnected for session: ${sessionId}`);
    };
    
    socket.onerror = (error) => {
      console.error(`WebSocket error for session ${sessionId}:`, error);
    };
    
    return response;
    
  } catch (error) {
    console.error("WebSocket setup error:", error);
    return new Response("WebSocket setup failed", { status: 500 });
  }
};

export const config = {
  path: "/ws/*"
};