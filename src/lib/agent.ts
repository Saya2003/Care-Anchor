// Client-side mock agent that simulates the FastAPI + Qwen + LangGraph backend.
// Wire your real WebSocket by setting VITE_AGENT_WS_URL; if unset, this mock
// runs locally: extracts clinical facts, streams tokens, and trips safety alerts.

import { supabase } from "@/integrations/supabase/client";

export type ClinicalMemory = {
  vitals?: {
    pain?: { value: number; scale: "0-10"; at: string };
    systolic_bp?: { value: number; at: string };
    diastolic_bp?: { value: number; at: string };
    heart_rate?: { value: number; at: string };
    temperature_c?: { value: number; at: string };
    oxygen_sat?: { value: number; at: string };
  };
  symptoms?: Array<{ name: string; severity?: string; at: string }>;
  medications?: Array<{ name: string; adherence: "taken" | "missed" | "reported"; at: string }>;
  notes?: Array<{ text: string; at: string }>;
};

type Extract = {
  updates: ClinicalMemory;
  safety: null | { severity: "warn" | "critical"; reason: string };
};

const RED_FLAG_TERMS = [
  { rx: /chest pain/i, reason: "Reported chest pain" },
  { rx: /can'?t breathe|shortness of breath|difficulty breathing/i, reason: "Reported breathing difficulty" },
  { rx: /passed out|fainted|syncope/i, reason: "Loss of consciousness reported" },
  { rx: /suicid|kill myself/i, reason: "Suicidal ideation flagged" },
];

export function extractFacts(text: string): Extract {
  const now = new Date().toISOString();
  const updates: ClinicalMemory = {};
  let safety: Extract["safety"] = null;

  const bp = text.match(/\b(\d{2,3})\s*[\/over]{1,4}\s*(\d{2,3})\b/i);
  if (bp) {
    const sys = parseInt(bp[1], 10);
    const dia = parseInt(bp[2], 10);
    updates.vitals = { ...(updates.vitals ?? {}), systolic_bp: { value: sys, at: now }, diastolic_bp: { value: dia, at: now } };
    if (sys > 180 || dia > 120) safety = { severity: "critical", reason: `Hypertensive crisis: BP ${sys}/${dia}` };
    else if (sys < 90) safety = { severity: "warn", reason: `Hypotension: systolic ${sys}` };
  }

  const pain = text.match(/pain\s*(?:is|at|of|\-|:)?\s*(\d{1,2})\s*(?:\/|out of)?\s*10?/i);
  if (pain) {
    const v = Math.min(10, parseInt(pain[1], 10));
    updates.vitals = { ...(updates.vitals ?? {}), pain: { value: v, scale: "0-10", at: now } };
    if (v >= 9) safety = safety ?? { severity: "critical", reason: `Severe pain reported (${v}/10)` };
    else if (v >= 7) safety = safety ?? { severity: "warn", reason: `High pain (${v}/10)` };
  }

  const temp = text.match(/(?:temp(?:erature)?|fever)\s*(?:is|of|:)?\s*(\d{2,3}(?:\.\d)?)\s*(c|f|°c|°f)?/i);
  if (temp) {
    let v = parseFloat(temp[1]);
    if ((temp[2] ?? "").toLowerCase().includes("f") || v > 45) v = ((v - 32) * 5) / 9;
    updates.vitals = { ...(updates.vitals ?? {}), temperature_c: { value: Math.round(v * 10) / 10, at: now } };
    if (v >= 39.4) safety = safety ?? { severity: "critical", reason: `High fever ${v.toFixed(1)}°C` };
    else if (v >= 38) safety = safety ?? { severity: "warn", reason: `Fever ${v.toFixed(1)}°C` };
  }

  const hr = text.match(/(?:heart rate|pulse|hr)\s*(?:is|of|:)?\s*(\d{2,3})/i);
  if (hr) {
    const v = parseInt(hr[1], 10);
    updates.vitals = { ...(updates.vitals ?? {}), heart_rate: { value: v, at: now } };
    if (v > 130 || v < 40) safety = safety ?? { severity: "warn", reason: `Abnormal heart rate ${v} bpm` };
  }

  const o2 = text.match(/(?:o2|oxygen|sat|spo2)\s*(?:is|of|:)?\s*(\d{2,3})\s*%?/i);
  if (o2) {
    const v = parseInt(o2[1], 10);
    updates.vitals = { ...(updates.vitals ?? {}), oxygen_sat: { value: v, at: now } };
    if (v < 90) safety = safety ?? { severity: "critical", reason: `Low oxygen saturation ${v}%` };
  }

  const took = text.match(/(?:took|had|taken)\s+(?:my\s+)?([a-z][a-z\-]{2,30})(?:\s+(?:this morning|today|at|earlier))?/i);
  if (took) updates.medications = [{ name: took[1], adherence: "taken", at: now }];
  const missed = text.match(/(?:missed|forgot|skipped)\s+(?:my\s+)?([a-z][a-z\-]{2,30})/i);
  if (missed) updates.medications = [{ name: missed[1], adherence: "missed", at: now }];

  const symptoms: string[] = [];
  ["dizzy", "nauseous", "nausea", "shaky", "swelling", "tired", "fatigued", "cough", "headache", "chills"].forEach((s) => {
    if (new RegExp(`\\b${s}\\b`, "i").test(text)) symptoms.push(s);
  });
  if (symptoms.length) updates.symptoms = symptoms.map((name) => ({ name, at: now }));

  for (const flag of RED_FLAG_TERMS) {
    if (flag.rx.test(text)) {
      safety = { severity: "critical", reason: flag.reason };
      break;
    }
  }

  return { updates, safety };
}

export function mergeMemory(prev: ClinicalMemory, add: ClinicalMemory): ClinicalMemory {
  return {
    vitals: { ...(prev.vitals ?? {}), ...(add.vitals ?? {}) },
    symptoms: [...(prev.symptoms ?? []), ...(add.symptoms ?? [])].slice(-20),
    medications: [...(prev.medications ?? []), ...(add.medications ?? [])].slice(-20),
    notes: [...(prev.notes ?? []), ...(add.notes ?? [])].slice(-20),
  };
}

function composeReply(userText: string, extract: Extract, mem: ClinicalMemory): string {
  if (extract.safety?.severity === "critical") {
    return `⚠️ **Safety escalation triggered.** I've flagged this for your care team: ${extract.safety.reason}. Automated advice is paused until a clinician reviews. If this is an emergency, call your local emergency number now.`;
  }
  const parts: string[] = [];
  if (extract.updates.vitals?.pain) parts.push(`I've noted your pain at ${extract.updates.vitals.pain.value}/10.`);
  if (extract.updates.vitals?.systolic_bp) parts.push(`BP recorded: ${extract.updates.vitals.systolic_bp.value}/${extract.updates.vitals.diastolic_bp?.value ?? "?"}.`);
  if (extract.updates.vitals?.temperature_c) parts.push(`Temperature logged: ${extract.updates.vitals.temperature_c.value}°C.`);
  if (extract.updates.medications?.length) {
    const m = extract.updates.medications[0];
    parts.push(m.adherence === "taken" ? `Marked ${m.name} as taken.` : `Noted you missed ${m.name} — try to take it as soon as you remember.`);
  }
  if (extract.updates.symptoms?.length) parts.push(`Symptoms noted: ${extract.updates.symptoms.map((s) => s.name).join(", ")}.`);

  if (!parts.length) {
    parts.push("Thanks for checking in. Can you tell me a bit more — any pain, medications taken today, or new symptoms?");
  } else {
    if (extract.safety?.severity === "warn") parts.push(`Heads up: ${extract.safety.reason}. I'll keep monitoring; if it worsens I'll notify your team.`);
    const pain = mem.vitals?.pain?.value;
    if (typeof pain === "number" && pain <= 3) parts.push("Your pain trend is looking manageable — keep resting and stay hydrated.");
    parts.push("Anything else changed today?");
  }
  return parts.join(" ");
}

export type AgentEvent =
  | { type: "state"; label: string }
  | { type: "extract"; updates: ClinicalMemory; safety: Extract["safety"] }
  | { type: "token"; text: string }
  | { type: "final"; content: string; safety: Extract["safety"] };

/** Streams agent events for a user turn. Uses VITE_AGENT_WS_URL if set, else runs the local mock. */
export async function* runAgent(userText: string, currentMemory: ClinicalMemory): AsyncGenerator<AgentEvent> {
  const wsUrl = import.meta.env.VITE_AGENT_WS_URL as string | undefined;
  if (wsUrl) {
    // Real backend path — connect and relay JSON events line-by-line.
    const { data: sess } = await supabase.auth.getSession();
    const token = sess.session?.access_token ?? "";
    const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
    const queue: AgentEvent[] = [];
    let done = false;
    let resolver: (() => void) | null = null;
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data) as AgentEvent;
        queue.push(evt);
        resolver?.();
      } catch { /* ignore */ }
    };
    ws.onclose = () => { done = true; resolver?.(); };
    ws.onerror = () => { done = true; resolver?.(); };
    await new Promise<void>((r) => { ws.onopen = () => r(); });
    ws.send(JSON.stringify({ userText, memory: currentMemory }));
    while (!done || queue.length) {
      if (!queue.length) await new Promise<void>((r) => { resolver = r; });
      while (queue.length) yield queue.shift()!;
    }
    return;
  }

  // Mock path
  yield { type: "state", label: "Memory Refiner (qwen-plus)" };
  await sleep(280);
  const extract = extractFacts(userText);
  yield { type: "extract", updates: extract.updates, safety: extract.safety };
  await sleep(180);
  yield { type: "state", label: extract.safety?.severity === "critical" ? "Escalation Node" : "Clinical Responder (qwen-max)" };
  await sleep(220);
  const merged = mergeMemory(currentMemory, extract.updates);
  const reply = composeReply(userText, extract, merged);
  // stream tokens
  const words = reply.split(/(\s+)/);
  for (const w of words) {
    yield { type: "token", text: w };
    await sleep(18 + Math.random() * 22);
  }
  yield { type: "final", content: reply, safety: extract.safety };
}

function sleep(ms: number) { return new Promise((r) => setTimeout(r, ms)); }
