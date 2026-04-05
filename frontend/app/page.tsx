/**
 * Home/Landing page.
 */
import Link from 'next/link';
import { Button } from '@/components/ui';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <span className="text-white font-bold text-xl">C</span>
              </div>
              <span className="text-xl font-bold text-gray-900">CineCraft</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link href="/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Transform Stories into{' '}
              <span className="text-indigo-600">Cinematic Videos</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
              Create stunning AI-powered videos from your stories. Generate scenes, images,
              voice narration, and background music—all with the power of artificial intelligence.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/register">
                <Button size="lg">
                  Start Creating Free
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg">
                  View Demo
                </Button>
              </Link>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mt-24 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <Feature
              title="AI Story Generation"
              description="Turn your ideas into compelling narratives with AI-powered story generation."
              icon="📝"
            />
            <Feature
              title="Scene Breakdown"
              description="Automatically split your story into visual scenes with descriptions."
              icon="🎬"
            />
            <Feature
              title="Image Generation"
              description="Create stunning visuals for each scene using AI image generation."
              icon="🎨"
            />
            <Feature
              title="Voice Narration"
              description="Generate professional voice narration for your entire story."
              icon="🎙️"
            />
            <Feature
              title="Background Music"
              description="Add mood-appropriate music automatically generated for your video."
              icon="🎵"
            />
            <Feature
              title="Professional Editing"
              description="Ken Burns effects, transitions, and audio mixing—all automated."
              icon="✨"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function Feature({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
