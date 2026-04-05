/**
 * Dashboard home page.
 */
'use client';

import { useAuth } from '@/lib/contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button } from '@/components/ui';
import Link from 'next/link';
import { FolderOpen, Video, Sparkles, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="mt-2 text-gray-600">
          Create stunning videos from your stories with AI
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Projects"
          value="0"
          icon={<FolderOpen className="h-6 w-6" />}
          color="text-blue-600"
          bgColor="bg-blue-50"
        />
        <StatCard
          title="Rendered Videos"
          value="0"
          icon={<Video className="h-6 w-6" />}
          color="text-green-600"
          bgColor="bg-green-50"
        />
        <StatCard
          title="AI Generations"
          value="0"
          icon={<Sparkles className="h-6 w-6" />}
          color="text-purple-600"
          bgColor="bg-purple-50"
        />
        <StatCard
          title="Total Views"
          value="0"
          icon={<TrendingUp className="h-6 w-6" />}
          color="text-orange-600"
          bgColor="bg-orange-50"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Create Your First Project</CardTitle>
            <CardDescription>
              Start by creating a new project and let AI transform your story into a video
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/projects/new">
              <Button className="w-full">
                <Sparkles className="mr-2 h-4 w-4" />
                New Project
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest projects and renders
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              <FolderOpen className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No activity yet</p>
              <p className="text-sm mt-1">Start creating to see your activity here</p>
            </div>
          </CardContent>
        </Card>
      </div>
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
