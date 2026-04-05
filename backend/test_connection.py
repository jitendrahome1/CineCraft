"""
Test OpenRouter connection with real API key.
"""
import asyncio
from app.providers.ai.factory import get_ai_provider_from_config

async def test_connection():
    """Test connection to OpenRouter API."""
    print("Testing OpenRouter connection...")
    print("=" * 60)

    try:
        # Get provider from config (should use OpenRouter now)
        provider = get_ai_provider_from_config()

        print(f"Provider: {provider.__class__.__name__}")
        print(f"Story Model: {provider.story_model}")
        print(f"Scene Model: {provider.scene_model}")
        print(f"Character Model: {provider.character_model}")
        print()

        # Test connection
        print("Testing API connection...")
        result = await provider.test_connection()

        if result:
            print("✅ Connection successful!")
            print()

            # Try a simple story generation
            print("Testing story generation with a simple prompt...")
            story = await provider.generate_story(
                title="The Magic Key",
                context="A short story for children"
            )

            print("✅ Story generated successfully!")
            print(f"Length: {len(story)} characters")
            print()
            print("Story preview (first 500 chars):")
            print("-" * 60)
            print(story[:500] + "..." if len(story) > 500 else story)
            print("-" * 60)

        else:
            print("❌ Connection failed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
