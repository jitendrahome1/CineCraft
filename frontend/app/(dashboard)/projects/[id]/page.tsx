/**
 * Project detail page with scenes.
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { projectsApi, renderingApi, apiClient, type Project, type Scene } from '@/lib/api';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, Badge, Spinner } from '@/components/ui';
import { ArrowLeft, Play, Edit, Trash2, Image as ImageIcon, Mic, Music } from 'lucide-react';
import { format } from 'date-fns';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = parseInt(params.id as string);

  const [project, setProject] = useState<Project | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRendering, setIsRendering] = useState(false);
  const [isGeneratingMedia, setIsGeneratingMedia] = useState(false);
  const [isGeneratingVoice, setIsGeneratingVoice] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      setIsLoading(true);
      const [projectData, scenesData] = await Promise.all([
        projectsApi.get(projectId),
        projectsApi.getScenes(projectId),
      ]);
      setProject(projectData);
      setScenes(Array.isArray(scenesData) ? scenesData : []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateMedia = async () => {
    try {
      setIsGeneratingMedia(true);
      setError('');
      const result = await apiClient.post(`/api/v1/media/projects/${projectId}/generate-placeholder-media`);
      // Refresh project to show new images
      await fetchProject();
      setIsGeneratingMedia(false);
      // Show warning if some images failed
      if (result?.failed_count > 0) {
        setError(`${result.failed_count} image(s) failed to generate. ${result.generated_count} succeeded.`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to generate media');
      setIsGeneratingMedia(false);
    }
  };

  const handleGenerateVoice = async () => {
    try {
      setIsGeneratingVoice(true);
      setError('');
      await apiClient.post(`/api/v1/media/projects/${projectId}/generate-voice`);
      await fetchProject();
      setIsGeneratingVoice(false);
    } catch (err: any) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to generate voice');
      setIsGeneratingVoice(false);
    }
  };

  const handleStartRender = async () => {
    try {
      setIsRendering(true);
      const result = await renderingApi.startRender({
        project_id: projectId,
      });
      router.push(`/renders/${(result as any).job_id}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to start render');
      setIsRendering(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this project?')) {
      return;
    }

    try {
      await projectsApi.delete(projectId);
      router.push('/projects');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete project');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Project not found</h2>
        <Link href="/projects">
          <Button variant="outline">Back to Projects</Button>
        </Link>
      </div>
    );
  }

  const statusColors: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'default',
    generating: 'warning',
    ready: 'success',
    rendering: 'info',
    completed: 'success',
    failed: 'danger',
  };

  const canRender = project.status === 'ready' && scenes.length > 0;

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{project.title}</h1>
              <Badge variant={statusColors[project.status] || 'default'}>
                {project.status}
              </Badge>
            </div>
            {project.description && (
              <p className="text-gray-600 mb-2">{project.description}</p>
            )}
            <p className="text-sm text-gray-500">
              Created {format(new Date(project.created_at), 'MMMM d, yyyy')}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            {(project.status === 'ready' || project.status === 'completed') && !project.video_url && (
              <>
                <Button
                  variant="outline"
                  onClick={handleGenerateMedia}
                  disabled={isGeneratingMedia}
                  isLoading={isGeneratingMedia}
                >
                  <ImageIcon className="mr-2 h-4 w-4" />
                  {Array.isArray(scenes) && scenes.some(s => s.image_url) ? 'Regenerate Images' : 'Generate Images'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleGenerateVoice}
                  disabled={isGeneratingVoice}
                  isLoading={isGeneratingVoice}
                >
                  <Mic className="mr-2 h-4 w-4" />
                  {Array.isArray(scenes) && scenes.some(s => s.voice_url) ? 'Regenerate Voice' : 'Generate Voice'}
                </Button>
                <Button
                  onClick={handleStartRender}
                  disabled={!canRender || isRendering}
                  isLoading={isRendering}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Render Video
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700">
          {error}
        </div>
      )}

      {/* Video Player */}
      {project.video_url && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Final Video</CardTitle>
            <CardDescription>
              Your rendered video is ready to watch
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="aspect-video rounded-lg overflow-hidden bg-black">
              <video
                controls
                className="w-full h-full"
                src={project.video_url}
                poster={project.thumbnail_url || undefined}
              >
                Your browser does not support the video element.
              </video>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {project.video_duration && (
                  <span>Duration: {project.video_duration}s</span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  as="a"
                  href={project.video_url}
                  download={`${project.title}.mp4`}
                >
                  Download Video
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Story */}
      {project.story && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Story</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{project.story}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scenes */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Scenes ({scenes.length})
        </h2>
      </div>

      {scenes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600">No scenes generated yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {scenes.map((scene) => (
            <SceneCard key={scene.id} scene={scene} />
          ))}
        </div>
      )}
    </div>
  );
}

function SceneCard({ scene }: { scene: Scene }) {
  // Helper to get full URL for images (prepend API base URL if relative)
  const getImageUrl = (url?: string) => {
    if (!url) return undefined;
    if (url.startsWith('http')) return url;
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${apiBaseUrl}${url}`;
  };

  const imageUrl = getImageUrl(scene.image_url);
  const sceneNumber = scene.sequence_number;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="default">Scene {sceneNumber}</Badge>
              {scene.title && (
                <CardTitle className="text-lg">{scene.title}</CardTitle>
              )}
            </div>
            {scene.narration && (
              <CardDescription>{scene.narration}</CardDescription>
            )}
          </div>
          <div className="flex gap-2">
            {scene.image_url && (
              <Badge variant="success">
                <ImageIcon className="h-3 w-3 mr-1" />
                Image
              </Badge>
            )}
            {scene.voice_url && (
              <Badge variant="success">
                <Mic className="h-3 w-3 mr-1" />
                Voice
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Image Preview */}
          {imageUrl && (
            <div className="aspect-video rounded-lg overflow-hidden bg-gray-100">
              <img
                src={imageUrl}
                alt={`Scene ${sceneNumber}`}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Visual Description */}
          {scene.visual_description && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Visual Description
              </h4>
              <p className="text-sm text-gray-600">{scene.visual_description}</p>
            </div>
          )}
        </div>

        {/* Audio Player */}
        {scene.voice_url && (
          <div className="mt-4">
            <audio
              controls
              className="w-full"
              src={scene.voice_url}
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
