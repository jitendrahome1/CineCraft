/**
 * User analytics and usage dashboard.
 */
'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui';
import { Video, Image, Music, Mic, TrendingUp, Calendar } from 'lucide-react';

interface UserStats {
  total_projects: number;
  total_renders: number;
  total_scenes: number;
  storage_used_mb: number;
  renders_this_month: number;
  last_activity: string;
}

interface RecentProject {
  id: number;
  title: string;
  status: string;
  created_at: string;
  scene_count: number;
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      // Fetch user projects to calculate stats
      const projects = await apiClient.get<{ projects: RecentProject[]; total: number }>(
        '/api/v1/projects?limit=10'
      );

      // Calculate stats from projects
      const totalProjects = projects.total || 0;
      const projectsList = projects.projects || [];
      const totalScenes = projectsList.reduce((sum, p) => sum + (p.scene_count || 0), 0);

      const mockStats: UserStats = {
        total_projects: totalProjects,
        total_renders: 0, // Would come from render jobs API
        total_scenes: totalScenes,
        storage_used_mb: 0, // Would come from storage API
        renders_this_month: 0,
        last_activity: projectsList[0]?.created_at || new Date().toISOString(),
      };

      setStats(mockStats);
      setRecentProjects(projectsList);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setRecentProjects([]); // Set empty array on error
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-2 text-gray-600">
          Track your usage and project statistics
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Projects"
          value={stats?.total_projects.toString() || '0'}
          icon={<Video className="h-6 w-6" />}
          color="text-blue-600"
          bgColor="bg-blue-50"
        />
        <StatCard
          title="Total Scenes"
          value={stats?.total_scenes.toString() || '0'}
          icon={<Image className="h-6 w-6" />}
          color="text-green-600"
          bgColor="bg-green-50"
        />
        <StatCard
          title="Renders Completed"
          value={stats?.total_renders.toString() || '0'}
          icon={<TrendingUp className="h-6 w-6" />}
          color="text-purple-600"
          bgColor="bg-purple-50"
        />
        <StatCard
          title="Storage Used"
          value={`${stats?.storage_used_mb || 0} MB`}
          icon={<Music className="h-6 w-6" />}
          color="text-orange-600"
          bgColor="bg-orange-50"
        />
      </div>

      {/* Usage This Month */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            This Month's Activity
          </CardTitle>
          <CardDescription>
            Your usage statistics for the current month
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-indigo-50">
                  <Video className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.renders_this_month || 0}
                  </p>
                  <p className="text-sm text-gray-600">Videos Rendered</p>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-green-50">
                  <Image className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">0</p>
                  <p className="text-sm text-gray-600">Images Generated</p>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-purple-50">
                  <Mic className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">0</p>
                  <p className="text-sm text-gray-600">Voice Narrations</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Projects */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
          <CardDescription>
            Your recently created projects
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentProjects.map((project) => (
              <div
                key={project.id}
                className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-indigo-200 hover:bg-indigo-50/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {project.title}
                  </h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-500">
                      {project.scene_count || 0} scenes
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500">
                      {new Date(project.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      project.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : project.status === 'processing'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {project.status}
                  </span>
                </div>
              </div>
            ))}
            {recentProjects.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Video className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                <p>No projects yet</p>
                <p className="text-sm mt-1">Create your first project to get started!</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
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
