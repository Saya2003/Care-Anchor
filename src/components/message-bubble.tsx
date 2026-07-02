import { cn } from "@/lib/utils";

type BubbleProps = {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
};

export function MessageBubble({ role, content, streaming }: BubbleProps) {
  const isUser = role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground"
            : "border border-border bg-card text-card-foreground",
        )}
      >
        {content}
        {streaming && (
          <span className="ml-1 inline-block h-3 w-1.5 animate-pulse bg-current align-middle" />
        )}
      </div>
    </div>
  );
}
