"""
Test project creation API.
"""
import httpx
import asyncio

async def test_create_project():
    """Test project creation."""
    print("Testing Project Creation API...")
    print("=" * 60)

    # First login to get token
    login_data = {
        "email": "admin@cinecraft.com",
        "password": "admin123"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Login
        print("\n1. Logging in...")
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return

        token = login_response.json().get("access_token")
        print(f"✅ Login successful")
        print(f"Token: {token[:20]}...")

        # Create project
        print("\n2. Creating project...")
        headers = {
            "Authorization": f"Bearer {token}"
        }

        project_data = {
            "title": "lion and monky story",
            "description": "A young detective discovers a mysterious key that unlocks secrets from the past...",
            "genre": "Mystery, Adventure",
            "tone": "Suspenseful"
        }

        create_response = await client.post(
            "http://localhost:8000/api/v1/projects/",
            json=project_data,
            headers=headers
        )

        print(f"Status: {create_response.status_code}")
        print(f"Response: {create_response.text[:500]}")

        if create_response.status_code == 200 or create_response.status_code == 201:
            project = create_response.json()
            print(f"\n✅ Project created successfully!")
            print(f"Project ID: {project.get('id')}")
            print(f"Title: {project.get('title')}")
            print(f"Status: {project.get('status')}")
        else:
            print(f"\n❌ Failed to create project")
            print(f"Full response: {create_response.text}")

asyncio.run(test_create_project())
