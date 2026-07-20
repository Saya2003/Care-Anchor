import { createFileRoute, Link } from "@tanstack/react-router";
import { Waves, User, Bell, Shield, Database, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { user } = Route.useRouteContext();
  const [downloading, setDownloading] = useState(false);

  async function handleDownloadData() {
    setDownloading(true);
    try {
      const response = await fetch("http://localhost:8000/export/all-data", {
        method: 'GET',
        headers: {
          'Accept': 'application/pdf',
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Download failed:", response.status, errorText);
        throw new Error(`Failed to download data: ${response.status} - ${errorText}`);
      }

      // Get the PDF blob
      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error("Received empty file");
      }
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `careanchor_data_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success("Data exported successfully", {
        description: "Your conversation history has been downloaded as PDF",
      });
    } catch (error) {
      console.error("Failed to download data:", error);
      toast.error("Failed to download data", {
        description: error instanceof Error ? error.message : "Please try again later",
      });
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/60 bg-background">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
                <Waves className="h-4 w-4" />
              </div>
              <span className="font-semibold tracking-tight">CareAnchor</span>
            </Link>
            <nav className="hidden items-center gap-6 md:flex">
              <Link 
                to="/dashboard" 
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Dashboard
              </Link>
              <Link 
                to="/app" 
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Chat
              </Link>
              <Link 
                to="/settings" 
                className="text-sm font-medium text-foreground"
              >
                Settings
              </Link>
            </nav>
          </div>
          <Link to="/logout" className="text-sm text-muted-foreground hover:text-foreground">
            Sign out
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold tracking-tight">Settings</h2>
          <p className="mt-2 text-muted-foreground">
            Manage your account and preferences
          </p>
        </div>

        <div className="space-y-6">
          <Card className="surface-panel">
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="h-5 w-5 text-muted-foreground" />
                <CardTitle>Account</CardTitle>
              </div>
              <CardDescription>
                Your account information and email
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm text-muted-foreground">Email</Label>
                <p className="mt-1 text-sm">{user.email}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">User ID</Label>
                <p className="mt-1 font-mono text-xs text-muted-foreground">{user.id}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="surface-panel">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-muted-foreground" />
                <CardTitle>Notifications</CardTitle>
              </div>
              <CardDescription>
                Manage how CareAnchor notifies you
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="email-notifications">Email notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive check-in reminders</p>
                </div>
                <Switch id="email-notifications" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="critical-alerts">Critical alerts</Label>
                  <p className="text-sm text-muted-foreground">Get notified of urgent health concerns</p>
                </div>
                <Switch id="critical-alerts" defaultChecked />
              </div>
            </CardContent>
          </Card>

          <Card className="surface-panel">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-muted-foreground" />
                <CardTitle>Privacy & Safety</CardTitle>
              </div>
              <CardDescription>
                Control your data and privacy settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="share-anonymous">Share anonymous data</Label>
                  <p className="text-sm text-muted-foreground">Help improve CareAnchor</p>
                </div>
                <Switch id="share-anonymous" />
              </div>
              <div className="pt-2 space-y-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleDownloadData}
                  disabled={downloading}
                  className="w-full sm:w-auto"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {downloading ? "Downloading..." : "Download my data"}
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={async () => {
                    try {
                      const response = await fetch("http://localhost:8000/export/test-pdf");
                      if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = "test_export.pdf";
                        a.click();
                        window.URL.revokeObjectURL(url);
                        toast.success("Test PDF downloaded");
                      } else {
                        toast.error("Test failed");
                      }
                    } catch (error) {
                      toast.error("Test error: " + error);
                    }
                  }}
                  className="w-full sm:w-auto ml-2"
                >
                  Test PDF Export
                </Button>
                <p className="mt-2 text-xs text-muted-foreground">
                  Export all your conversations as a PDF file
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="surface-panel border-destructive/50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-destructive" />
                <CardTitle className="text-destructive">Danger Zone</CardTitle>
              </div>
              <CardDescription>
                Irreversible actions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10">
                Clear all chat history
              </Button>
              <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10">
                Delete account
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
