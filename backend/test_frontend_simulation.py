"""
Test that simulates exactly what the frontend does.
"""
import httpx
import asyncio
import json

async def test_frontend_flow():
    """Simulate frontend behavior exactly."""
    print("=" * 60)
    print("Testing Frontend Simulation")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
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
        print(f"✅ Token received: {token[:20]}...")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 2: Create project (EXACT frontend format)
        print("\n2. Creating project with EXACT frontend format...")
        project_data = {
            "title": "Frontend Test Story",
            "description": "Testing exactly as frontend does"
        }

        print(f"Request payload: {json.dumps(project_data, indent=2)}")

        create_response = await client.post(
            "http://localhost:8000/api/v1/projects",
            json=project_data,
            headers=headers
        )

        print(f"Status: {create_response.status_code}")
        print(f"Response headers: {dict(create_response.headers)}")

        if create_response.status_code not in [200, 201]:
            print(f"❌ Project creation failed")
            print(f"Response: {create_response.text}")
            return

        project = create_response.json()
        project_id = project.get("id")
        print(f"✅ Project created: ID {project_id}")
        print(f"Project data: {json.dumps(project, indent=2)}")

        # Step 3: Generate story (EXACT frontend format)
        print("\n3. Generating story with EXACT frontend format...")
        story_request = {
            "project_id": project_id
        }

        print(f"Request payload: {json.dumps(story_request, indent=2)}")
        print(f"Request URL: http://localhost:8000/api/v1/ai/generate-story")
        print(f"Request headers: {headers}")

        story_response = await client.post(
            "http://localhost:8000/api/v1/ai/generate-story",
            json=story_request,
            headers=headers
        )

        print(f"\n📊 Response Details:")
        print(f"Status Code: {story_response.status_code}")
        print(f"Status Text: {story_response.reason_phrase}")
        print(f"Response Headers:")
        for key, value in story_response.headers.items():
            print(f"  {key}: {value}")

        print(f"\nResponse Body Length: {len(story_response.text)} chars")
        print(f"First 500 chars: {story_response.text[:500]}")

        if story_response.status_code == 200:
            try:
                story_result = story_response.json()
                print(f"\n✅ Story generation SUCCESS!")
                print(f"Response keys: {list(story_result.keys())}")
                print(f"Project ID: {story_result.get('project_id')}")
                print(f"Story length: {len(story_result.get('story', ''))} chars")
                print(f"Scenes: {len(story_result.get('scenes', []))}")
                print(f"Characters: {len(story_result.get('characters', []))}")
                print(f"Status: {story_result.get('status')}")

                # Check scene structure
                if story_result.get('scenes'):
                    print(f"\n📋 First scene structure:")
                    first_scene = story_result['scenes'][0]
                    print(f"  Keys: {list(first_scene.keys())}")
                    print(f"  Scene: {json.dumps(first_scene, indent=2)}")

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response")
                print(f"Error: {str(e)}")
        else:
            print(f"❌ Story generation failed")
            print(f"Error: {story_response.text}")

        # Step 4: Verify project status
        print("\n4. Checking project status...")
        project_response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}",
            headers=headers
        )

        if project_response.status_code == 200:
            project_details = project_response.json()
            print(f"Project status: {project_details.get('status')}")
            print(f"Has story: {bool(project_details.get('story'))}")
            print(f"Story length in project: {len(project_details.get('story', ''))} chars")
        else:
            print(f"❌ Failed to get project: {project_response.text}")

asyncio.run(test_frontend_flow())
