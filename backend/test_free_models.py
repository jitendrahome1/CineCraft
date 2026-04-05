"""
Test OpenRouter with FREE models.
"""
import asyncio
from app.providers.ai.factory import get_ai_provider_from_config

async def test_free_models():
    """Test with free models from OpenRouter."""
    print("=" * 60)
    print("Testing OpenRouter with FREE Models")
    print("=" * 60)

    try:
        # Get provider (should use free models now)
        provider = get_ai_provider_from_config()

        print(f"\nProvider: {provider.__class__.__name__}")
        print(f"Story Model: {provider.story_model}")
        print(f"Scene Model: {provider.scene_model}")
        print(f"Character Model: {provider.character_model}")
        print()

        # Test 1: Connection test
        print("Test 1: Connection Test")
        print("-" * 60)
        result = await provider.test_connection()

        if result:
            print("✅ Connection successful with free model!")
        else:
            print("❌ Connection failed")
            return

        # Test 2: Story Generation
        print("\nTest 2: Story Generation")
        print("-" * 60)
        print("Generating a short story...")

        story = await provider.generate_story(
            title="The Lost Puppy",
            context="Write a very short story (3-4 paragraphs) about a child finding a lost puppy"
        )

        print("✅ Story generated successfully!")
        print(f"\nStory Length: {len(story)} characters")
        print("\nGenerated Story:")
        print("=" * 60)
        print(story)
        print("=" * 60)

        # Test 3: Scene Breakdown
        print("\nTest 3: Scene Breakdown")
        print("-" * 60)
        print("Breaking story into scenes...")

        scenes = await provider.generate_scene_breakdown(story)

        print(f"✅ Generated {len(scenes)} scenes")
        for i, scene in enumerate(scenes[:3], 1):  # Show first 3 scenes
            print(f"\nScene {i}:")
            print(f"  Description: {scene.get('description', 'N/A')[:100]}...")
            print(f"  Location: {scene.get('location', 'N/A')}")
            print(f"  Duration: {scene.get('duration', 'N/A')}s")

        # Test 4: Character Extraction
        print("\nTest 4: Character Extraction")
        print("-" * 60)
        print("Extracting characters...")

        characters = await provider.extract_characters(story)

        print(f"✅ Extracted {len(characters)} characters")
        for char in characters:
            print(f"\n  - {char.get('name', 'Unknown')}")
            print(f"    Role: {char.get('role', 'N/A')}")
            print(f"    Description: {char.get('description', 'N/A')[:100]}...")

        print("\n" + "=" * 60)
        print("🎉 All tests passed with FREE models!")
        print("=" * 60)
        print("\n💡 You can now use CineCraft with FREE OpenRouter models")
        print("   Later, you can upgrade to paid models for better quality:")
        print("   - anthropic/claude-3.5-sonnet")
        print("   - openai/gpt-4-turbo")
        print("   - google/gemini-pro")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_free_models())
