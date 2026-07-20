import { useEffect, useRef, useState, type RefObject } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageBubble } from "@/components/message-bubble";
import { Send, ShieldAlert, Paperclip, X, FileText, Image as ImageIcon, Mic, MicOff, Volume2, VolumeX, Activity } from "lucide-react";

export type AttachedFile = {
  name: string;
  type: string;
  size: number;
  dataUrl: string;
};

type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type PendingState = {
  user: string;
  assistantStream: string;
};

type Props = {
  messages: Msg[];
  pending: PendingState | null;
  agentState: string | null;
  busy: boolean;
  criticalAlert: { reason: string } | null;
  inputRef: RefObject<HTMLTextAreaElement | null>;
  scrollRef: RefObject<HTMLDivElement | null>;
  onSend: (text: string, files?: AttachedFile[]) => void;
  onDraftChange: (text: string) => void;
  draft: string;
  connected?: boolean;
};

export function ChatPanel({
  messages,
  pending,
  agentState,
  busy,
  criticalAlert,
  inputRef,
  scrollRef,
  onSend,
  onDraftChange,
  draft,
  connected = true,
}: Props) {
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [inputRef]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending?.assistantStream, scrollRef]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendClick();
    }
  }

  function handleSendClick() {
    if (!draft.trim() && attachedFiles.length === 0) return;
    onSend(draft, attachedFiles);
    setAttachedFiles([]);
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newFiles: AttachedFile[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Check file type
      const isImage = file.type.startsWith('image/');
      const isDocument = file.type === 'application/pdf' || 
                        file.type === 'application/msword' ||
                        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                        file.type === 'text/plain';
      
      if (!isImage && !isDocument) {
        alert(`File type not supported: ${file.name}`);
        continue;
      }

      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File too large: ${file.name} (max 10MB)`);
        continue;
      }

      // Convert to base64
      const dataUrl = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });

      newFiles.push({
        name: file.name,
        type: file.type,
        size: file.size,
        dataUrl,
      });
    }

    setAttachedFiles((prev) => [...prev, ...newFiles]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function removeFile(index: number) {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  return (
    <section className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border/60 px-6 py-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Conversation
          </div>
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

      {criticalAlert && (
        <div className="border-b border-destructive/30 bg-destructive/10 px-6 py-3 text-sm text-destructive-foreground">
          <div className="flex items-center gap-2 text-destructive">
            <ShieldAlert className="h-4 w-4" />
            <span className="font-medium">Human-in-the-loop escalation:</span>
            <span>{criticalAlert.reason}</span>
          </div>
        </div>
      )}

      {!connected && (
        <div className="border-b border-orange-500/30 bg-orange-500/10 px-6 py-3 text-sm">
          <div className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
            <ShieldAlert className="h-4 w-4" />
            <span className="font-medium">Disconnected:</span>
            <span>Make sure the backend server is running at localhost:8000</span>
          </div>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && !pending && (
            <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              Tell CareAnchor how you&apos;re feeling. Try:{" "}
              <em>&ldquo;My pain is 4/10, I took my metformin, and I feel a little dizzy.&rdquo;</em>
            </div>
          )}
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} content={m.content} />
          ))}
          {pending && (
            <>
              <MessageBubble role="user" content={pending.user} />
              <MessageBubble
                role="assistant"
                content={pending.assistantStream || "\u2026"}
                streaming
              />
            </>
          )}
        </div>
      </div>

      <div className="border-t border-border/60 bg-card/40 px-6 py-4">
        <div className="mx-auto max-w-3xl">
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm"
                >
                  {file.type.startsWith('image/') ? (
                    <ImageIcon className="h-4 w-4 text-primary" />
                  ) : (
                    <FileText className="h-4 w-4 text-primary" />
                  )}
                  <span className="max-w-[200px] truncate">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(file.size)}
                  </span>
                  <button
                    onClick={() => removeFile(idx)}
                    className="ml-1 rounded-full p-0.5 hover:bg-destructive/10"
                    disabled={busy}
                  >
                    <X className="h-3 w-3 text-destructive" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-end gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              disabled={busy}
              className="h-[52px] w-[52px] shrink-0"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Textarea
              ref={inputRef}
              value={draft}
              onChange={(e) => onDraftChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="How are you feeling? Pain level, meds, vitals \u2014 anything."
              className="min-h-[52px] max-h-40 resize-none"
              disabled={busy}
            />
            <Button
              onClick={handleSendClick}
              disabled={busy || (!draft.trim() && attachedFiles.length === 0)}
              className="h-[52px] px-4 shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Research prototype \u2014 not a substitute for medical care.
          </p>
        </div>
      </div>
    </section>
  );
}
