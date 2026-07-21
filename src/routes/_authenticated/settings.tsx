import { createFileRoute, Link } from "@tanstack/react-router";
import { Waves, User, Bell, Shield, Database, Download, Phone, Plus, Trash2, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/settings")({
  component: SettingsPage,
});

interface EmergencyContact {
  id: number;
  user_id: string;
  name: string;
  phone: string;
  email?: string;
  relationship: string;
  is_primary: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface EmergencyContactForm {
  name: string;
  phone: string;
  email: string;
  relationship: string;
  is_primary: boolean;
  notes: string;
}

function SettingsPage() {
  const { user } = Route.useRouteContext();
  const [downloading, setDownloading] = useState(false);
  const [emergencyContacts, setEmergencyContacts] = useState<EmergencyContact[]>([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [editingContact, setEditingContact] = useState<EmergencyContact | null>(null);
  const [contactForm, setContactForm] = useState<EmergencyContactForm>({
    name: "",
    phone: "",
    email: "",
    relationship: "",
    is_primary: false,
    notes: "",
  });

  // Load emergency contacts on component mount
  useEffect(() => {
    loadEmergencyContacts();
  }, [user.id]);

  async function loadEmergencyContacts() {
    try {
      const response = await fetch(`http://localhost:8000/emergency-contacts?user_id=${user.id}`);
      if (response.ok) {
        const contacts = await response.json();
        setEmergencyContacts(contacts);
      }
    } catch (error) {
      console.error("Failed to load emergency contacts:", error);
      toast.error("Failed to load emergency contacts");
    }
  }

  async function saveEmergencyContact() {
    try {
      const url = editingContact 
        ? `http://localhost:8000/emergency-contacts/${editingContact.id}?user_id=${user.id}`
        : `http://localhost:8000/emergency-contacts?user_id=${user.id}`;
      
      const method = editingContact ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(contactForm),
      });

      if (response.ok) {
        await loadEmergencyContacts();
        setShowAddContact(false);
        setEditingContact(null);
        setContactForm({
          name: "",
          phone: "",
          email: "",
          relationship: "",
          is_primary: false,
          notes: "",
        });
        toast.success(editingContact ? "Contact updated" : "Contact added");
      } else {
        throw new Error("Failed to save contact");
      }
    } catch (error) {
      console.error("Failed to save emergency contact:", error);
      toast.error("Failed to save contact");
    }
  }

  async function deleteEmergencyContact(contactId: number) {
    try {
      const response = await fetch(
        `http://localhost:8000/emergency-contacts/${contactId}?user_id=${user.id}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        await loadEmergencyContacts();
        toast.success("Contact deleted");
      } else {
        throw new Error("Failed to delete contact");
      }
    } catch (error) {
      console.error("Failed to delete emergency contact:", error);
      toast.error("Failed to delete contact");
    }
  }

  function openEditContact(contact: EmergencyContact) {
    setEditingContact(contact);
    setContactForm({
      name: contact.name,
      phone: contact.phone,
      email: contact.email || "",
      relationship: contact.relationship,
      is_primary: contact.is_primary,
      notes: contact.notes || "",
    });
    setShowAddContact(true);
  }

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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Phone className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <CardTitle>Emergency Contacts</CardTitle>
                    <CardDescription>
                      Manage contacts for emergency situations
                    </CardDescription>
                  </div>
                </div>
                <Dialog open={showAddContact} onOpenChange={setShowAddContact}>
                  <DialogTrigger asChild>
                    <Button 
                      size="sm" 
                      onClick={() => {
                        setEditingContact(null);
                        setContactForm({
                          name: "",
                          phone: "",
                          email: "",
                          relationship: "",
                          is_primary: false,
                          notes: "",
                        });
                      }}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Contact
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {editingContact ? "Edit Emergency Contact" : "Add Emergency Contact"}
                      </DialogTitle>
                      <DialogDescription>
                        This contact will be notified in case of a medical emergency.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="name">Full Name</Label>
                        <Input
                          id="name"
                          value={contactForm.name}
                          onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                          placeholder="Enter full name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                          id="phone"
                          type="tel"
                          value={contactForm.phone}
                          onChange={(e) => setContactForm({...contactForm, phone: e.target.value})}
                          placeholder="+1 (555) 123-4567"
                        />
                      </div>
                      <div>
                        <Label htmlFor="email">Email (Optional)</Label>
                        <Input
                          id="email"
                          type="email"
                          value={contactForm.email}
                          onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                          placeholder="email@example.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="relationship">Relationship</Label>
                        <Select 
                          value={contactForm.relationship} 
                          onValueChange={(value) => setContactForm({...contactForm, relationship: value})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select relationship" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="spouse">Spouse/Partner</SelectItem>
                            <SelectItem value="parent">Parent</SelectItem>
                            <SelectItem value="child">Child</SelectItem>
                            <SelectItem value="sibling">Sibling</SelectItem>
                            <SelectItem value="friend">Friend</SelectItem>
                            <SelectItem value="doctor">Doctor</SelectItem>
                            <SelectItem value="caregiver">Caregiver</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="is-primary"
                          checked={contactForm.is_primary}
                          onCheckedChange={(checked) => setContactForm({...contactForm, is_primary: checked})}
                        />
                        <Label htmlFor="is-primary">Primary emergency contact</Label>
                      </div>
                      <div>
                        <Label htmlFor="notes">Notes (Optional)</Label>
                        <Textarea
                          id="notes"
                          value={contactForm.notes}
                          onChange={(e) => setContactForm({...contactForm, notes: e.target.value})}
                          placeholder="Additional notes or instructions..."
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowAddContact(false)}>
                        Cancel
                      </Button>
                      <Button onClick={saveEmergencyContact}>
                        {editingContact ? "Update" : "Add"} Contact
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {emergencyContacts.length === 0 ? (
                <div className="text-center py-6">
                  <Phone className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">
                    No emergency contacts added yet.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Add contacts who should be notified in case of a medical emergency.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {emergencyContacts.map((contact) => (
                    <div 
                      key={contact.id} 
                      className={`p-3 rounded-lg border ${contact.is_primary ? 'border-primary bg-primary/5' : 'border-border'}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{contact.name}</h4>
                            {contact.is_primary && (
                              <span className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded">
                                Primary
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {contact.relationship} • {contact.phone}
                          </p>
                          {contact.email && (
                            <p className="text-sm text-muted-foreground">{contact.email}</p>
                          )}
                          {contact.notes && (
                            <p className="text-xs text-muted-foreground mt-1">{contact.notes}</p>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => openEditContact(contact)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => deleteEmergencyContact(contact.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
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
