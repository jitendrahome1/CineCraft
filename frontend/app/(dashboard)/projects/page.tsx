/**
 * Projects list page.
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { projectsApi, type Project } from '@/lib/api';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, Badge, Spinner } from '@/components/ui';
import { Plus, FolderOpen, Calendar, Sparkles } from 'lucide-react';
import { format } from 'date-fns';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setIsLoading(true);
      const response = await projectsApi.list(0, 50);
      setProjects(response.items || []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load projects');
      setProjects([]); // Set empty array on error
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
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="mt-2 text-gray-600">
            Manage your story-to-video projects
          </p>
        </div>
        <Link href="/projects/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 text-red-700">
          {error}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && projects.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FolderOpen className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No projects yet
            </h3>
            <p className="text-gray-600 mb-6 text-center max-w-md">
              Create your first project to start transforming stories into videos with AI
            </p>
            <Link href="/projects/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Project
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Projects Grid */}
      {projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectCard({ project }: { project: Project }) {
  const statusColors: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'default',
    generating: 'warning',
    ready: 'success',
    rendering: 'info',
    completed: 'success',
    failed: 'danger',
  };

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardHeader>
          <div className="flex items-start justify-between mb-2">
            <CardTitle className="text-xl">{project.title}</CardTitle>
            <Badge variant={statusColors[project.status] || 'default'}>
              {project.status}
            </Badge>
          </div>
          {project.description && (
            <CardDescription className="line-clamp-2">
              {project.description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{format(new Date(project.created_at), 'MMM d, yyyy')}</span>
            </div>
            {project.scenes && project.scenes.length > 0 && (
              <div className="flex items-center gap-1">
                <Sparkles className="h-4 w-4" />
                <span>{project.scenes.length} scenes</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
