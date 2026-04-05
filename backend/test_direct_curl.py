"""
Test OpenRouter exactly like curl command.
"""
import httpx
import asyncio

async def test_direct():
    api_key = "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"

    print("Testing OpenRouter with direct httpx request...")
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"Length: {len(api_key)}")
    print()

    # Exact same as curl
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("Making request to OpenRouter...")
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")

            if response.status_code == 200:
                result = response.json()
                print("\n✅ SUCCESS!")
                print(f"Message: {result['choices'][0]['message']['content']}")
            else:
                print("\n❌ FAILED")
                print(f"Full response: {response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")

asyncio.run(test_direct())
