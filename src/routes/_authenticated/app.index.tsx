import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Plus, HeartPulse } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/app/")({
  component: EmptyState,
});

function EmptyState() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  async function createThread() {
    const { data: user } = await supabase.auth.getUser();
    if (!user.user) return;
    const title = `Check-in · ${new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
    const { data, error } = await supabase.from("threads").insert({ user_id: user.user.id, title }).select("id").single();
    if (error) { toast.error(error.message); return; }
    await qc.invalidateQueries({ queryKey: ["threads"] });
    navigate({ to: "/app/$threadId", params: { threadId: data.id } });
  }
  return (
    <div className="grid h-full place-items-center p-8">
      <div className="text-center">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-primary/10 text-primary">
          <HeartPulse className="h-8 w-8" />
        </div>
        <h2 className="mt-6 text-2xl font-semibold tracking-tight">How are you feeling today?</h2>
        <p className="mt-2 max-w-md text-muted-foreground">
          Start a check-in and CareAnchor will begin building your recovery memory.
        </p>
        <Button className="mt-6 gap-2" onClick={createThread}>
          <Plus className="h-4 w-4" /> New check-in
        </Button>
      </div>
    </div>
  );
}
