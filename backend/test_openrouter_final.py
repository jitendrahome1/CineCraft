"""
Final comprehensive test for OpenRouter.
"""
import asyncio
from app.providers.ai.factory import get_ai_provider_from_config
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

async def test_openrouter_comprehensive():
    """Comprehensive OpenRouter test."""
    print("=" * 60)
    print("OpenRouter Comprehensive Test")
    print("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"\nAPI Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"Length: {len(api_key)}")

    # Test 1: Direct API call with free model
    print("\n" + "=" * 60)
    print("Test 1: Free Model (liquid/lfm-2.5-1.2b-instruct:free)")
    print("=" * 60)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    try:
        response = await client.chat.completions.create(
            model="liquid/lfm-2.5-1.2b-instruct:free",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=50
        )
        print("✅ Free model works!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Free model failed: {str(e)}")
        if "401" in str(e):
            print("\n⚠️  Authentication failed. Possible issues:")
            print("  1. API key is invalid or expired")
            print("  2. OpenRouter account not verified")
            print("  3. Account doesn't exist")
            print("\nPlease:")
            print("  - Log in to https://openrouter.ai/")
            print("  - Verify your email")
            print("  - Go to https://openrouter.ai/keys")
            print("  - Delete and regenerate a new API key")
            return

    # Test 2: Try Claude model (requires credits)
    print("\n" + "=" * 60)
    print("Test 2: Claude Model (requires credits)")
    print("=" * 60)

    try:
        response = await client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=50
        )
        print("✅ Claude model works!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "insufficient" in error_msg.lower():
            print("⚠️  Claude requires credits")
            print("Add credits at: https://openrouter.ai/credits")
        else:
            print(f"❌ Claude failed: {error_msg}")

    # Test 3: Use provider from config
    print("\n" + "=" * 60)
    print("Test 3: Story Generation via Provider")
    print("=" * 60)

    try:
        provider = get_ai_provider_from_config()
        print(f"Provider: {provider.__class__.__name__}")
        print(f"Story Model: {provider.story_model}")

        # Try generating a short story
        print("\nGenerating story...")
        story = await provider.generate_story(
            title="The Magic Key",
            context="A very short story, just 2-3 sentences"
        )

        print("✅ Story generation works!")
        print(f"\nGenerated Story ({len(story)} chars):")
        print("-" * 60)
        print(story)
        print("-" * 60)

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Story generation failed: {error_msg}")
        if "402" in error_msg:
            print("\n💡 Solution: Add credits or use a free model")
            print("   Update .env with free model:")
            print("   OPENROUTER_STORY_MODEL=liquid/lfm-2.5-1.2b-instruct:free")

if __name__ == "__main__":
    asyncio.run(test_openrouter_comprehensive())
