import { createFileRoute, redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/_authenticated/logout")({
  loader: async () => {
    await supabase.auth.signOut();
    throw redirect({ to: "/" });
  },
});
