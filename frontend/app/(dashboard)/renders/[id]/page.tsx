/**
 * Render job detail page with real-time progress.
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { renderingApi, type RenderJob } from '@/lib/api';
import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Spinner, Progress } from '@/components/ui';
import { ArrowLeft, Download, Play, CheckCircle2, XCircle, Clock, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

export default function RenderDetailPage() {
  const params = useParams();
  const jobId = parseInt(params.id as string);

  const [job, setJob] = useState<RenderJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket({
    jobId,
    enabled: true,
    onProgress: (data) => {
      setJob((prev) => prev ? {
        ...prev,
        progress: data.progress,
        stage: data.stage,
        status: data.status as any,
      } : null);
    },
    onComplete: (data) => {
      setJob((prev) => prev ? {
        ...prev,
        status: 'completed',
        progress: 100,
        output_url: data.output_url,
        completed_at: new Date().toISOString(),
      } : null);
    },
    onError: (data) => {
      setJob((prev) => prev ? {
        ...prev,
        status: 'failed',
        error_message: data.message,
      } : null);
    },
  });

  useEffect(() => {
    fetchJob();
  }, [jobId]);

  const fetchJob = async () => {
    try {
      setIsLoading(true);
      const jobData = await renderingApi.getJobStatus(jobId);
      setJob(jobData);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load render job');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this render?')) {
      return;
    }

    try {
      await renderingApi.cancelJob(jobId);
      fetchJob();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to cancel render');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Job not found</h2>
        <Link href="/renders">
          <Button variant="outline">Back to Renders</Button>
        </Link>
      </div>
    );
  }

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
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link href="/renders">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Renders
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                Render Job #{job.id}
              </h1>
              <Badge variant={statusColors[job.status] || 'default'}>
                <Icon className="h-4 w-4 mr-1" />
                {job.status}
              </Badge>
            </div>
            <p className="text-sm text-gray-500">
              Created {format(new Date(job.created_at), 'MMMM d, yyyy h:mm a')}
            </p>
          </div>
          {isConnected && job.status === 'processing' && (
            <Badge variant="success">
              <div className="h-2 w-2 rounded-full bg-green-600 mr-2 animate-pulse" />
              Live
            </Badge>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700">
          {error}
        </div>
      )}

      {/* Progress Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Render Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {job.status === 'queued' && (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">Render queued and waiting to start...</p>
            </div>
          )}

          {job.status === 'processing' && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {job.stage || job.current_stage || 'Processing...'}
                </span>
                <span className="text-sm font-bold text-gray-900">{job.progress}%</span>
              </div>
              <Progress value={job.progress} variant="info" />

              <div className="mt-6 grid grid-cols-3 gap-4 text-center">
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-600 mb-1">Started</p>
                  <p className="text-sm font-medium">
                    {job.started_at ? format(new Date(job.started_at), 'h:mm a') : '-'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-600 mb-1">Stage</p>
                  <p className="text-sm font-medium">{job.stage || job.current_stage || 'Processing'}</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-600 mb-1">Progress</p>
                  <p className="text-sm font-medium">{job.progress}%</p>
                </div>
              </div>

              <div className="mt-4">
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleCancel}
                >
                  Cancel Render
                </Button>
              </div>
            </div>
          )}

          {job.status === 'completed' && (
            <div className="text-center py-8">
              <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Render Complete!
              </h3>
              <p className="text-gray-600 mb-6">
                Your video is ready to download
              </p>
              {job.completed_at && (
                <p className="text-sm text-gray-500 mb-6">
                  Completed {format(new Date(job.completed_at), 'MMMM d, yyyy h:mm a')}
                </p>
              )}
              {job.output_url && (
                <div className="space-y-4">
                  <Button
                    size="lg"
                    onClick={() => window.open(job.output_url, '_blank')}
                  >
                    <Download className="mr-2 h-5 w-5" />
                    Download Video
                  </Button>

                  {/* Video Player */}
                  <div className="mt-6 rounded-lg overflow-hidden bg-black">
                    <video
                      controls
                      className="w-full"
                      src={job.output_url}
                    >
                      Your browser does not support the video element.
                    </video>
                  </div>
                </div>
              )}
            </div>
          )}

          {job.status === 'failed' && (
            <div className="text-center py-8">
              <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Render Failed
              </h3>
              {job.error_message && (
                <div className="mt-4 p-4 rounded-lg bg-red-50 text-red-700 text-left max-w-lg mx-auto">
                  <p className="font-medium mb-1">Error Details:</p>
                  <p className="text-sm">{job.error_message}</p>
                </div>
              )}
              <div className="mt-6">
                <Button
                  variant="outline"
                  onClick={fetchJob}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Retry
                </Button>
              </div>
            </div>
          )}

          {job.status === 'cancelled' && (
            <div className="text-center py-8">
              <XCircle className="h-16 w-16 text-yellow-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Render Cancelled
              </h3>
              <p className="text-gray-600">
                This render job was cancelled
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job Details */}
      <Card>
        <CardHeader>
          <CardTitle>Job Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Job ID</dt>
              <dd className="text-sm text-gray-900 mt-1">#{job.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Project ID</dt>
              <dd className="text-sm text-gray-900 mt-1">#{job.project_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="text-sm text-gray-900 mt-1">{job.status}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Progress</dt>
              <dd className="text-sm text-gray-900 mt-1">{job.progress}%</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="text-sm text-gray-900 mt-1">
                {format(new Date(job.created_at), 'MMM d, yyyy h:mm a')}
              </dd>
            </div>
            {job.completed_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Completed</dt>
                <dd className="text-sm text-gray-900 mt-1">
                  {format(new Date(job.completed_at), 'MMM d, yyyy h:mm a')}
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
