import { useMemo } from "react";
import {
  Activity,
  Brain,
  CircleDot,
  Gauge,
  HeartPulse,
  Pill,
  ShieldAlert,
  ThermometerSun,
  Wind,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

export type Vitals = {
  systolic_bp?: { value: number };
  diastolic_bp?: { value: number };
  heart_rate?: { value: number };
  temperature?: { value: number };
  sp_o2?: { value: number };
  pain?: { value: number; scale?: string };
};

export type Medication = {
  name: string;
  dosage?: string;
  frequency?: string;
};

export type Symptom = {
  description: string;
  severity?: string;
  onset?: string;
};

export type SafetyAlert = {
  id: string;
  severity: string;
  reason: string;
  created_at: string;
};

export type ClinicalProfile = {
  vitals?: Vitals;
  medications?: Medication[];
  symptoms?: Symptom[];
  care_plan?: {
    follow_up?: string;
    restrictions?: string[];
    next_appointment?: string;
  };
};

type Props = {
  profile: ClinicalProfile;
  alerts?: SafetyAlert[];
};

export function ClinicalMemoryViewer({ profile, alerts = [] }: Props) {
  const vitals = profile.vitals ?? {};
  const meds = profile.medications ?? [];
  const syms = profile.symptoms ?? [];

  const vitalItems = useMemo(
    () => [
      {
        key: "pain",
        label: "Pain",
        icon: Gauge,
        value: vitals.pain ? `${vitals.pain.value}/10` : "\u2014",
        danger: (vitals.pain?.value ?? 0) >= 7,
      },
      {
        key: "bp",
        label: "Blood pressure",
        icon: HeartPulse,
        value:
          vitals.systolic_bp
            ? `${vitals.systolic_bp.value}/${vitals.diastolic_bp?.value ?? "?"}`
            : "\u2014",
        danger: (vitals.systolic_bp?.value ?? 0) > 180,
      },
      {
        key: "hr",
        label: "Heart rate",
        icon: Activity,
        value: vitals.heart_rate ? `${vitals.heart_rate.value} bpm` : "\u2014",
        danger: (vitals.heart_rate?.value ?? 0) > 130,
      },
      {
        key: "temp",
        label: "Temperature",
        icon: ThermometerSun,
        value: vitals.temperature ? `${vitals.temperature.value}\u00b0C` : "\u2014",
        danger: (vitals.temperature?.value ?? 0) >= 38,
      },
      {
        key: "o2",
        label: "Oxygen sat",
        icon: Wind,
        value: vitals.sp_o2 ? `${vitals.sp_o2.value}%` : "\u2014",
        danger: (vitals.sp_o2?.value ?? 100) < 92,
      },
    ],
    [vitals],
  );

  return (
    <aside className="hidden h-full flex-col border-l border-border/60 bg-secondary/30 lg:flex">
      <header className="flex items-center gap-2 border-b border-border/60 px-5 py-4">
        <Brain className="h-4 w-4 text-primary" />
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Clinical Memory
          </div>
          <div className="text-sm">Persistent recovery state</div>
        </div>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        <section>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Vitals
          </div>
          <div className="grid grid-cols-2 gap-2">
            {vitalItems.map((v) => (
              <div
                key={v.key}
                className={`surface-panel p-3 ${v.danger ? "ring-1 ring-destructive/40" : ""}`}
              >
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <v.icon className="h-3.5 w-3.5" /> {v.label}
                </div>
                <div
                  className={`mt-1 text-lg font-semibold tabular-nums ${v.danger ? "text-destructive" : ""}`}
                >
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
              {meds.map((m, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-2 text-sm"
                >
                  <span className="capitalize">{m.name}</span>
                  {m.dosage && (
                    <span className="text-xs text-muted-foreground">{m.dosage}</span>
                  )}
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
              {Array.from(new Set(syms.map((s) => s.description))).map((n) => (
                <Badge key={n} variant="secondary" className="capitalize">
                  {n}
                </Badge>
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
                <li
                  key={a.id}
                  className={`rounded-md border p-2.5 text-xs ${
                    a.severity === "critical"
                      ? "border-destructive/40 bg-destructive/10"
                      : "border-warning/40 bg-warning/10"
                  }`}
                >
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
