import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { runAgent, mergeMemory, type ClinicalMemory, type AgentEvent } from "@/lib/agent";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ShieldAlert, Send, Brain, Activity, Pill, ThermometerSun, HeartPulse, Wind, Gauge, CircleDot } from "lucide-react";

export const Route = createFileRoute("/_authenticated/app/$threadId")({
  component: ThreadPage,
});

type Msg = { id: string; role: "user" | "assistant"; content: string; created_at: string };

function ThreadPage() {
  const { threadId } = useParams({ from: "/_authenticated/app/$threadId" });
  const qc = useQueryClient();

  const { data: messages } = useQuery({
    queryKey: ["messages", threadId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("messages")
        .select("id, role, content, created_at")
        .eq("thread_id", threadId)
        .order("created_at", { ascending: true });
      if (error) throw error;
      return data as Msg[];
    },
  });

  const { data: memory } = useQuery({
    queryKey: ["memory"],
    queryFn: async () => {
      const { data, error } = await supabase.from("clinical_memory").select("data").maybeSingle();
      if (error) throw error;
      return (data?.data ?? {}) as ClinicalMemory;
    },
  });

  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("safety_alerts")
        .select("id, severity, reason, acknowledged, created_at")
        .order("created_at", { ascending: false })
        .limit(5);
      if (error) throw error;
      return data;
    },
  });

  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<{ user: string; assistantStream: string } | null>(null);
  const [agentState, setAgentState] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, [threadId]);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending?.assistantStream]);

  async function send() {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    setBusy(true);
    setPending({ user: text, assistantStream: "" });

    const { data: u } = await supabase.auth.getUser();
    if (!u.user) { setBusy(false); return; }

    // save user message
    const { error: uerr } = await supabase.from("messages").insert({
      thread_id: threadId, user_id: u.user.id, role: "user", content: text,
    });
    if (uerr) { toast.error(uerr.message); setBusy(false); setPending(null); return; }
    await qc.invalidateQueries({ queryKey: ["messages", threadId] });

    let assistantText = "";
    let finalMem = memory ?? {};
    let safety: AgentEvent extends { safety: infer S } ? S : null = null;

    try {
      for await (const evt of runAgent(text, memory ?? {})) {
        if (evt.type === "state") setAgentState(evt.label);
        else if (evt.type === "extract") {
          finalMem = mergeMemory(finalMem, evt.updates);
          safety = evt.safety;
          // persist memory as we go
          await supabase.from("clinical_memory").upsert({ user_id: u.user.id, data: finalMem });
          qc.setQueryData(["memory"], finalMem);
          if (evt.safety) {
            await supabase.from("safety_alerts").insert({
              user_id: u.user.id, thread_id: threadId,
              severity: evt.safety.severity, reason: evt.safety.reason,
            });
            qc.invalidateQueries({ queryKey: ["alerts"] });
            toast.warning(`Safety: ${evt.safety.reason}`);
          }
        } else if (evt.type === "token") {
          assistantText += evt.text;
          setPending((p) => (p ? { ...p, assistantStream: assistantText } : p));
        } else if (evt.type === "final") {
          assistantText = evt.content;
        }
      }
      await supabase.from("messages").insert({
        thread_id: threadId, user_id: u.user.id, role: "assistant",
        content: assistantText, metadata: { safety },
      });
      await supabase.from("threads").update({ updated_at: new Date().toISOString() }).eq("id", threadId);
      qc.invalidateQueries({ queryKey: ["threads"] });
      qc.invalidateQueries({ queryKey: ["messages", threadId] });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Agent error");
    } finally {
      setPending(null);
      setAgentState(null);
      setBusy(false);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }

  const critical = alerts?.find((a) => a.severity === "critical" && !a.acknowledged);

  return (
    <div className="grid h-full w-full grid-cols-1 lg:grid-cols-[1fr_420px]">
      {/* Chat */}
      <section className="flex h-full flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div>
            <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Conversation</div>
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

        {critical && (
          <div className="border-b border-destructive/30 bg-destructive/10 px-6 py-3 text-sm text-destructive-foreground">
            <div className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-4 w-4" />
              <span className="font-medium">Human-in-the-loop escalation:</span>
              <span>{critical.reason}</span>
            </div>
          </div>
        )}

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages?.length === 0 && !pending && (
              <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                Tell CareAnchor how you're feeling. Try:{" "}
                <em>"My pain is 4/10, I took my metformin, and I feel a little dizzy."</em>
              </div>
            )}
            {messages?.map((m) => <Bubble key={m.id} role={m.role} content={m.content} />)}
            {pending && (
              <>
                <Bubble role="user" content={pending.user} />
                <Bubble role="assistant" content={pending.assistantStream || "…"} streaming />
              </>
            )}
          </div>
        </div>

        <div className="border-t border-border/60 bg-card/40 px-6 py-4">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <Textarea
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder="How are you feeling? Pain level, meds, vitals — anything."
              className="min-h-[52px] max-h-40 resize-none"
              disabled={busy}
            />
            <Button onClick={send} disabled={busy || !draft.trim()} className="h-[52px] px-4">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">
            Research prototype — not a substitute for medical care.
          </p>
        </div>
      </section>

      {/* Memory panel */}
      <MemoryPanel memory={memory ?? {}} alerts={alerts ?? []} />
    </div>
  );
}

function Bubble({ role, content, streaming }: { role: "user" | "assistant"; content: string; streaming?: boolean }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "border border-border bg-card text-card-foreground"
        }`}
      >
        {content}
        {streaming && <span className="ml-1 inline-block h-3 w-1.5 animate-pulse bg-current align-middle" />}
      </div>
    </div>
  );
}

function MemoryPanel({ memory, alerts }: { memory: ClinicalMemory; alerts: Array<{ id: string; severity: string; reason: string; created_at: string }> }) {
  const vitals = memory.vitals ?? {};
  const meds = memory.medications ?? [];
  const syms = memory.symptoms ?? [];

  const vitalItems = useMemo(() => [
    { key: "pain", label: "Pain", icon: Gauge, value: vitals.pain ? `${vitals.pain.value}/10` : "—", danger: (vitals.pain?.value ?? 0) >= 7 },
    { key: "bp", label: "Blood pressure", icon: HeartPulse, value: vitals.systolic_bp ? `${vitals.systolic_bp.value}/${vitals.diastolic_bp?.value ?? "?"}` : "—", danger: (vitals.systolic_bp?.value ?? 0) > 180 },
    { key: "hr", label: "Heart rate", icon: Activity, value: vitals.heart_rate ? `${vitals.heart_rate.value} bpm` : "—", danger: (vitals.heart_rate?.value ?? 0) > 130 },
    { key: "temp", label: "Temperature", icon: ThermometerSun, value: vitals.temperature_c ? `${vitals.temperature_c.value}°C` : "—", danger: (vitals.temperature_c?.value ?? 0) >= 38 },
    { key: "o2", label: "Oxygen sat", icon: Wind, value: vitals.oxygen_sat ? `${vitals.oxygen_sat.value}%` : "—", danger: (vitals.oxygen_sat?.value ?? 100) < 92 },
  ], [vitals]);

  return (
    <aside className="hidden h-full flex-col border-l border-border/60 bg-secondary/30 lg:flex">
      <header className="flex items-center gap-2 border-b border-border/60 px-5 py-4">
        <Brain className="h-4 w-4 text-primary" />
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Clinical Memory</div>
          <div className="text-sm">Persistent recovery state</div>
        </div>
      </header>
      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        <section>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Vitals</div>
          <div className="grid grid-cols-2 gap-2">
            {vitalItems.map((v) => (
              <div key={v.key} className={`surface-panel p-3 ${v.danger ? "ring-1 ring-destructive/40" : ""}`}>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <v.icon className="h-3.5 w-3.5" /> {v.label}
                </div>
                <div className={`mt-1 text-lg font-semibold tabular-nums ${v.danger ? "text-destructive" : ""}`}>
                  {v.value}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Pill className="h-3.5 w-3.5" /> Medications
          </div>
          {meds.length === 0 ? (
            <div className="text-xs text-muted-foreground">Not tracked yet.</div>
          ) : (
            <ul className="space-y-1.5">
              {meds.slice(-6).reverse().map((m, i) => (
                <li key={i} className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-2 text-sm">
                  <span className="capitalize">{m.name}</span>
                  <Badge variant={m.adherence === "taken" ? "default" : "destructive"} className="text-xs">
                    {m.adherence}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <CircleDot className="h-3.5 w-3.5" /> Symptoms
          </div>
          {syms.length === 0 ? (
            <div className="text-xs text-muted-foreground">None reported.</div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {Array.from(new Set(syms.map((s) => s.name))).map((n) => (
                <Badge key={n} variant="secondary" className="capitalize">{n}</Badge>
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <ShieldAlert className="h-3.5 w-3.5" /> Safety events
          </div>
          {alerts.length === 0 ? (
            <div className="text-xs text-muted-foreground">No escalations.</div>
          ) : (
            <ul className="space-y-1.5">
              {alerts.map((a) => (
                <li key={a.id} className={`rounded-md border p-2.5 text-xs ${a.severity === "critical" ? "border-destructive/40 bg-destructive/10" : "border-warning/40 bg-warning/10"}`}>
                  <div className="font-medium capitalize">{a.severity}</div>
                  <div className="text-muted-foreground">{a.reason}</div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </aside>
  );
}
