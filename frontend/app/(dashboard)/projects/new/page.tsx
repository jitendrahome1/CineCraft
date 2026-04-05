/**
 * New project creation page with AI story generation.
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { projectsApi, aiApi } from '@/lib/api';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent, Progress } from '@/components/ui';
import { ArrowLeft, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState<'english' | 'hindi'>('english');
  const [videoLength, setVideoLength] = useState<'short' | 'long'>('short');
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsGenerating(true);
    setProgress(0);

    try {
      // Step 1: Create project (20%)
      setCurrentStep('Creating project...');
      setProgress(20);
      const project = await projectsApi.create({ title, description, language, video_length: videoLength });

      // Step 2: Generate story with AI (60%)
      setCurrentStep('Generating story with AI...');
      setProgress(40);
      const storyResult = await aiApi.generateStory({
        project_id: project.id,
      });

      // Backend already saved story and updated status
      // No need to update project again
      setProgress(100);
      setCurrentStep('Complete!');

      // Redirect to project detail page
      setTimeout(() => {
        router.push(`/projects/${project.id}`);
      }, 500);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to create project');
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
        <p className="mt-2 text-gray-600">
          Start with a story title and let AI generate the rest
        </p>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
          <CardDescription>
            Tell us about your story and we'll generate scenes, images, and narration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 rounded-lg bg-red-50 text-red-700">
                {error}
              </div>
            )}

            <Input
              label="Story Title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="The Lost Key"
              required
              disabled={isGenerating}
              helperText="A clear, descriptive title for your story"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Story Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="A young detective discovers a mysterious key that unlocks secrets from the past..."
                rows={4}
                disabled={isGenerating}
                className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"
              />
              <p className="mt-1 text-sm text-gray-500">
                Optional: Provide more context to help AI generate a better story
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as 'english' | 'hindi')}
                  disabled={isGenerating}
                  className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="english">English</option>
                  <option value="hindi">Hindi</option>
                </select>
                <p className="mt-1 text-sm text-gray-500">Narration language</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Video Length
                </label>
                <select
                  value={videoLength}
                  onChange={(e) => setVideoLength(e.target.value as 'short' | 'long')}
                  disabled={isGenerating}
                  className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="short">Short (5-8 scenes)</option>
                  <option value="long">Long (10-20 scenes)</option>
                </select>
                <p className="mt-1 text-sm text-gray-500">Controls scene count and detail</p>
              </div>
            </div>

            {isGenerating && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{currentStep}</span>
                  <span className="text-gray-900 font-medium">{progress}%</span>
                </div>
                <Progress value={progress} showLabel={false} />
              </div>
            )}

            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={isGenerating || !title}
                isLoading={isGenerating}
                className="flex-1"
              >
                {isGenerating ? (
                  'Generating...'
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate with AI
                  </>
                )}
              </Button>
              <Link href="/projects" className="flex-1">
                <Button
                  type="button"
                  variant="outline"
                  disabled={isGenerating}
                  className="w-full"
                >
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="mt-6 bg-indigo-50 border-indigo-200">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Sparkles className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-indigo-900 mb-1">
                Documentary-Style Generation
              </h3>
              <ul className="text-sm text-indigo-700 space-y-1">
                <li>• AI generates a cinematic documentary narration (BBC/National Geographic style)</li>
                <li>• Characters are extracted with detailed appearances for visual consistency</li>
                <li>• Story is broken into scenes with camera angles, motion prompts, and emotions</li>
                <li>• Each scene includes ultra-detailed visual and video generation prompts</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
