import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  CheckSquare,
  AlertTriangle,
  MoreVertical,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export type ChatSession = {
  session_id: string;
  session_name: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
};

type Props = {
  currentSessionId: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  refreshTrigger?: number; // Optional prop to trigger refresh
};

export function ChatHistorySidebar({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  refreshTrigger,
}: Props) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [loading, setLoading] = useState(true);
  const [bulkDeleteMode, setBulkDeleteMode] = useState(false);
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(
    new Set()
  );
  
  // Delete dialog states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);

  useEffect(() => {
    loadSessions();
  }, [refreshTrigger]); // Refresh when trigger changes

  async function loadSessions() {
    try {
      const response = await fetch("http://localhost:8000/sessions");
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRename(sessionId: string, newName: string) {
    if (!newName.trim()) return;

    try {
      const response = await fetch(
        `http://localhost:8000/sessions/${sessionId}/name`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_name: newName }),
        }
      );

      if (response.ok) {
        setSessions((prev) =>
          prev.map((s) =>
            s.session_id === sessionId ? { ...s, session_name: newName } : s
          )
        );
        setEditingId(null);
      }
    } catch (error) {
      console.error("Failed to rename session:", error);
    }
  }

  function confirmDelete(sessionId: string) {
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  }

  async function handleDelete() {
    if (!sessionToDelete) return;

    try {
      const response = await fetch(
        `http://localhost:8000/sessions/${sessionToDelete}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionToDelete));
        
        // If deleting current session, create new chat
        if (sessionToDelete === currentSessionId) {
          onNewChat();
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    } finally {
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
    }
  }

  function startEditing(session: ChatSession) {
    setEditingId(session.session_id);
    setEditName(session.session_name);
  }

  function cancelEditing() {
    setEditingId(null);
    setEditName("");
  }

  function toggleBulkDeleteMode() {
    setBulkDeleteMode(!bulkDeleteMode);
    setSelectedSessions(new Set());
  }

  function toggleSessionSelection(sessionId: string) {
    const newSelected = new Set(selectedSessions);
    if (newSelected.has(sessionId)) {
      newSelected.delete(sessionId);
    } else {
      newSelected.add(sessionId);
    }
    setSelectedSessions(newSelected);
  }

  function selectAllSessions() {
    setSelectedSessions(new Set(sessions.map((s) => s.session_id)));
  }

  function deselectAllSessions() {
    setSelectedSessions(new Set());
  }

  function confirmBulkDelete() {
    if (selectedSessions.size === 0) return;
    setBulkDeleteDialogOpen(true);
  }

  async function handleBulkDelete() {
    if (selectedSessions.size === 0) return;

    try {
      const response = await fetch(
        "http://localhost:8000/sessions/bulk-delete",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_ids: Array.from(selectedSessions),
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`Deleted ${result.deleted_count} conversations`);

        // Remove deleted sessions from list
        setSessions((prev) =>
          prev.filter((s) => !selectedSessions.has(s.session_id))
        );

        // If current session was deleted, create new chat
        if (selectedSessions.has(currentSessionId)) {
          onNewChat();
        }

        // Exit bulk delete mode
        setBulkDeleteMode(false);
        setSelectedSessions(new Set());
      }
    } catch (error) {
      console.error("Failed to bulk delete sessions:", error);
    } finally {
      setBulkDeleteDialogOpen(false);
    }
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-border/60 bg-secondary/30">
      {/* Header */}
      <div className="border-b border-border/60 p-4 space-y-2">
        <Button
          onClick={onNewChat}
          className="w-full justify-start gap-2"
          variant="default"
        >
          <Plus className="h-4 w-4" />
          New Conversation
        </Button>

        {/* Bulk delete controls */}
        {!bulkDeleteMode ? (
          <Button
            onClick={toggleBulkDeleteMode}
            className="w-full justify-start gap-2"
            variant="outline"
            size="sm"
          >
            <CheckSquare className="h-4 w-4" />
            Select Multiple
          </Button>
        ) : (
          <div className="space-y-2">
            <div className="flex gap-2">
              <Button
                onClick={selectAllSessions}
                className="flex-1"
                variant="outline"
                size="sm"
              >
                Select All
              </Button>
              <Button
                onClick={deselectAllSessions}
                className="flex-1"
                variant="outline"
                size="sm"
              >
                Clear
              </Button>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={confirmBulkDelete}
                className="flex-1"
                variant="destructive"
                size="sm"
                disabled={selectedSessions.size === 0}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete ({selectedSessions.size})
              </Button>
              <Button
                onClick={toggleBulkDeleteMode}
                className="flex-1"
                variant="outline"
                size="sm"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {loading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Loading conversations...
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                className={`group relative rounded-lg transition-colors ${
                  session.session_id === currentSessionId
                    ? "bg-primary/10 border border-primary/20"
                    : "hover:bg-muted/50 border border-transparent"
                } ${
                  bulkDeleteMode && selectedSessions.has(session.session_id)
                    ? "ring-2 ring-primary"
                    : ""
                }`}
              >
                {editingId === session.session_id ? (
                  <div className="flex items-center gap-1 p-3">
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleRename(session.session_id, editName);
                        } else if (e.key === "Escape") {
                          cancelEditing();
                        }
                      }}
                      className="h-7 text-sm"
                      autoFocus
                    />
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 shrink-0"
                      onClick={() =>
                        handleRename(session.session_id, editName)
                      }
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 shrink-0"
                      onClick={cancelEditing}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start gap-2 p-3 pr-10">
                      {/* Bulk delete checkbox */}
                      {bulkDeleteMode && (
                        <div className="pt-0.5">
                          <Checkbox
                            checked={selectedSessions.has(session.session_id)}
                            onCheckedChange={() =>
                              toggleSessionSelection(session.session_id)
                            }
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      )}

                      {/* Message icon and content */}
                      <div
                        onClick={() => {
                          if (bulkDeleteMode) {
                            toggleSessionSelection(session.session_id);
                          } else {
                            onSessionSelect(session.session_id);
                          }
                        }}
                        className="flex items-start gap-2 flex-1 min-w-0 cursor-pointer"
                      >
                        <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium">
                            {session.session_name}
                          </div>
                          {session.last_message_preview && (
                            <div className="mt-1 truncate text-xs text-muted-foreground">
                              {session.last_message_preview}
                            </div>
                          )}
                          <div className="mt-1 text-xs text-muted-foreground">
                            {session.message_count} messages
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Three dots menu - absolute positioned on the right */}
                    {!bulkDeleteMode && (
                      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8 hover:bg-muted rounded-md"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditing(session);
                              }}
                              className="cursor-pointer"
                            >
                              <Edit2 className="mr-2 h-4 w-4" />
                              Rename conversation
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                confirmDelete(session.session_id);
                              }}
                              className="cursor-pointer text-destructive focus:text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete conversation
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Single Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-destructive/10 text-destructive">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <AlertDialogTitle>Delete Conversation</AlertDialogTitle>
                <AlertDialogDescription className="mt-1">
                  This action cannot be undone. This will permanently delete
                  this conversation and all associated messages.
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Conversation
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bulk Delete Confirmation Dialog */}
      <AlertDialog
        open={bulkDeleteDialogOpen}
        onOpenChange={setBulkDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-destructive/10 text-destructive">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <AlertDialogTitle>
                  Delete {selectedSessions.size} Conversation
                  {selectedSessions.size > 1 ? "s" : ""}
                </AlertDialogTitle>
                <AlertDialogDescription className="mt-1">
                  This action cannot be undone. This will permanently delete{" "}
                  {selectedSessions.size} conversation
                  {selectedSessions.size > 1 ? "s" : ""} and all associated
                  messages.
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete {selectedSessions.size} Conversation
              {selectedSessions.size > 1 ? "s" : ""}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
