/**
 * Admin dashboard overview.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, Button, Spinner } from '@/components/ui';
import { Users, Video, Sparkles, DollarSign, TrendingUp, Activity } from 'lucide-react';

interface SystemStats {
  event_counts: Record<string, number>;
  total_events: number;
  unique_users: number;
  api_calls: number;
  error_rate: number;
  avg_response_time_ms: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await apiClient.get<SystemStats>('/api/v1/analytics/system/stats');
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
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
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Platform overview and management
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Users"
          value={stats?.unique_users.toString() || '0'}
          icon={<Users className="h-6 w-6" />}
          color="text-blue-600"
          bgColor="bg-blue-50"
        />
        <StatCard
          title="API Calls"
          value={stats?.api_calls.toString() || '0'}
          icon={<Activity className="h-6 w-6" />}
          color="text-green-600"
          bgColor="bg-green-50"
        />
        <StatCard
          title="Total Events"
          value={stats?.total_events.toString() || '0'}
          icon={<Sparkles className="h-6 w-6" />}
          color="text-purple-600"
          bgColor="bg-purple-50"
        />
        <StatCard
          title="Error Rate"
          value={`${stats?.error_rate.toFixed(1) || '0'}%`}
          icon={<TrendingUp className="h-6 w-6" />}
          color="text-orange-600"
          bgColor="bg-orange-50"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>User Management</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/admin/users">
              <Button variant="outline" className="w-full justify-start">
                <Users className="mr-2 h-4 w-4" />
                Manage Users
              </Button>
            </Link>
            <Link href="/admin/analytics">
              <Button variant="outline" className="w-full justify-start">
                <Activity className="mr-2 h-4 w-4" />
                View Analytics
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3">
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">API Calls</dt>
                <dd className="text-sm font-medium">{stats?.api_calls || 0}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">Error Rate</dt>
                <dd className="text-sm font-medium">{stats?.error_rate.toFixed(2) || 0}%</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">Avg Response Time</dt>
                <dd className="text-sm font-medium">{stats?.avg_response_time_ms.toFixed(0) || 0}ms</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      {stats?.event_counts && (
        <Card>
          <CardHeader>
            <CardTitle>Event Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(stats.event_counts).slice(0, 10).map(([event, count]) => (
                <div key={event} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <span className="text-sm text-gray-700">{event.replace(/_/g, ' ')}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
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
