"""
Test UI by creating a project with mock video URL.
"""
import httpx
import asyncio

async def test_ui():
    """Create a project with mock video for UI testing."""
    print("=" * 60)
    print("Testing UI with Mock Video")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        print("\n1. Logging in...")
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "admin@cinecraft.com", "password": "admin123"}
        )

        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get project 27
        print("\n2. Getting project 27...")
        project_response = await client.get(
            "http://localhost:8000/api/v1/projects/27",
            headers=headers
        )

        if project_response.status_code == 200:
            project = project_response.json()
            print(f"✅ Project: {project['title']}")
            print(f"   Status: {project['status']}")
            print(f"   Scenes: {project.get('scene_count', 0)}")
            print(f"   Video URL: {project.get('video_url', 'None')}")
            print(f"   Thumbnail: {project.get('thumbnail_url', 'None')}")

        # Set mock video URL for testing
        print("\n3. Setting mock video URL for UI testing...")
        update_response = await client.put(
            "http://localhost:8000/api/v1/projects/27",
            json={
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "thumbnail_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/BigBuckBunny.jpg",
                "video_duration": 596
            },
            headers=headers
        )

        if update_response.status_code == 200:
            print("✅ Mock video URL set!")
            print("\n🎬 Now visit the UI to test:")
            print("   URL: http://localhost:3000/projects/27")
            print("   - Should see video player at top")
            print("   - Should see play/pause controls")
            print("   - Should see download button")
            print("   - Should see all scenes with placeholder images below")
        else:
            print(f"❌ Failed to set video URL: {update_response.text}")

        # Get project again to verify
        print("\n4. Verifying video URL was set...")
        verify_response = await client.get(
            "http://localhost:8000/api/v1/projects/27",
            headers=headers
        )

        if verify_response.status_code == 200:
            project = verify_response.json()
            print(f"✅ Video URL: {project.get('video_url', 'None')}")
            print(f"✅ Duration: {project.get('video_duration', 'None')}s")

asyncio.run(test_ui())
