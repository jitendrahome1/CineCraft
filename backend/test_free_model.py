"""
Test OpenRouter with a free model like in the curl command.
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_free_model():
    """Test with free model."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    print("Testing OpenRouter with free model...")
    print("=" * 60)

    # Use only the headers from the curl command
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Test with free model
    data = {
        "model": "liquid/lfm-2.5-1.2b-instruct:free",
        "messages": [
            {"role": "user", "content": "What is the meaning of life?"}
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            print("Making request with free model...")
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
                print("✅ Success with free model!")
                if "choices" in result:
                    print(f"Response: {result['choices'][0]['message']['content']}")
                print()

                # Now test with Claude model
                print("Testing with Claude model (requires credits)...")
                data["model"] = "anthropic/claude-3.5-sonnet"
                data["messages"] = [{"role": "user", "content": "Say hello in one sentence."}]

                response2 = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )

                print(f"Status Code: {response2.status_code}")

                if response2.status_code == 200:
                    result2 = response2.json()
                    print("✅ Success with Claude model!")
                    if "choices" in result2:
                        print(f"Response: {result2['choices'][0]['message']['content']}")
                else:
                    print(f"❌ Claude model failed: {response2.text}")
                    print("\nThis likely means you need to add credits to your OpenRouter account.")
                    print("Visit: https://openrouter.ai/credits")

            else:
                print("❌ Failed!")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_free_model())
