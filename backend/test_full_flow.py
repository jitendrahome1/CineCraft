"""
Test the complete project creation flow.
"""
import httpx
import asyncio
import json

async def test_complete_flow():
    """Test complete project creation and story generation."""
    print("=" * 60)
    print("Testing Complete Project Creation Flow")
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
        print(f"✅ Logged in successfully")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create project
        print("\n2. Creating project...")
        project_data = {
            "title": "Test Lion and Monkey",
            "description": "A young detective discovers a mysterious key"
        }

        create_response = await client.post(
            "http://localhost:8000/api/v1/projects",
            json=project_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            print(f"❌ Project creation failed: {create_response.text}")
            return

        project = create_response.json()
        project_id = project.get("id")
        print(f"✅ Project created: ID {project_id}")

        # Step 3: Generate story with AI
        print("\n3. Generating story with AI (this will take ~60 seconds)...")
        story_response = await client.post(
            "http://localhost:8000/api/v1/ai/generate-story",
            json={"project_id": project_id},
            headers=headers
        )

        print(f"Status: {story_response.status_code}")
        print(f"Response length: {len(story_response.text)} chars")

        if story_response.status_code == 200:
            try:
                story_result = story_response.json()
                print(f"\n✅ Story generation SUCCESS!")
                print(f"Project ID: {story_result.get('project_id')}")
                print(f"Story length: {len(story_result.get('story', ''))} chars")
                print(f"Scenes: {len(story_result.get('scenes', []))}")
                print(f"Characters: {len(story_result.get('characters', []))}")
                print(f"Message: {story_result.get('message')}")

                # Check response structure
                print(f"\nResponse keys: {list(story_result.keys())}")

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response")
                print(f"Raw response: {story_response.text[:500]}")
        else:
            print(f"❌ Story generation failed")
            print(f"Error: {story_response.text}")

asyncio.run(test_complete_flow())
