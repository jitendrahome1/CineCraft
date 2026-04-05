"""
Test OpenRouter with the new API key.
"""
import asyncio
from openai import AsyncOpenAI

async def test_new_key():
    """Test with new OpenRouter API key."""
    api_key = "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"

    print("Testing OpenRouter with new API key...")
    print("=" * 60)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    try:
        # Test with free model
        print("1. Testing with free model: liquid/lfm-2.5-1.2b-instruct:free")
        response = await client.chat.completions.create(
            model="liquid/lfm-2.5-1.2b-instruct:free",
            messages=[
                {"role": "user", "content": "Say 'Hello from CineCraft!' in one sentence."}
            ]
        )

        print("✅ Free model works!")
        print(f"   Response: {response.choices[0].message.content}")
        print()

        # Test with Claude (requires credits)
        print("2. Testing with Claude: anthropic/claude-3.5-sonnet")
        response2 = await client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {"role": "user", "content": "Say 'Hello from CineCraft!' in one sentence."}
            ],
            max_tokens=100
        )

        print("✅ Claude model works!")
        print(f"   Response: {response2.choices[0].message.content}")
        print()

        print("=" * 60)
        print("🎉 All tests passed! OpenRouter is configured correctly.")
        print("=" * 60)

    except Exception as e:
        error_str = str(e)
        print(f"❌ Error: {error_str}")

        if "402" in error_str or "credits" in error_str.lower():
            print("\n💡 The free model works but Claude requires credits.")
            print("   Add credits at: https://openrouter.ai/credits")
            print("   Or use free models like: liquid/lfm-2.5-1.2b-instruct:free")
        elif "401" in error_str:
            print("\n❌ Still getting authentication error.")
            print("   Please verify the API key at: https://openrouter.ai/keys")

if __name__ == "__main__":
    asyncio.run(test_new_key())
