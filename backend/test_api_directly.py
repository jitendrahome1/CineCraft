"""
Test OpenRouter API directly with httpx to debug authentication.
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_direct():
    """Test OpenRouter API directly."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    print("Testing OpenRouter API directly...")
    print("=" * 60)
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}" if api_key else "NO KEY")
    print(f"API Key Length: {len(api_key)}" if api_key else "N/A")
    print()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cinecraft.app",
        "X-Title": "CineCraft"
    }

    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": "Say 'Hello, CineCraft!' in one sentence."}
        ],
        "max_tokens": 50
    }

    async with httpx.AsyncClient() as client:
        try:
            print("Making request to OpenRouter...")
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )

            print(f"Status Code: {response.status_code}")
            print()

            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"Response: {result}")
                if "choices" in result:
                    print(f"Message: {result['choices'][0]['message']['content']}")
            else:
                print("❌ Failed!")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct())
