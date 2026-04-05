# OpenRouter Integration Guide

## Overview

CineCraft now supports **OpenRouter** as an AI provider, giving you access to 100+ AI models from multiple providers (Anthropic Claude, OpenAI GPT, Google Gemini, Meta Llama, and more) through a single unified API.

## Why OpenRouter?

- **Flexibility**: Access to 100+ models instead of being locked to one provider
- **Cost Optimization**: Choose cheaper models for non-critical tasks
- **Best-of-Breed**: Use the best model for each specific task
- **Fallback Support**: Switch providers if one is down or rate-limited
- **Future-Proof**: Test new models without code changes

## Quick Start

### 1. Get an API Key

Sign up and get your API key from: https://openrouter.ai/keys

### 2. Configure Environment

Edit your `.env` file:

```bash
# Switch to OpenRouter provider
AI_PROVIDER=openrouter

# Add your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# Configure models (these are the defaults)
OPENROUTER_STORY_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SCENE_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_CHARACTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 3. Restart Backend

```bash
uvicorn app.main:app --reload
```

That's it! Your story generation will now use OpenRouter.

## Configuration Strategies

### High Quality (Claude for Everything)

Best quality, higher cost:

```bash
OPENROUTER_STORY_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SCENE_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_CHARACTER_MODEL=anthropic/claude-3.5-sonnet
```

### Cost Optimized

Balanced quality and cost:

```bash
OPENROUTER_STORY_MODEL=anthropic/claude-3.5-sonnet  # Quality for creative writing
OPENROUTER_SCENE_MODEL=openai/gpt-4o-mini           # Cheaper for structured output
OPENROUTER_CHARACTER_MODEL=openai/gpt-3.5-turbo     # Cheapest for extraction
```

### Best of Breed

Use the best model for each task:

```bash
OPENROUTER_STORY_MODEL=anthropic/claude-3-opus          # Most creative
OPENROUTER_SCENE_MODEL=openai/gpt-4-turbo              # Best structured output
OPENROUTER_CHARACTER_MODEL=google/gemini-pro           # Fast extraction
```

### Speed Optimized

Fastest response times:

```bash
OPENROUTER_STORY_MODEL=anthropic/claude-3-haiku
OPENROUTER_SCENE_MODEL=anthropic/claude-3-haiku
OPENROUTER_CHARACTER_MODEL=openai/gpt-3.5-turbo
```

## Available Models

OpenRouter provides access to 100+ models. Here are some popular choices:

### Anthropic Claude
- `anthropic/claude-3.5-sonnet` - **Recommended** for quality (balanced cost/performance)
- `anthropic/claude-3-opus` - Highest quality (most expensive)
- `anthropic/claude-3-sonnet` - Good balance
- `anthropic/claude-3-haiku` - Fastest and cheapest

### OpenAI GPT
- `openai/gpt-4-turbo` - High quality structured output
- `openai/gpt-4o` - Latest GPT-4 optimized
- `openai/gpt-4o-mini` - Cheaper GPT-4 variant
- `openai/gpt-3.5-turbo` - Fast and cheap

### Google Gemini
- `google/gemini-pro` - Good for extraction and analysis
- `google/gemini-pro-1.5` - Latest version with longer context

### Meta Llama
- `meta-llama/llama-3-70b-instruct` - Open-source, good quality
- `meta-llama/llama-3.1-405b-instruct` - Largest Llama model

### Other Notable Models
- `mistralai/mistral-large` - European provider
- `perplexity/llama-3.1-sonar-huge-128k-online` - Has web search capability
- `anthropic/claude-3.5-sonnet:thinking` - Extended thinking mode

**Full model list**: https://openrouter.ai/models

## Model Selection Guide

### For Story Generation (Creative Writing)

**Best choices**:
1. `anthropic/claude-3.5-sonnet` - Excellent creative writing (recommended)
2. `anthropic/claude-3-opus` - Highest quality but expensive
3. `openai/gpt-4-turbo` - Good alternative

**Temperature**: 1.0 (high creativity)

### For Scene Breakdown (Structured Output)

**Best choices**:
1. `anthropic/claude-3.5-sonnet` - Reliable JSON output (recommended)
2. `openai/gpt-4-turbo` - Excellent at structured data
3. `openai/gpt-4o` - Fast structured output

**Temperature**: 0.7 (balanced)

### For Character Extraction (Precise Extraction)

**Best choices**:
1. `anthropic/claude-3.5-sonnet` - Good extraction (recommended)
2. `google/gemini-pro` - Fast extraction
3. `openai/gpt-3.5-turbo` - Cheapest option

**Temperature**: 0.5 (precise)

## Switching Between Providers

You can easily switch between Anthropic and OpenRouter:

### Use Anthropic Directly

```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

### Use OpenRouter (with Claude)

```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_STORY_MODEL=anthropic/claude-3.5-sonnet
```

### Use OpenRouter (with GPT-4)

```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_STORY_MODEL=openai/gpt-4-turbo
```

## Cost Comparison

Approximate costs per 1M tokens (as of 2024):

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| claude-3.5-sonnet | $3 | $15 | Balanced quality/cost |
| claude-3-opus | $15 | $75 | Maximum quality |
| claude-3-haiku | $0.25 | $1.25 | Speed/cost |
| gpt-4-turbo | $10 | $30 | Structured output |
| gpt-4o-mini | $0.15 | $0.60 | Budget option |
| gpt-3.5-turbo | $0.50 | $1.50 | Cheapest |
| gemini-pro | $0.50 | $1.50 | Extraction |

**Note**: Check https://openrouter.ai/models for current pricing.

## Testing Your Configuration

Run the test script to verify your setup:

```bash
cd backend
python3 test_openrouter.py
```

This will verify:
- ✅ Provider is registered
- ✅ Configuration is loaded
- ✅ All methods are implemented
- ✅ Models are configured correctly

## Architecture

OpenRouter integration follows the existing provider pattern:

```
AIProvider (Abstract Base Class)
    ├── AnthropicProvider
    └── OpenRouterProvider (NEW)
```

### Key Components

1. **Provider Class**: `app/providers/ai/openrouter.py`
   - Implements `AIProvider` interface
   - Three methods: `generate_story()`, `generate_scene_breakdown()`, `extract_characters()`
   - Uses AsyncOpenAI client (OpenRouter is OpenAI-compatible)

2. **Factory**: `app/providers/ai/factory.py`
   - Registers OpenRouter provider
   - Builds configuration from environment variables

3. **Configuration**: `app/core/config.py`
   - Settings for API key and model selection

## API Usage

OpenRouter uses OpenAI-compatible API format:

```python
response = await client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {"role": "user", "content": "Tell me a story about..."}
    ],
    max_tokens=4096,
    temperature=1.0
)
```

## Error Handling

The provider includes comprehensive error handling:

- **Invalid API Key**: Returns clear error message
- **Rate Limiting**: Logs and propagates error
- **Model Not Found**: Falls back gracefully
- **JSON Parsing**: Handles markdown code blocks in responses

## Performance Tips

1. **Use appropriate models per task**: Don't use expensive models for simple tasks
2. **Monitor costs**: Check OpenRouter dashboard for usage
3. **Test different combinations**: Find the sweet spot for your use case
4. **Cache results**: Store generated content to avoid re-generation

## Troubleshooting

### "No API key configured"

Make sure you've set `OPENROUTER_API_KEY` in your `.env` file.

### "Unknown AI provider: openrouter"

Make sure you've installed the `openai` package:
```bash
pip install openai==1.12.0
```

### "Model not found"

Check the model name is correct. List available models at: https://openrouter.ai/models

Model names are case-sensitive and must include the provider prefix:
- ✅ `anthropic/claude-3.5-sonnet`
- ❌ `claude-3.5-sonnet`

### JSON parsing errors

Some models may return JSON wrapped in markdown code blocks. The provider automatically strips these, but if you encounter issues, try a different model.

## Migration from Anthropic

If you're currently using Anthropic directly, migration is seamless:

1. Keep your existing configuration working:
   ```bash
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. Add OpenRouter configuration:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_STORY_MODEL=anthropic/claude-3.5-sonnet
   ```

3. Test with OpenRouter using the same Claude model:
   ```bash
   AI_PROVIDER=openrouter
   ```

4. Once verified, experiment with other models:
   ```bash
   OPENROUTER_SCENE_MODEL=openai/gpt-4-turbo
   ```

## Future Enhancements

Potential future additions:

- [ ] Frontend UI for model selection in settings
- [ ] Model cost tracking in analytics
- [ ] Automatic fallback if provider fails
- [ ] A/B testing different models
- [ ] Model performance benchmarking
- [ ] Per-user model preferences

## Support

For issues with:
- **OpenRouter API**: https://openrouter.ai/docs
- **Model selection**: Check model docs at https://openrouter.ai/models
- **Integration issues**: Check CineCraft backend logs

## References

- OpenRouter API Docs: https://openrouter.ai/docs
- Available Models: https://openrouter.ai/models
- Pricing: https://openrouter.ai/models (pricing column)
- API Keys: https://openrouter.ai/keys
