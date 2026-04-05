"""
Test Anthropic provider connection.
"""
import asyncio
from app.providers.ai.factory import get_ai_provider_from_config

async def test_anthropic():
    """Test Anthropic provider."""
    print("Testing Anthropic connection...")
    print("=" * 60)

    try:
        # Get provider from config (should use Anthropic now)
        provider = get_ai_provider_from_config()

        print(f"Provider: {provider.__class__.__name__}")
        print()

        # Test connection
        print("Testing API connection...")
        result = await provider.test_connection()

        if result:
            print("✅ Connection successful!")
            print()

            # Try a simple story generation
            print("Testing story generation...")
            story = await provider.generate_story(
                title="The Magic Key",
                context="A short children's story"
            )

            print("✅ Story generated successfully!")
            print(f"Length: {len(story)} characters")
            print()
            print("Story preview (first 500 chars):")
            print("-" * 60)
            print(story[:500] + "..." if len(story) > 500 else story)
            print("-" * 60)
            print()
            print("=" * 60)
            print("🎉 Anthropic provider is working correctly!")
            print("=" * 60)

        else:
            print("❌ Connection failed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

        error_str = str(e)
        if "401" in error_str or "authentication" in error_str.lower():
            print("\n⚠️  Authentication error detected.")
            print("Please verify your Anthropic API key:")
            print("  1. Go to https://console.anthropic.com/")
            print("  2. Get your API key from Settings > API Keys")
            print("  3. Update ANTHROPIC_API_KEY in .env file")
            print("\nNote: Anthropic keys should start with 'sk-ant-' and be much longer")

        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_anthropic())
