"""
Quick test script to verify OpenRouter provider implementation.
This tests the provider structure and configuration without making real API calls.
"""
import asyncio
from app.providers.ai.openrouter import OpenRouterProvider
from app.providers.ai.factory import AIProviderFactory, get_ai_provider_from_config
from app.core.config import settings

def test_provider_registration():
    """Test that OpenRouter is registered in the factory."""
    print("Testing provider registration...")

    available_providers = AIProviderFactory.list_providers()
    print(f"  Available providers: {available_providers}")

    assert "openrouter" in available_providers, "OpenRouter not registered!"
    assert AIProviderFactory.is_provider_available("openrouter"), "OpenRouter not available!"

    print("  ✅ OpenRouter is registered in factory")

def test_provider_creation():
    """Test creating an OpenRouter provider instance."""
    print("\nTesting provider creation...")

    config = {
        "story_model": "anthropic/claude-3.5-sonnet",
        "scene_model": "openai/gpt-4-turbo",
        "character_model": "google/gemini-pro",
        "base_url": "https://openrouter.ai/api/v1",
        "max_tokens": 4096
    }

    provider = AIProviderFactory.create(
        provider_name="openrouter",
        api_key="test-key",
        config=config
    )

    assert isinstance(provider, OpenRouterProvider), "Provider is not OpenRouterProvider!"
    assert provider.story_model == "anthropic/claude-3.5-sonnet"
    assert provider.scene_model == "openai/gpt-4-turbo"
    assert provider.character_model == "google/gemini-pro"
    assert provider.max_tokens == 4096

    print(f"  ✅ Provider created successfully")
    print(f"     Story model: {provider.story_model}")
    print(f"     Scene model: {provider.scene_model}")
    print(f"     Character model: {provider.character_model}")

def test_configuration():
    """Test configuration loading from settings."""
    print("\nTesting configuration...")

    print(f"  Current AI_PROVIDER: {settings.AI_PROVIDER}")
    print(f"  OPENROUTER_STORY_MODEL: {settings.OPENROUTER_STORY_MODEL}")
    print(f"  OPENROUTER_SCENE_MODEL: {settings.OPENROUTER_SCENE_MODEL}")
    print(f"  OPENROUTER_CHARACTER_MODEL: {settings.OPENROUTER_CHARACTER_MODEL}")
    print(f"  OPENROUTER_BASE_URL: {settings.OPENROUTER_BASE_URL}")

    # Test that config can be loaded (requires API key in .env)
    if settings.OPENROUTER_API_KEY:
        print(f"  OPENROUTER_API_KEY: ✅ Set (length: {len(settings.OPENROUTER_API_KEY)})")
    else:
        print(f"  OPENROUTER_API_KEY: ⚠️  Not set (required for real API calls)")

    print("  ✅ Configuration accessible")

async def test_provider_methods():
    """Test that all required methods are implemented."""
    print("\nTesting provider methods...")

    provider = OpenRouterProvider(
        api_key="test-key",
        config={
            "story_model": "anthropic/claude-3.5-sonnet",
            "scene_model": "anthropic/claude-3.5-sonnet",
            "character_model": "anthropic/claude-3.5-sonnet"
        }
    )

    # Check methods exist
    assert hasattr(provider, "generate_story"), "generate_story method missing!"
    assert hasattr(provider, "generate_scene_breakdown"), "generate_scene_breakdown method missing!"
    assert hasattr(provider, "extract_characters"), "extract_characters method missing!"
    assert hasattr(provider, "test_connection"), "test_connection method missing!"

    print("  ✅ All required methods implemented")
    print("     - generate_story()")
    print("     - generate_scene_breakdown()")
    print("     - extract_characters()")
    print("     - test_connection()")

def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenRouter Provider Implementation Tests")
    print("=" * 60)

    try:
        # Synchronous tests
        test_provider_registration()
        test_provider_creation()
        test_configuration()

        # Async tests
        asyncio.run(test_provider_methods())

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        # Additional guidance
        print("\nNext steps:")
        if not settings.OPENROUTER_API_KEY:
            print("  1. Get an API key from https://openrouter.ai/keys")
            print("  2. Add OPENROUTER_API_KEY to your .env file")
            print("  3. Set AI_PROVIDER=openrouter in .env")
            print("  4. Start the backend server and test story generation")
        else:
            print("  1. Set AI_PROVIDER=openrouter in .env")
            print("  2. Start the backend server: uvicorn app.main:app --reload")
            print("  3. Test story generation through the frontend or API")
            print("  4. Try different model combinations for different tasks")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
