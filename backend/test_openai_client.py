"""
Test using OpenAI client library directly.
"""
import asyncio
from openai import AsyncOpenAI

async def test_with_openai_client():
    """Test OpenRouter using AsyncOpenAI client."""
    api_key = "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"

    print("Testing OpenRouter with AsyncOpenAI client...")
    print("=" * 60)

    # Create client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    try:
        # Test with free model first
        print("Testing with free model: liquid/lfm-2.5-1.2b-instruct:free")
        response = await client.chat.completions.create(
            model="liquid/lfm-2.5-1.2b-instruct:free",
            messages=[
                {"role": "user", "content": "Say hello in one sentence"}
            ]
        )

        print("✅ Success!")
        print(f"Response: {response.choices[0].message.content}")
        print()

        # Test with Claude
        print("Testing with Claude model: anthropic/claude-3.5-sonnet")
        response2 = await client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {"role": "user", "content": "Say hello in one sentence"}
            ],
            max_tokens=50
        )

        print("✅ Success with Claude!")
        print(f"Response: {response2.choices[0].message.content}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        # Check if it's authentication error
        if "401" in str(e) or "User not found" in str(e):
            print("\n" + "=" * 60)
            print("Authentication Error Troubleshooting:")
            print("=" * 60)
            print("1. Verify your API key at: https://openrouter.ai/keys")
            print("2. Make sure your OpenRouter account is active")
            print("3. Check if you have credits (for paid models)")
            print("4. Try regenerating your API key")
            print("\nCurrent API key format:")
            print(f"  Length: {len(api_key)}")
            print(f"  Starts with: {api_key[:15]}...")
            print(f"  Ends with: ...{api_key[-15:]}")

if __name__ == "__main__":
    asyncio.run(test_with_openai_client())
