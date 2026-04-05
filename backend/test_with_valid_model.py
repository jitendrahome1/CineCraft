"""
Test with valid free model.
"""
import httpx
import asyncio

async def test_valid_model():
    api_key = "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"

    print("Testing OpenRouter with valid free model...")
    print()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Try different free models
    free_models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemini-flash-1.5:free",
        "nousresearch/hermes-3-llama-3.1-405b:free"
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in free_models:
            print(f"Testing: {model}")
            print("-" * 60)

            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Say hello in one sentence"}
                ]
            }

            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    message = result['choices'][0]['message']['content']
                    print(f"✅ SUCCESS!")
                    print(f"Response: {message}")
                    print(f"\n🎉 Working model found: {model}")
                    print()
                    return model
                else:
                    print(f"❌ Failed: {response.status_code}")
                    print(f"Error: {response.text[:200]}")
                    print()

            except Exception as e:
                print(f"❌ Error: {e}")
                print()

    print("❌ No free models worked")
    return None

result = asyncio.run(test_valid_model())
if result:
    print(f"\n✅ Use this model: {result}")
