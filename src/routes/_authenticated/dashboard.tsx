import { createFileRoute, Link } from "@tanstack/react-router";
import { MessageSquare, Activity, Clock, TrendingUp, Waves, Heart, Thermometer, Zap, AlertTriangle, CheckCircle, TrendingDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/_authenticated/dashboard")({
  component: DashboardPage,
});

type RecentActivity = {
  session_id: string;
  session_name: string;
  timestamp: string;
  message_preview: string;
  message_count: number;
};

type HealthOverview = {
  health_score: number;
  status: string;
  message: string;
  vital_signs: Record<string, { value: string; status: string }>;
  recommendations: string[];
  last_updated: string | null;
  trend: string;
  symptoms_count: number;
  medications_count: number;
};

function DashboardPage() {
  const { user } = Route.useRouteContext();
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(true);
  const [healthOverview, setHealthOverview] = useState<HealthOverview | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  useEffect(() => {
    loadRecentActivity();
    loadHealthOverview();
  }, []);

  async function loadRecentActivity() {
    try {
      const response = await fetch("http://localhost:8000/activity/recent?limit=5");
      if (response.ok) {
        const data = await response.json();
        setRecentActivity(data);
      }
    } catch (error) {
      console.error("Failed to load recent activity:", error);
    } finally {
      setLoadingActivity(false);
    }
  }

  async function loadHealthOverview() {
    try {
      const response = await fetch("http://localhost:8000/analytics/health-overview");
      if (response.ok) {
        const data = await response.json();
        setHealthOverview(data);
      }
    } catch (error) {
      console.error("Failed to load health overview:", error);
    } finally {
      setLoadingHealth(false);
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'normal':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'secondary';
      case 'normal':
        return 'default';
      default:
        return 'outline';
    }
  }

  function getTrendIcon(trend: string) {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'declining':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-blue-500" />;
    }
  }

  function getHealthScoreColor(score: number) {
    if (score >= 90) return "text-green-600";
    if (score >= 75) return "text-blue-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
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
                className="text-sm font-medium text-foreground"
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
                className="text-sm text-muted-foreground hover:text-foreground"
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

      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold tracking-tight">Your Recovery Dashboard</h2>
          <p className="mt-2 text-muted-foreground">
            Track your post-discharge recovery and check in with CareAnchor.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Health Analytics - Main Card */}
          <Card className="surface-panel md:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Health Analytics</CardTitle>
                <div className="flex items-center gap-2">
                  {healthOverview && getTrendIcon(healthOverview.trend)}
                  <Heart className="h-5 w-5 text-red-500" />
                </div>
              </div>
              <CardDescription>
                Your current health status and recovery progress
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingHealth ? (
                <div className="space-y-4">
                  <div className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                  <div className="h-8 bg-muted/50 rounded-lg animate-pulse" />
                </div>
              ) : healthOverview ? (
                <div className="space-y-6">
                  {/* Health Score */}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Health Score</p>
                      <p className={`text-3xl font-bold ${getHealthScoreColor(healthOverview.health_score)}`}>
                        {healthOverview.health_score}/100
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={getStatusColor(healthOverview.status) as any} className="mb-2">
                        {getStatusIcon(healthOverview.status)}
                        <span className="ml-1 capitalize">{healthOverview.status}</span>
                      </Badge>
                      <p className="text-sm text-muted-foreground">{healthOverview.message}</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <Progress value={healthOverview.health_score} className="h-3" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Poor</span>
                      <span>Good</span>
                      <span>Excellent</span>
                    </div>
                  </div>

                  {/* Vital Signs Grid */}
                  {Object.keys(healthOverview.vital_signs).length > 0 && (
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(healthOverview.vital_signs).map(([key, vital]) => (
                        <div key={key} className="border border-border/40 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs text-muted-foreground font-medium">
                              {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </p>
                            {getStatusIcon(vital.status)}
                          </div>
                          <p className="text-sm font-semibold">{vital.value}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Summary Stats */}
                  <div className="flex items-center justify-between pt-2 border-t border-border/40">
                    <div className="text-center">
                      <p className="text-lg font-semibold">{healthOverview.symptoms_count}</p>
                      <p className="text-xs text-muted-foreground">Symptoms Tracked</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{healthOverview.medications_count}</p>
                      <p className="text-xs text-muted-foreground">Medications</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold capitalize">{healthOverview.trend}</p>
                      <p className="text-xs text-muted-foreground">Trend</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Heart className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-sm text-muted-foreground">Start a check-in to see your health analytics</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity - Sidebar */}
          <Card className="surface-panel">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Recent Activity</CardTitle>
                <Clock className="h-5 w-5 text-muted-foreground" />
              </div>
              <CardDescription>
                Your recent check-ins
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingActivity ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : recentActivity.length === 0 ? (
                <div className="text-center py-4">
                  <MessageSquare className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No recent activity yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentActivity.map((activity) => (
                    <Link
                      key={activity.session_id}
                      to="/app"
                      className="block rounded-lg border border-border/40 p-3 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {activity.session_name}
                          </p>
                          <p className="text-xs text-muted-foreground truncate mt-1">
                            {activity.message_preview}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {activity.message_count} messages
                          </p>
                        </div>
                        <MessageSquare className="h-4 w-4 text-muted-foreground shrink-0" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Health Recommendations */}
        {healthOverview && healthOverview.recommendations.length > 0 && (
          <div className="mt-6">
            <Card className="surface-panel">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Health Recommendations</CardTitle>
                  <Zap className="h-5 w-5 text-yellow-500" />
                </div>
                <CardDescription>
                  Personalized guidance based on your current health data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2">
                  {healthOverview.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 border border-border/40 rounded-lg">
                      <div className="mt-0.5">
                        {rec.includes('🚨') || rec.includes('⚠️') ? (
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                        ) : (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                      </div>
                      <p className="text-sm">{rec}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="mt-8">
          <Card className="surface-panel">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Start a Check-in</CardTitle>
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <CardDescription>
                Chat with CareAnchor about how you're feeling today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/app">
                <Button className="w-full">Open Chat</Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 rounded-lg border border-border bg-card p-6">
          <div className="flex items-start gap-4">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold">How CareAnchor Works</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Share how you're feeling in natural conversation. CareAnchor extracts clinical facts,
                maintains your recovery memory, and alerts your care team when needed. Your privacy
                is protected and all data stays secure.
              </p>
              <div className="mt-4">
                <Link to="/app">
                  <Button size="sm">Get Started</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
