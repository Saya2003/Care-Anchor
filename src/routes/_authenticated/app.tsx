import { createFileRoute, Link, Outlet, useNavigate, useParams } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Plus, Waves, LogOut, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

export const Route = createFileRoute("/_authenticated/app")({
  component: AppShell,
});

function AppShell() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const params = useParams({ strict: false }) as { threadId?: string };

  const { data: threads } = useQuery({
    queryKey: ["threads"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("threads")
        .select("id, title, updated_at")
        .order("updated_at", { ascending: false });
      if (error) throw error;
      return data;
    },
  });

  const { data: userMeta } = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await supabase.auth.getUser();
      return data.user;
    },
  });

  async function createThread() {
    const { data: user } = await supabase.auth.getUser();
    if (!user.user) return;
    const title = `Check-in · ${new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
    const { data, error } = await supabase
      .from("threads")
      .insert({ user_id: user.user.id, title })
      .select("id")
      .single();
    if (error) { toast.error(error.message); return; }
    await qc.invalidateQueries({ queryKey: ["threads"] });
    navigate({ to: "/app/$threadId", params: { threadId: data.id } });
  }

  async function deleteThread(id: string, e: React.MouseEvent) {
    e.preventDefault(); e.stopPropagation();
    const { error } = await supabase.from("threads").delete().eq("id", id);
    if (error) { toast.error(error.message); return; }
    await qc.invalidateQueries({ queryKey: ["threads"] });
    if (params.threadId === id) navigate({ to: "/app" });
  }

  async function signOut() {
    await qc.cancelQueries();
    qc.clear();
    await supabase.auth.signOut();
    navigate({ to: "/auth", replace: true });
  }

  // Auto-create first thread on empty state at /app
  useEffect(() => {
    if (!threads) return;
    if (!params.threadId && threads.length > 0) {
      navigate({ to: "/app/$threadId", params: { threadId: threads[0].id }, replace: true });
    }
  }, [threads, params.threadId, navigate]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="flex w-72 flex-col border-r border-border/60 bg-card/40">
        <div className="flex items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Waves className="h-4 w-4" />
            </div>
            <span className="font-semibold tracking-tight">CareAnchor</span>
          </Link>
        </div>
        <div className="px-3">
          <Button className="w-full justify-start gap-2" onClick={createThread}>
            <Plus className="h-4 w-4" /> New check-in
          </Button>
        </div>
        <div className="mt-4 flex-1 overflow-y-auto px-2">
          <div className="px-2 py-1 text-xs font-medium text-muted-foreground">Recent</div>
          <ul className="mt-1 space-y-0.5">
            {threads?.map((t) => {
              const active = params.threadId === t.id;
              return (
                <li key={t.id}>
                  <div
                    className={`group flex items-center justify-between rounded-md px-2 py-2 text-sm ${active ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"}`}
                  >
                    <Link
                      to="/app/$threadId"
                      params={{ threadId: t.id }}
                      className="flex-1 truncate"
                    >
                      <div className="truncate font-medium">{t.title}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(t.updated_at), { addSuffix: true })}
                      </div>
                    </Link>
                    <button
                      onClick={(e) => deleteThread(t.id, e)}
                      className="ml-2 opacity-0 transition group-hover:opacity-100"
                      aria-label="Delete thread"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
                    </button>
                  </div>
                </li>
              );
            })}
            {threads && threads.length === 0 && (
              <li className="px-2 py-6 text-center text-sm text-muted-foreground">
                No check-ins yet. Start one above.
              </li>
            )}
          </ul>
        </div>
        <div className="border-t border-border/60 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{userMeta?.email ?? "Patient"}</div>
              <div className="text-xs text-muted-foreground">Signed in</div>
            </div>
            <Button variant="ghost" size="icon" onClick={signOut} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
