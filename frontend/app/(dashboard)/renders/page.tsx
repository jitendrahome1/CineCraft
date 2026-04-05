/**
 * Render jobs list page.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient, type RenderJob } from '@/lib/api';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Spinner, Progress } from '@/components/ui';
import { Video, Play, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function RendersPage() {
  const [jobs, setJobs] = useState<RenderJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJobs();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.get<{ items: RenderJob[] }>('/api/v1/jobs?skip=0&limit=50');
      setJobs(response.items || []);
      setIsLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load render jobs');
      setJobs([]); // Set empty array on error
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
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Render Jobs</h1>
        <p className="mt-2 text-gray-600">
          Track your video rendering progress
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700">
          {error}
        </div>
      )}

      {/* Empty State */}
      {jobs.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Video className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No render jobs yet
            </h3>
            <p className="text-gray-600 mb-6 text-center max-w-md">
              Create a project and start rendering to see your jobs here
            </p>
            <Link href="/projects/new">
              <Button>
                Create Project
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Jobs List */}
      {jobs.length > 0 && (
        <div className="space-y-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}

function JobCard({ job }: { job: RenderJob }) {
  const statusIcons = {
    queued: Clock,
    processing: Play,
    completed: CheckCircle2,
    failed: XCircle,
    cancelled: XCircle,
  };

  const statusColors: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
    queued: 'default',
    processing: 'info',
    completed: 'success',
    failed: 'danger',
    cancelled: 'warning',
  };

  const Icon = statusIcons[job.status] || Clock;

  return (
    <Link href={`/renders/${job.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <CardTitle className="text-lg">Render Job #{job.id}</CardTitle>
                <Badge variant={statusColors[job.status] || 'default'}>
                  <Icon className="h-3 w-3 mr-1" />
                  {job.status}
                </Badge>
              </div>
              {job.stage && (
                <p className="text-sm text-gray-600 mb-2">{job.stage}</p>
              )}
              <p className="text-sm text-gray-500">
                Started {format(new Date(job.created_at), 'MMM d, yyyy h:mm a')}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {job.status === 'processing' && (
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-600">{job.stage || 'Processing...'}</span>
                <span className="text-gray-900 font-medium">{job.progress}%</span>
              </div>
              <Progress value={job.progress} showLabel={false} />
            </div>
          )}

          {job.status === 'completed' && job.output_url && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Video ready</span>
              <Button
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  window.open(job.output_url, '_blank');
                }}
              >
                Download
              </Button>
            </div>
          )}

          {job.status === 'failed' && job.error_message && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
              {job.error_message}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
