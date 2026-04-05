/**
 * Analytics dashboard for admins.
 */
'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components/ui';
import { Activity, TrendingUp, Users, Zap } from 'lucide-react';

interface SystemStats {
  event_counts: Record<string, number>;
  total_events: number;
  unique_users: number;
  api_calls: number;
  error_rate: number;
  avg_response_time_ms: number;
}

interface EndpointStats {
  endpoint: string;
  method: string;
  count: number;
  avg_response_time_ms: number;
}

export default function AnalyticsPage() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [topEndpoints, setTopEndpoints] = useState<EndpointStats[]>([]);
  const [slowestEndpoints, setSlowestEndpoints] = useState<EndpointStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [stats, top, slow] = await Promise.all([
        apiClient.get<SystemStats>('/api/v1/analytics/system/stats'),
        apiClient.get<{ endpoints: EndpointStats[] }>('/api/v1/analytics/performance/endpoints?limit=10'),
        apiClient.get<{ endpoints: EndpointStats[] }>('/api/v1/analytics/performance/slowest?limit=10'),
      ]);
      setSystemStats(stats);
      setTopEndpoints(top.endpoints);
      setSlowestEndpoints(slow.endpoints);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="mt-2 text-gray-600">
          System performance and usage metrics
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Events"
          value={systemStats?.total_events.toLocaleString() || '0'}
          icon={<Activity className="h-6 w-6" />}
          color="text-blue-600"
          bgColor="bg-blue-50"
        />
        <StatCard
          title="Unique Users"
          value={systemStats?.unique_users.toString() || '0'}
          icon={<Users className="h-6 w-6" />}
          color="text-green-600"
          bgColor="bg-green-50"
        />
        <StatCard
          title="API Calls"
          value={systemStats?.api_calls.toLocaleString() || '0'}
          icon={<Zap className="h-6 w-6" />}
          color="text-purple-600"
          bgColor="bg-purple-50"
        />
        <StatCard
          title="Error Rate"
          value={`${systemStats?.error_rate.toFixed(2) || '0'}%`}
          icon={<TrendingUp className="h-6 w-6" />}
          color="text-orange-600"
          bgColor="bg-orange-50"
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Most Called Endpoints</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topEndpoints.map((endpoint, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono px-2 py-0.5 bg-gray-100 rounded">
                        {endpoint.method}
                      </span>
                      <span className="text-sm text-gray-900 truncate">
                        {endpoint.endpoint}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {endpoint.avg_response_time_ms.toFixed(0)}ms avg
                    </p>
                  </div>
                  <span className="text-sm font-medium text-gray-900 ml-4">
                    {endpoint.count.toLocaleString()}
                  </span>
                </div>
              ))}
              {topEndpoints.length === 0 && (
                <p className="text-center text-gray-500 py-4">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Slowest Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Slowest Endpoints</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {slowestEndpoints.map((endpoint, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono px-2 py-0.5 bg-gray-100 rounded">
                        {endpoint.method}
                      </span>
                      <span className="text-sm text-gray-900 truncate">
                        {endpoint.endpoint}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {endpoint.count} calls
                    </p>
                  </div>
                  <span className="text-sm font-medium text-orange-600 ml-4">
                    {endpoint.avg_response_time_ms.toFixed(0)}ms
                  </span>
                </div>
              ))}
              {slowestEndpoints.length === 0 && (
                <p className="text-center text-gray-500 py-4">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Event Breakdown */}
      {systemStats?.event_counts && (
        <Card>
          <CardHeader>
            <CardTitle>Event Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Object.entries(systemStats.event_counts)
                .sort(([, a], [, b]) => b - a)
                .map(([event, count]) => (
                  <div key={event} className="p-4 rounded-lg border border-gray-200">
                    <p className="text-2xl font-bold text-gray-900">
                      {count.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {event.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
  bgColor,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          </div>
          <div className={`${bgColor} ${color} p-3 rounded-lg`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
