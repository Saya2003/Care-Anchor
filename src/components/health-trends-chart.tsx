import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, Activity, Calendar, BarChart3 } from 'lucide-react';

interface TrendData {
  date: string;
  health_score: number;
  systolic_bp?: number;
  heart_rate?: number;
  sp_o2?: number;
  temperature?: number;
}

interface HealthTrendsProps {
  className?: string;
}

export function HealthTrendsChart({ className }: HealthTrendsProps) {
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string>('health_score');
  const [timeRange, setTimeRange] = useState<string>('7d');

  useEffect(() => {
    loadTrends();
  }, [timeRange]);

  async function loadTrends() {
    setLoading(true);
    try {
      // Simulate API call - replace with actual endpoint
      const response = await fetch(`http://localhost:8000/analytics/trends?range=${timeRange}`);
      if (response.ok) {
        const data = await response.json();
        setTrends(data.trends || generateMockData());
      } else {
        setTrends(generateMockData());
      }
    } catch (error) {
      console.error('Failed to load trends:', error);
      setTrends(generateMockData());
    } finally {
      setLoading(false);
    }
  }

  function generateMockData(): TrendData[] {
    const data: TrendData[] = [];
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Generate realistic health data with some trends
      const baseScore = 75 + Math.sin(i * 0.1) * 10 + Math.random() * 8;
      
      data.push({
        date: date.toISOString().split('T')[0],
        health_score: Math.round(Math.max(60, Math.min(95, baseScore))),
        systolic_bp: Math.round(120 + Math.sin(i * 0.15) * 15 + Math.random() * 10),
        heart_rate: Math.round(75 + Math.sin(i * 0.2) * 8 + Math.random() * 6),
        sp_o2: Math.round(96 + Math.random() * 3),
        temperature: Number((37.0 + Math.sin(i * 0.1) * 0.5 + Math.random() * 0.3).toFixed(1))
      });
    }
    
    return data;
  }

  function getMetricLabel(metric: string): string {
    const labels: Record<string, string> = {
      health_score: 'Health Score',
      systolic_bp: 'Systolic BP',
      heart_rate: 'Heart Rate',
      sp_o2: 'Oxygen Saturation',
      temperature: 'Temperature'
    };
    return labels[metric] || metric;
  }

  function getMetricUnit(metric: string): string {
    const units: Record<string, string> = {
      health_score: '/100',
      systolic_bp: 'mmHg',
      heart_rate: 'bpm',
      sp_o2: '%',
      temperature: '°C'
    };
    return units[metric] || '';
  }

  function getTrendDirection(): 'up' | 'down' | 'stable' {
    if (trends.length < 2) return 'stable';
    
    const recent = trends.slice(-3);
    const values = recent.map(t => (t as any)[selectedMetric]).filter(v => v != null);
    
    if (values.length < 2) return 'stable';
    
    const change = values[values.length - 1] - values[0];
    const threshold = selectedMetric === 'health_score' ? 5 : 2;
    
    if (change > threshold) return 'up';
    if (change < -threshold) return 'down';
    return 'stable';
  }

  function renderChart() {
    if (loading) {
      return <div className="h-48 bg-muted/50 rounded-lg animate-pulse" />;
    }

    if (trends.length === 0) {
      return (
        <div className="h-48 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No trend data available</p>
            <p className="text-xs">Start tracking your health to see trends</p>
          </div>
        </div>
      );
    }

    const values = trends.map(t => (t as any)[selectedMetric]).filter(v => v != null);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;

    return (
      <div className="h-48 relative">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground w-12">
          <span>{maxVal}{getMetricUnit(selectedMetric)}</span>
          <span>{Math.round((maxVal + minVal) / 2)}</span>
          <span>{minVal}{getMetricUnit(selectedMetric)}</span>
        </div>

        {/* Chart area */}
        <div className="ml-12 h-full relative">
          <svg className="w-full h-full">
            {/* Grid lines */}
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            {/* Trend line */}
            <polyline
              fill="none"
              stroke="rgb(59, 130, 246)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={trends.map((trend, index) => {
                const value = (trend as any)[selectedMetric];
                if (value == null) return '';
                
                const x = (index / (trends.length - 1)) * 100;
                const y = 100 - ((value - minVal) / range) * 90 - 5;
                return `${x}%,${y}%`;
              }).join(' ')}
            />

            {/* Data points */}
            {trends.map((trend, index) => {
              const value = (trend as any)[selectedMetric];
              if (value == null) return null;
              
              const x = (index / (trends.length - 1)) * 100;
              const y = 100 - ((value - minVal) / range) * 90 - 5;
              
              return (
                <g key={index}>
                  <circle
                    cx={`${x}%`}
                    cy={`${y}%`}
                    r="4"
                    fill="rgb(59, 130, 246)"
                    stroke="white"
                    strokeWidth="2"
                  />
                  {/* Tooltip on hover */}
                  <circle
                    cx={`${x}%`}
                    cy={`${y}%`}
                    r="8"
                    fill="transparent"
                    className="hover:fill-blue-500/20 transition-colors cursor-pointer"
                    title={`${trend.date}: ${value}${getMetricUnit(selectedMetric)}`}
                  />
                </g>
              );
            })}
          </svg>

          {/* X-axis labels */}
          <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-muted-foreground">
            <span>{trends[0]?.date}</span>
            {trends.length > 1 && <span>{trends[trends.length - 1]?.date}</span>}
          </div>
        </div>
      </div>
    );
  }

  const trendDirection = getTrendDirection();

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Health Trends
            </CardTitle>
            <CardDescription>
              Track your recovery progress over time
            </CardDescription>
          </div>
          <Badge variant={trendDirection === 'up' ? 'default' : trendDirection === 'down' ? 'destructive' : 'secondary'}>
            {trendDirection === 'up' ? <TrendingUp className="h-3 w-3 mr-1" /> : 
             trendDirection === 'down' ? <TrendingDown className="h-3 w-3 mr-1" /> :
             <Activity className="h-3 w-3 mr-1" />}
            {trendDirection === 'up' ? 'Improving' : trendDirection === 'down' ? 'Declining' : 'Stable'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Metric:</span>
            <select 
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="text-sm border border-border rounded px-2 py-1 bg-background"
            >
              <option value="health_score">Health Score</option>
              <option value="systolic_bp">Blood Pressure</option>
              <option value="heart_rate">Heart Rate</option>
              <option value="sp_o2">Oxygen Saturation</option>
              <option value="temperature">Temperature</option>
            </select>
          </div>
          
          <div className="flex items-center gap-1">
            {['7d', '30d', '90d'].map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setTimeRange(range)}
                className="h-8"
              >
                {range}
              </Button>
            ))}
          </div>
        </div>

        {/* Chart */}
        {renderChart()}

        {/* Summary */}
        {trends.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/40">
            <div className="grid grid-cols-3 gap-4 text-center text-sm">
              <div>
                <p className="text-muted-foreground">Current</p>
                <p className="font-semibold">
                  {(trends[trends.length - 1] as any)[selectedMetric] || 'N/A'}{getMetricUnit(selectedMetric)}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Average</p>
                <p className="font-semibold">
                  {Math.round(trends.reduce((sum, t) => sum + ((t as any)[selectedMetric] || 0), 0) / trends.length)}{getMetricUnit(selectedMetric)}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Trend</p>
                <p className={`font-semibold ${
                  trendDirection === 'up' ? 'text-green-600' : 
                  trendDirection === 'down' ? 'text-red-600' : 'text-blue-600'
                }`}>
                  {trendDirection === 'up' ? 'Improving' : trendDirection === 'down' ? 'Declining' : 'Stable'}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}