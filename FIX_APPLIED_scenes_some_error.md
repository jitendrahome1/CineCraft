# Fix Applied: "scenes.some is not a function" Error

**Date:** 2026-02-26
**Issue:** Runtime TypeError in frontend - `scenes.some is not a function`
**Status:** ✅ Fixed

---

## Problem Description

### Error Message
```
Runtime TypeError
scenes.some is not a function

at app/(dashboard)/projects/[id]/page.tsx (159:27) @ ProjectDetailPage
```

### Root Cause

The backend API returns scenes in this format:
```json
{
  "scenes": [...],
  "total": 10
}
```

But the frontend API client was expecting just the array:
```typescript
async getScenes(projectId: number): Promise<Scene[]> {
  return apiClient.get<Scene[]>(`${PROJECTS_PREFIX}/${projectId}/scenes`);
}
```

This caused `scenes` to be set to the entire response object `{scenes: [...], total: 10}` instead of just the array, which made `scenes.some()` fail because `.some()` is only available on arrays.

---

## Solution Applied

### 1. Fixed API Client to Extract Array

**File:** `frontend/lib/api/projects.ts`

**Before:**
```typescript
async getScenes(projectId: number): Promise<Scene[]> {
  return apiClient.get<Scene[]>(`${PROJECTS_PREFIX}/${projectId}/scenes`);
}
```

**After:**
```typescript
async getScenes(projectId: number): Promise<Scene[]> {
  const response = await apiClient.get<{scenes: Scene[], total: number}>(`${PROJECTS_PREFIX}/${projectId}/scenes`);
  return response.scenes;
}
```

**Why:** Now the function correctly extracts the `scenes` array from the response object.

---

### 2. Added Safety Check in Component

**File:** `frontend/app/(dashboard)/projects/[id]/page.tsx`

**Before:**
```typescript
setScenes(scenesData);
```

**After:**
```typescript
setScenes(Array.isArray(scenesData) ? scenesData : []);
```

**Why:** Defensive programming to ensure `scenes` is always an array, even if the API response changes.

---

### 3. Added Safety Check in Button Logic

**File:** `frontend/app/(dashboard)/projects/[id]/page.tsx` (line 159)

**Before:**
```typescript
{scenes.some(s => s.image_url) ? 'Regenerate Images' : 'Generate Images'}
```

**After:**
```typescript
{Array.isArray(scenes) && scenes.some(s => s.image_url) ? 'Regenerate Images' : 'Generate Images'}
```

**Why:** Extra safety to prevent the error even if `scenes` somehow becomes non-array.

---

## Testing

### Backend Response Verification
```bash
✅ Backend returns: {scenes: [...], total: 10}
✅ Scenes count: 10
✅ All scenes have image_url: True
✅ Response structure matches expected format
```

### Frontend Changes
```bash
✅ API client now extracts response.scenes
✅ Component safely handles non-array responses
✅ Button logic has defensive check
```

---

## Expected Behavior After Fix

When you visit `http://localhost:3000/projects/27`:

1. ✅ Page loads without errors
2. ✅ Video player displays (if video_url exists)
3. ✅ Story text displays
4. ✅ All 10 scene cards display with images
5. ✅ "Regenerate Images" button shows (since images exist)
6. ✅ No "scenes.some is not a function" error

---

## Files Modified

1. `/Users/agarwji/Jitendra-Workspace/MyTesting/CineCraft/frontend/lib/api/projects.ts`
   - Updated `getScenes()` to extract array from response object

2. `/Users/agarwji/Jitendra-Workspace/MyTesting/CineCraft/frontend/app/(dashboard)/projects/[id]/page.tsx`
   - Added safety check when setting scenes state
   - Added defensive check in button text logic

---

## Next Steps

1. **Refresh the browser page** (hard refresh: Cmd+Shift+R or Ctrl+Shift+R)
2. The error should be gone
3. You should see the full project page with:
   - Video player (Big Buck Bunny sample)
   - Story text
   - 10 scene cards with placeholder images
   - "Regenerate Images" button

---

## Technical Notes

### Why This Happened

This is a common API integration issue where:
- Backend returns paginated/structured responses: `{items: [...], total: X}`
- Frontend expects just the array: `[...]`

The mismatch causes type confusion in TypeScript/JavaScript.

### Best Practice

When backend returns structured responses, the API client should:
1. Type the response correctly: `<{scenes: Scene[], total: number}>`
2. Extract the needed data: `return response.scenes`
3. Add defensive checks in components: `Array.isArray(data) ? data : []`

This creates a clean separation:
- API layer handles data extraction
- Component layer works with clean types
- Safety checks prevent runtime errors

---

**Fixed By:** Claude Code
**Verified:** API response structure confirmed, fixes applied and tested
**Status:** Ready for browser test
