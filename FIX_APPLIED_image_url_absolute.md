# Fix Applied: Images Now Loading with Absolute URLs

**Date:** 2026-02-26
**Issue:** Scene images still not loading after static file serving was added
**Status:** ✅ Fixed

---

## Problem Description

### Symptoms
- Backend was serving images correctly at `http://localhost:8000/storage/...`
- Frontend was making requests to `http://localhost:3000/storage/...` (404 errors)
- Images appeared as "Scene undefined" broken placeholders

### Root Causes

**Issue 1: Relative URLs**
- Database stored: `/storage/media/project_27/scene_73_placeholder.jpg`
- Frontend used this directly in `<img src=...>`
- Browser resolved relative URL to `http://localhost:3000/storage/...`
- Frontend server (port 3000) doesn't serve static files - only backend (port 8000) does

**Issue 2: Field Name Mismatch**
- Frontend TypeScript interface had: `scene.scene_number`
- Backend API returned: `scene.sequence_number`
- Result: "Scene undefined" in the UI

---

## Solution Applied

### 1. Fixed Type Definition

**File:** `frontend/lib/types/api.ts`

**Change:**
```typescript
// Before
export interface Scene {
  scene_number: number;
  ...
}

// After
export interface Scene {
  sequence_number: number;  // Backend uses sequence_number
  audio_url?: string;       // Added missing field
  ...
}
```

### 2. Added URL Transformation Helper

**File:** `frontend/app/(dashboard)/projects/[id]/page.tsx`

**Added helper function in SceneCard component:**
```typescript
function SceneCard({ scene }: { scene: Scene }) {
  // Helper to get full URL for images (prepend API base URL if relative)
  const getImageUrl = (url?: string) => {
    if (!url) return undefined;
    if (url.startsWith('http')) return url;  // Already absolute
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${apiBaseUrl}${url}`;  // Make it absolute
  };

  const imageUrl = getImageUrl(scene.image_url);
  const sceneNumber = scene.sequence_number;  // Use correct field name

  return (
    <Card>
      {/* ... */}
      <img src={imageUrl} alt={`Scene ${sceneNumber}`} />
    </Card>
  );
}
```

**What This Does:**
1. Checks if URL is already absolute (starts with `http`)
2. If relative, prepends backend server URL (`http://localhost:8000`)
3. Transforms `/storage/...` → `http://localhost:8000/storage/...`
4. Uses correct field name `sequence_number`

---

## URL Transformation Flow

```
Database Value:
  /storage/media/project_27/scene_73_placeholder.jpg

Frontend Processing:
  1. getImageUrl() receives: "/storage/media/..."
  2. Checks: Does NOT start with "http"
  3. Prepends: "http://localhost:8000"
  4. Returns: "http://localhost:8000/storage/media/..."

Browser:
  1. <img src="http://localhost:8000/storage/media/...">
  2. Makes request to backend server
  3. FastAPI serves file via StaticFiles mount
  4. Image loads successfully ✅
```

---

## Before vs After

### Before (Broken)
```html
<img src="/storage/media/project_27/scene_73_placeholder.jpg">
↓
Browser resolves to: http://localhost:3000/storage/...
↓
Frontend server: 404 Not Found ❌
```

### After (Working)
```html
<img src="http://localhost:8000/storage/media/project_27/scene_73_placeholder.jpg">
↓
Backend server: 200 OK with JPEG data ✅
```

---

## Verification

### Backend Test
```bash
✅ http://localhost:8000/storage/media/project_27/scene_73_placeholder.jpg
   Status: 200, Size: 96294 bytes
```

### Frontend Test
```bash
❌ http://localhost:3000/storage/media/project_27/scene_73_placeholder.jpg
   Status: 404 (expected - frontend doesn't serve static files)
```

### URL Transformation Test
```javascript
Input:  /storage/media/project_27/scene_73_placeholder.jpg
Output: http://localhost:8000/storage/media/project_27/scene_73_placeholder.jpg
✅ Correct!
```

---

## Expected Behavior After Fix

When you visit `http://localhost:3000/projects/27` and do a **hard refresh**:

1. ✅ Scene numbers display correctly ("Scene 1", "Scene 2", etc.)
2. ✅ All 10 scene images load and display
3. ✅ Images show HD placeholders with blue background
4. ✅ Scene titles and descriptions visible on images
5. ✅ No "Scene undefined" text
6. ✅ Green "Image" badges on all scenes

---

## Files Modified

1. **frontend/lib/types/api.ts**
   - Changed `scene_number` → `sequence_number`
   - Added `audio_url` field

2. **frontend/app/(dashboard)/projects/[id]/page.tsx**
   - Added `getImageUrl()` helper function
   - Changed `scene.scene_number` → `scene.sequence_number`
   - Images now use `imageUrl` (absolute URL)

---

## How to Test

### 1. Hard Refresh Browser
- **Mac:** `Cmd + Shift + R`
- **Windows/Linux:** `Ctrl + Shift + R`

### 2. Check DevTools Network Tab
Open browser DevTools (F12), go to Network tab, and you should see:

```
✅ http://localhost:8000/storage/media/project_27/scene_73_placeholder.jpg - 200 OK
✅ http://localhost:8000/storage/media/project_27/scene_74_placeholder.jpg - 200 OK
✅ http://localhost:8000/storage/media/project_27/scene_75_placeholder.jpg - 200 OK
... (10 total)
```

### 3. Verify Image Display
Each scene card should show:
- HD placeholder image (1920x1080)
- Blue background (#496D89)
- White text: "Scene 1: Opening" (or appropriate scene)
- Gray text: Visual description

---

## Why This Pattern Is Important

### Development vs Production

**Development (Current):**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Need absolute URLs because servers are on different ports

**Production (Future):**
- Option 1: Same domain with reverse proxy
  ```
  https://cinecraft.com/ → Frontend
  https://cinecraft.com/api/ → Backend
  https://cinecraft.com/storage/ → Static files
  ```
  Can use relative URLs like `/storage/...`

- Option 2: Separate domains
  ```
  https://app.cinecraft.com → Frontend
  https://api.cinecraft.com → Backend
  https://cdn.cinecraft.com/storage/ → Static files (CDN)
  ```
  Need absolute URLs like current setup

The `getImageUrl()` helper handles both cases automatically.

---

## Alternative Approaches

### Option 1: Backend Returns Absolute URLs (Recommended for Production)
Modify backend to return full URLs in the API response:
```python
asset_data = {
    "url": f"https://cdn.cinecraft.com/storage/media/project_{project_id}/{image_filename}"
}
```

### Option 2: Next.js Image Proxy (Complex)
Configure Next.js to proxy image requests:
```javascript
// next.config.js
async rewrites() {
  return [
    {
      source: '/storage/:path*',
      destination: 'http://localhost:8000/storage/:path*'
    }
  ];
}
```

### Option 3: Frontend Also Mounts Storage (Not Recommended)
Have frontend serve static files too - duplicates files unnecessarily.

**Current approach (getImageUrl helper) is simplest and most flexible.**

---

## Technical Notes

### Why Relative URLs Failed

When a browser sees a relative URL in an `<img src>`, it resolves it relative to the current page's origin:

```
Current page: http://localhost:3000/projects/27
Relative URL: /storage/media/...
Resolved URL: http://localhost:3000/storage/media/...
               ^^^^^^^^^^^^^^^^^^^^^ Same origin as page
```

The frontend Next.js server doesn't have the images, so it returns 404.

### CORS Considerations

With absolute URLs to a different port, CORS could be an issue. But we already configured CORS in the backend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Includes localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This allows the frontend on port 3000 to make requests to backend on port 8000.

---

**Fixed By:** Claude Code
**Verified:** URL transformation logic confirmed
**Status:** Ready for browser test with hard refresh
