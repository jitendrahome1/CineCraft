"""
Test complete video generation workflow.
"""
import httpx
import asyncio
import json
import time

async def test_video_workflow():
    """Test from project creation to video rendering."""
    print("=" * 60)
    print("Testing Complete Video Workflow")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        # Step 1: Login
        print("\n1. Logging in...")
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "admin@cinecraft.com", "password": "admin123"}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return

        token = login_response.json().get("access_token")
        print(f"✅ Logged in successfully")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Get latest project with scenes
        print("\n2. Finding project with scenes...")
        projects_response = await client.get(
            "http://localhost:8000/api/v1/projects",
            headers=headers
        )

        if projects_response.status_code != 200:
            print(f"❌ Failed to get projects: {projects_response.text}")
            return

        projects = projects_response.json()
        if not projects:
            print("❌ No projects found. Create a project first.")
            return

        # Get the latest project
        project = projects[0]
        project_id = project["id"]
        print(f"✅ Using project {project_id}: '{project['title']}'")

        # Get scenes
        scenes_response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}/scenes",
            headers=headers
        )

        if scenes_response.status_code != 200:
            print(f"❌ Failed to get scenes: {scenes_response.text}")
            return

        scenes_data = scenes_response.json()
        scenes = scenes_data.get("scenes", [])

        if not scenes:
            print("❌ Project has no scenes. Generate story first.")
            return

        print(f"✅ Project has {len(scenes)} scenes")

        # Step 3: Generate placeholder media
        print("\n3. Generating placeholder images...")
        media_response = await client.post(
            f"http://localhost:8000/api/v1/media/projects/{project_id}/generate-placeholder-media",
            headers=headers
        )

        print(f"Status: {media_response.status_code}")

        if media_response.status_code == 200:
            media_result = media_response.json()
            print(f"✅ Media generation SUCCESS!")
            print(f"Generated: {media_result.get('generated_count')} images")
            print(f"Already existed: {media_result.get('existing_count')} images")
            print(f"Total scenes: {media_result.get('scenes_count')}")
        else:
            print(f"❌ Media generation failed")
            print(f"Error: {media_response.text}")
            return

        # Step 4: Start video rendering
        print("\n4. Starting video rendering...")
        render_response = await client.post(
            "http://localhost:8000/api/v1/rendering/render",
            json={
                "project_id": project_id,
                "preset": "high_quality"
            },
            headers=headers
        )

        print(f"Status: {render_response.status_code}")

        if render_response.status_code == 200:
            render_result = render_response.json()
            job_id = render_result.get("job_id")
            print(f"✅ Render job created: ID {job_id}")
            print(f"Status: {render_result.get('status')}")
            print(f"Message: {render_result.get('message')}")

            # Step 5: Check render status (poll for a bit)
            print("\n5. Monitoring render progress...")
            max_polls = 60  # 5 minutes max
            poll_count = 0

            while poll_count < max_polls:
                await asyncio.sleep(5)  # Wait 5 seconds
                poll_count += 1

                status_response = await client.get(
                    f"http://localhost:8000/api/v1/rendering/status/{job_id}",
                    headers=headers
                )

                if status_response.status_code == 200:
                    status_result = status_response.json()
                    job_status = status_result.get("status")
                    progress = status_result.get("progress", 0)

                    print(f"⏳ Poll {poll_count}: Status={job_status}, Progress={progress}%")

                    if job_status == "completed":
                        print(f"\n✅ Render COMPLETED!")
                        print(f"Video URL: {status_result.get('video_url')}")
                        print(f"Duration: {status_result.get('duration')}s")
                        break
                    elif job_status == "failed":
                        print(f"\n❌ Render FAILED")
                        print(f"Error: {status_result.get('error_message')}")
                        break
                else:
                    print(f"⚠️ Failed to get status: {status_response.status_code}")

            if poll_count >= max_polls:
                print(f"\n⏱️ Render still in progress after {max_polls * 5} seconds")
                print(f"Check status later at /api/v1/rendering/status/{job_id}")

        else:
            print(f"❌ Failed to start render")
            print(f"Error: {render_response.text}")
            return

        # Step 6: Get final project state
        print("\n6. Checking final project state...")
        final_project_response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}",
            headers=headers
        )

        if final_project_response.status_code == 200:
            final_project = final_project_response.json()
            print(f"Project status: {final_project.get('status')}")
            print(f"Has video: {bool(final_project.get('video_url'))}")
            if final_project.get('video_url'):
                print(f"Video URL: {final_project.get('video_url')}")
                print(f"\n🎉 SUCCESS! Video is ready to watch!")
        else:
            print(f"Failed to get project: {final_project_response.text}")

asyncio.run(test_video_workflow())
