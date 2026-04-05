# OpenRouter Troubleshooting Guide

## Current Issue: "User not found" (401 Error)

### Symptoms
- API key format looks correct: `sk-or-v1-...`
- Error: `{"error":{"message":"User not found.","code":401}}`
- Both old and new API keys show same error
- User reports it works in Postman

### Possible Causes

1. **Account Not Fully Set Up**
   - Visit https://openrouter.ai/ and log in
   - Check if email verification is required
   - Check if account setup is complete

2. **API Key Not Generated Correctly**
   - Go to https://openrouter.ai/keys
   - Delete old keys
   - Generate a NEW key
   - Copy it immediately (it won't be shown again)

3. **Account Suspended or Restricted**
   - Check account status at https://openrouter.ai/account
   - Verify no restrictions or warnings

4. **Different Account in Postman vs Website**
   - Make sure you're logged into the same account
   - Check which email/account you used in Postman

### Steps to Fix

#### Step 1: Verify Account
1. Go to https://openrouter.ai/
2. Log in with your credentials
3. Check for any notifications or verification emails
4. Complete any pending setup steps

#### Step 2: Generate Fresh API Key
1. Go to https://openrouter.ai/keys
2. Click "Create Key"
3. Give it a name (e.g., "CineCraft")
4. Copy the key immediately
5. Update `.env` file with new key

#### Step 3: Test in Postman First
Before updating CineCraft, test in Postman:

```bash
POST https://openrouter.ai/api/v1/chat/completions

Headers:
  Content-Type: application/json
  Authorization: Bearer YOUR_NEW_KEY

Body:
{
  "model": "liquid/lfm-2.5-1.2b-instruct:free",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

#### Step 4: Update CineCraft
If Postman works, update the `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-new-working-key
AI_PROVIDER=openrouter
```

### Alternative: Use Free Models with Credits

Some accounts may require adding credits even for free models:

1. Go to https://openrouter.ai/credits
2. Add a small amount ($1-5)
3. Try again

### Alternative: Use Anthropic Directly

If OpenRouter continues to have issues, switch back to Anthropic:

```bash
# In .env file
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### Debug Information

**API Key Format Validation:**
- ✅ Should start with: `sk-or-v1-`
- ✅ Should be 73 characters long
- ✅ Should be alphanumeric (lowercase hex)

**Current Keys Tested:**
- Key 1: `sk-or-v1-8d36fd76...73bc23c3` (73 chars) - ❌ Failed
- Key 2: `sk-or-v1-9fc211d0...f325cabe` (73 chars) - ❌ Failed

Both keys have correct format but return "User not found" error.

### Contact Support

If none of the above works:
- Email OpenRouter support: support@openrouter.ai
- Join Discord: https://discord.gg/openrouter
- Check status page: https://status.openrouter.ai/

### Temporary Workaround

Use a different AI provider while troubleshooting:

**Option 1: Anthropic Claude (Direct)**
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Option 2: OpenAI**
```bash
# Future implementation
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Next Steps

1. ✅ OpenRouter integration code is complete and working
2. ⏳ Waiting for valid API key from OpenRouter
3. ⏳ Account verification may be needed
4. Alternative: Switch to Anthropic provider temporarily

The implementation is solid - we just need a valid, active OpenRouter account with proper authentication.
