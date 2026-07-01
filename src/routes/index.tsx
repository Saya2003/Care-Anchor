import { createFileRoute, Link } from "@tanstack/react-router";
import { Activity, Brain, ShieldAlert, Waves } from "lucide-react";

export const Route = createFileRoute("/")({
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <header className="border-b border-border/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Waves className="h-4 w-4" />
            </div>
            <span className="font-semibold tracking-tight">CareAnchor</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/auth" className="text-sm text-muted-foreground hover:text-foreground">Sign in</Link>
            <Link to="/auth" className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-24">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/70" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </span>
            Autonomous post-discharge assistant
          </div>
          <h1 className="mt-6 text-5xl font-semibold tracking-tight text-foreground sm:text-6xl">
            The days after discharge are the riskiest.<br />
            <span className="text-primary">CareAnchor stays with you.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
            Chat naturally about how you're feeling. CareAnchor extracts clinical facts,
            maintains a persistent recovery memory, and escalates to a human when your
            vitals cross a safe threshold.
          </p>
          <div className="mt-8 flex gap-3">
            <Link to="/auth" className="rounded-md bg-primary px-5 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
              Start a check-in
            </Link>
            <a href="#how" className="rounded-md border border-border bg-card px-5 py-3 text-sm font-medium hover:bg-accent">
              How it works
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="how" className="border-t border-border/60 bg-secondary/40">
        <div className="mx-auto grid max-w-6xl gap-6 px-6 py-20 md:grid-cols-3">
          {[
            { icon: Brain, title: "Persistent clinical memory", body: "Every conversation refines a structured recovery profile — pain trends, meds, vitals — never lost between sessions." },
            { icon: Activity, title: "Real-time state view", body: "A split-screen dashboard shows the memory graph updating as the agent extracts new facts from your words." },
            { icon: ShieldAlert, title: "Human-in-the-loop safety", body: "When metrics cross clinical thresholds, CareAnchor pauses automated advice and notifies your care team." },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title} className="surface-panel p-6">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-border/60 py-8 text-center text-xs text-muted-foreground">
        CareAnchor · Research prototype · Not a substitute for medical care
      </footer>
    </div>
  );
}
