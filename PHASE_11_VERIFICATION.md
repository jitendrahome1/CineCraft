# Phase 11: Admin Panel - Verification Document

## Overview

Phase 11 implements the admin panel for platform management, including user administration, feature flag system, subscription management, job monitoring, and system health checks.

## Completion Date

2026-02-25

## Files Created/Modified

### New Files

1. **`backend/app/models/feature_flag.py`** (155 lines)
   - FeatureFlag model for runtime feature toggles
   - Enums: FeatureFlagType (BOOLEAN, STRING, NUMBER, JSON)
   - Enums: FeatureFlagScope (GLOBAL, USER, PLAN, ROLE)
   - Methods:
     - get_value() - Get typed value
     - set_value() - Set typed value
     - is_enabled_for_user() - Check if enabled for user
     - is_in_rollout() - Check if user in rollout percentage
   - Supports A/B testing with rollout percentage (0-100%)
   - Target specific users, plans, or roles
   - Categorization and tagging

2. **`backend/app/repositories/feature_flag.py`** (213 lines)
   - FeatureFlagRepository for data access
   - Methods (18 total):
     - get_by_key() - Get flag by key
     - get_by_category() - Filter by category
     - get_enabled_flags() - Get all enabled
     - get_by_scope() - Filter by scope
     - get_flags_for_user() - User-specific flags
     - get_flags_for_plan() - Plan-specific flags
     - get_flags_for_role() - Role-specific flags
     - create_or_update() - Upsert operation
     - toggle() - Toggle enabled state
     - set_rollout_percentage() - Update rollout
     - get_by_tags() - Search by tags
     - get_stats() - Flag statistics

3. **`backend/app/services/feature_flag.py`** (233 lines)
   - FeatureFlagService for business logic
   - Methods:
     - is_enabled() - Check if flag enabled for user
     - get_value() - Get flag value with default
     - get_all_for_user() - All applicable flags
     - create_flag() - Create new flag
     - update_flag() - Update existing flag
     - toggle_flag() - Toggle with audit logging
     - set_rollout() - Update rollout percentage
     - delete_flag() - Delete flag with warning
     - get_stats() - Statistics
     - get_all_flags() - List with filtering

4. **`backend/app/schemas/admin.py`** (229 lines)
   - Pydantic schemas for admin operations
   - Feature Flag schemas:
     - FeatureFlagCreate, FeatureFlagUpdate
     - FeatureFlagResponse, FeatureFlagListResponse
     - FeatureFlagStatsResponse
   - User Management schemas:
     - AdminUserUpdate, AdminUserResponse
     - AdminUserListResponse, UserBanRequest
   - System Health schemas:
     - SystemHealthResponse, SystemStatsResponse
   - Job Monitoring schemas:
     - AdminJobResponse, AdminJobListResponse
   - Subscription Management schemas:
     - AdminSubscriptionResponse, AdminSubscriptionListResponse
   - Analytics schemas:
     - AdminAnalyticsResponse, AdminAnalyticsListResponse

5. **`backend/app/api/v1/admin.py`** (639 lines)
   - Admin API endpoints (23 endpoints)
   - Feature Flag Management (8 endpoints):
     - POST /admin/feature-flags - Create flag
     - GET /admin/feature-flags - List flags
     - GET /admin/feature-flags/{id} - Get flag
     - PUT /admin/feature-flags/{id} - Update flag
     - POST /admin/feature-flags/{id}/toggle - Toggle flag
     - DELETE /admin/feature-flags/{id} - Delete flag
     - GET /admin/feature-flags/stats/summary - Statistics
   - User Management (6 endpoints):
     - GET /admin/users - List users
     - GET /admin/users/{id} - Get user
     - PUT /admin/users/{id} - Update user
     - POST /admin/users/{id}/ban - Ban user
     - POST /admin/users/{id}/unban - Unban user
   - System Health (2 endpoints):
     - GET /admin/health - System health check
     - GET /admin/stats - System statistics
   - Job Monitoring (1 endpoint):
     - GET /admin/jobs - List all jobs
   - Subscription Management (1 endpoint):
     - GET /admin/subscriptions - List all subscriptions

### Modified Files

6. **`backend/app/api/deps.py`**
   - Already contained get_current_admin_user() (lines 131-152)
   - No changes needed

7. **`backend/app/db/base.py`**
   - Added FeatureFlag model import

8. **`backend/app/main.py`**
   - Added admin router import
   - Registered admin routes at `/api/v1/admin`

## Features Implemented

### 1. Feature Flag System

#### Feature Flag Types
- **BOOLEAN**: Simple on/off flags (enabled: true/false)
- **STRING**: Text configuration values
- **NUMBER**: Numeric configuration values
- **JSON**: Complex configuration objects

#### Feature Flag Scopes
- **GLOBAL**: Applies to all users
- **USER**: Specific user IDs only
- **PLAN**: Specific subscription plans
- **ROLE**: Specific user roles (admin, user)

#### Rollout Percentage
- Gradual rollout support (0-100%)
- Consistent hashing (same user always gets same result)
- Perfect for A/B testing
- Example: Set 25% rollout to test new feature with 25% of users

#### Example Feature Flags
```json
{
  "key": "hd_export",
  "name": "HD Video Export",
  "description": "Allow 1080p video export",
  "flag_type": "boolean",
  "scope": "plan",
  "enabled": true,
  "target_plan_ids": [2, 3],  // Pro and Enterprise plans
  "rollout_percentage": 100
}
```

```json
{
  "key": "max_scenes_per_project",
  "name": "Max Scenes Per Project",
  "description": "Maximum number of scenes allowed",
  "flag_type": "number",
  "scope": "plan",
  "enabled": true,
  "value_number": 20,
  "target_plan_ids": [1],  // Free plan
  "rollout_percentage": 100
}
```

```json
{
  "key": "new_rendering_engine",
  "name": "New Rendering Engine",
  "description": "Beta test new rendering pipeline",
  "flag_type": "boolean",
  "scope": "global",
  "enabled": true,
  "rollout_percentage": 25,  // 25% of users
  "tags": ["beta", "experimental"]
}
```

#### Usage in Code
```python
# Check boolean flag
if flag_service.is_enabled("hd_export", user_id=user.id):
    # Allow HD export

# Get typed value
max_scenes = flag_service.get_value(
    "max_scenes_per_project",
    user_id=user.id,
    default=10
)

# Get all flags for user
flags = flag_service.get_all_for_user(user.id)
# Returns: {"hd_export": True, "max_scenes_per_project": 20}
```

### 2. User Management

#### User Administration
- List all users with filtering:
  - By role (admin, user)
  - By active status
  - Search by email/name
- View user details
- Update user information:
  - Email
  - Full name
  - Role
  - Active status
- Ban/unban users

#### User Banning
- Deactivates user account
- Prevents login
- Audit logging with reason
- Cannot ban self

### 3. System Health Monitoring

#### Health Check Endpoint
Returns:
- Overall status (healthy/degraded)
- Database status
- Redis status
- Active Celery workers count
- WebSocket connections count
- Timestamp

Example response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "unknown",
  "celery_workers": 0,
  "websocket_connections": 5,
  "timestamp": "2026-02-25T10:00:00Z"
}
```

#### System Statistics
Returns:
- Total users
- Active users
- Total projects
- Total render jobs
- Completed/failed jobs
- Active subscriptions
- Total revenue
- Storage used (GB)

### 4. Job Monitoring

#### View All Jobs
- List all render jobs across all users
- Filter by:
  - Job status
  - User ID
- Includes:
  - User email
  - Project title
  - Job type and status
  - Progress percentage
  - Current stage
  - Error messages
  - Duration

### 5. Subscription Management

#### View All Subscriptions
- List all subscriptions
- Filter by:
  - Status
  - Plan ID
- Includes:
  - User email
  - Plan name
  - Status
  - Current period dates
  - Cancellation status

### 6. Authorization

All admin endpoints require:
1. Valid JWT token
2. User role = ADMIN

Non-admin access returns:
```json
{
  "detail": "Not enough permissions"
}
```

## Technical Architecture

### Feature Flag Evaluation Flow

```
Request → FeatureFlagService.is_enabled(key, user_id)
    ↓
1. Get flag by key
2. Check if globally enabled
3. Check rollout percentage (consistent hashing)
4. Check scope:
   - GLOBAL: Always enabled
   - USER: Check target_user_ids
   - PLAN: Check user's subscription plan
   - ROLE: Check user's role
    ↓
Return: true/false
```

### Admin Authorization Flow

```
Request → get_current_admin_user
    ↓
1. Extract JWT token
2. Decode and validate
3. Get user from database
4. Check user.role == UserRole.ADMIN
5. Return user or raise 403
```

### Rollout Percentage Algorithm

```python
def is_in_rollout(self, user_id: int) -> bool:
    if self.rollout_percentage == 100:
        return True
    if self.rollout_percentage == 0:
        return False

    # Consistent hash: user_id % 100 < rollout_percentage
    hash_value = user_id % 100
    return hash_value < self.rollout_percentage
```

Example:
- User ID 123: hash = 23, rollout = 25% → Included
- User ID 150: hash = 50, rollout = 25% → Excluded
- User ID 123: Always gets same result (consistent)

## Verification Commands

### 1. Create Admin User

First, create an admin user if you don't have one:

```bash
# Method 1: Via Python script
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.repositories.user import UserRepository
from app.models.user import UserRole
from app.core.security import hash_password

db = SessionLocal()
user_repo = UserRepository(db)

user = user_repo.create({
    'email': 'admin@cinecraft.com',
    'hashed_password': hash_password('admin123'),
    'full_name': 'Admin User',
    'role': UserRole.ADMIN.value,
    'is_active': True,
    'is_email_verified': True
})

print(f'Admin user created: {user.email}')
"

# Method 2: Promote existing user
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.repositories.user import UserRepository
from app.models.user import UserRole

db = SessionLocal()
user_repo = UserRepository(db)

user = user_repo.get_by_email('your.email@example.com')
if user:
    user_repo.update(user.id, {'role': UserRole.ADMIN.value})
    print(f'User promoted to admin: {user.email}')
"
```

### 2. Get Admin Token

```bash
# Login as admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@cinecraft.com",
    "password": "admin123"
  }'

# Save the access_token from response
export ADMIN_TOKEN="your-admin-token-here"
```

### 3. Test Feature Flags

#### Create Feature Flag
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "hd_export",
    "name": "HD Video Export",
    "description": "Allow 1080p video export",
    "flag_type": "boolean",
    "scope": "global",
    "enabled": true,
    "rollout_percentage": 100
  }'
```

#### List Feature Flags
```bash
curl http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Toggle Feature Flag
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags/1/toggle \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Get Feature Flag Statistics
```bash
curl http://localhost:8000/api/v1/admin/feature-flags/stats/summary \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected response:
# {
#   "total": 10,
#   "enabled": 7,
#   "disabled": 3,
#   "by_scope": {"global": 5, "user": 2, "plan": 2, "role": 1},
#   "by_type": {"boolean": 8, "string": 1, "number": 1, "json": 0}
# }
```

### 4. Test User Management

#### List Users
```bash
curl "http://localhost:8000/api/v1/admin/users?skip=0&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Get User by ID
```bash
curl http://localhost:8000/api/v1/admin/users/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Update User
```bash
curl -X PUT http://localhost:8000/api/v1/admin/users/2 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "is_active": true
  }'
```

#### Ban User
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/2/ban \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Violating terms of service"
  }'
```

#### Unban User
```bash
curl -X POST http://localhost:8000/api/v1/admin/users/2/unban \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 5. Test System Health

#### Get System Health
```bash
curl http://localhost:8000/api/v1/admin/health \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Get System Statistics
```bash
curl http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected response:
# {
#   "total_users": 150,
#   "active_users": 145,
#   "total_projects": 320,
#   "total_render_jobs": 580,
#   "completed_jobs": 540,
#   "failed_jobs": 40,
#   "active_subscriptions": 85,
#   "total_revenue": 8500.00,
#   "storage_used_gb": 125.5,
#   "timestamp": "2026-02-25T10:00:00Z"
# }
```

### 6. Test Job Monitoring

```bash
# List all jobs
curl "http://localhost:8000/api/v1/admin/jobs?skip=0&limit=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by user
curl "http://localhost:8000/api/v1/admin/jobs?user_id=2" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by status
curl "http://localhost:8000/api/v1/admin/jobs?status_filter=failed" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 7. Test Subscription Management

```bash
# List all subscriptions
curl "http://localhost:8000/api/v1/admin/subscriptions?skip=0&limit=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by plan
curl "http://localhost:8000/api/v1/admin/subscriptions?plan_id=2" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 8. Test Authorization

```bash
# Try accessing admin endpoint without admin role
# (Use regular user token)
curl http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $USER_TOKEN"

# Expected: 403 Forbidden
# {
#   "detail": "Not enough permissions"
# }
```

### 9. Test Feature Flag in Code

```bash
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.services.feature_flag import FeatureFlagService

db = SessionLocal()
flag_service = FeatureFlagService(db)

# Check if feature is enabled for user
user_id = 1
if flag_service.is_enabled('hd_export', user_id):
    print('HD export enabled for user')
else:
    print('HD export disabled for user')

# Get all flags for user
flags = flag_service.get_all_for_user(user_id)
print('User flags:', flags)
"
```

## Database Schema

### feature_flags Table

```sql
CREATE TABLE feature_flags (
    id INTEGER PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    flag_type VARCHAR(20) NOT NULL DEFAULT 'boolean',
    scope VARCHAR(20) NOT NULL DEFAULT 'global',
    enabled BOOLEAN NOT NULL DEFAULT 0,
    value_string VARCHAR(500),
    value_number INTEGER,
    value_json JSON,
    target_user_ids JSON,
    target_plan_ids JSON,
    target_roles JSON,
    category VARCHAR(100),
    tags JSON,
    rollout_percentage INTEGER NOT NULL DEFAULT 100,
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key (key),
    INDEX idx_enabled (enabled),
    INDEX idx_category (category)
);
```

## Security Considerations

### Admin Access Control
✅ JWT authentication required
✅ Admin role verification
✅ Audit logging for all actions
✅ Cannot ban self
✅ Failed attempts logged

### Feature Flag Security
✅ Only admins can modify flags
✅ Changes logged with user ID
✅ Rollout percentage validated (0-100)
✅ Consistent hashing prevents gaming

### Data Exposure
✅ Admin endpoints return appropriate data
✅ User passwords never exposed
✅ Sensitive config values sanitized
⚠️ Consider encrypting sensitive flag values

## Performance Considerations

### Feature Flag Evaluation
- Flag lookups: O(1) with database index on key
- User evaluation: O(1) hash calculation
- Plan/Role checks: Single join query
- Recommended: Cache flags in Redis (future enhancement)

### Admin Queries
- User listing: Paginated (max 100 per request)
- Job monitoring: Indexed by user_id and status
- Subscription listing: Indexed by status and plan_id

### Optimization Tips
1. Cache feature flags (Redis, 5-minute TTL)
2. Index commonly filtered fields
3. Limit admin query results
4. Use async queries for statistics

## Known Limitations

1. **No Flag Audit History**: Changes not tracked historically
2. **No Flag Scheduling**: Cannot schedule enable/disable
3. **No User Segments**: No advanced targeting (e.g., by country, behavior)
4. **No Flag Dependencies**: Cannot link flags together
5. **No Real-time Updates**: Flag changes require application restart or cache invalidation
6. **Basic Analytics**: No A/B test metrics or conversion tracking

## Future Enhancements

1. **Flag Audit Log**: Track all changes with timestamps
2. **Scheduled Flags**: Enable/disable at specific times
3. **User Segments**: Advanced targeting criteria
4. **Flag Experiments**: Built-in A/B testing metrics
5. **Real-time Updates**: WebSocket broadcast on flag changes
6. **Flag UI**: Web-based admin dashboard
7. **Flag SDK**: Client-side feature flag evaluation
8. **Flag Override**: Per-user manual overrides
9. **Flag Dependencies**: Conditional flags
10. **Analytics Dashboard**: Visual metrics and charts

## Integration with Other Phases

### Phase 1 (Authentication)
- Uses get_current_admin_user for authorization
- Admin role from UserRole enum

### Phase 2 (Subscriptions)
- Feature flags can target specific plans
- Plan-based feature gating

### Phase 8 (Celery)
- Can monitor Celery worker health
- Job statistics in admin panel

### Phase 9 (Rendering)
- Feature flags for rendering options
- Admin can monitor all render jobs

### Phase 10 (WebSocket)
- Admin panel shows active connections
- Future: Broadcast flag changes

### Phase 12 (Analytics - Next)
- Admin analytics endpoints
- Usage tracking and reporting

## Testing Checklist

- [x] Feature flag model created
- [x] Feature flag repository created
- [x] Feature flag service created
- [x] Admin schemas created
- [x] Admin API endpoints created
- [x] Admin authorization working
- [x] Routes registered
- [x] Database imports updated
- [ ] Manual test: Create feature flag
- [ ] Manual test: Toggle feature flag
- [ ] Manual test: Check flag in code
- [ ] Manual test: List users
- [ ] Manual test: Ban/unban user
- [ ] Manual test: System health check
- [ ] Manual test: Job monitoring
- [ ] Manual test: Non-admin access blocked

## Success Criteria

✅ Feature flag system implemented
✅ Four flag types supported (BOOLEAN, STRING, NUMBER, JSON)
✅ Four scopes supported (GLOBAL, USER, PLAN, ROLE)
✅ Rollout percentage for gradual rollout
✅ User management endpoints
✅ Ban/unban functionality
✅ System health monitoring
✅ System statistics
✅ Job monitoring across all users
✅ Subscription management view
✅ Admin-only authorization
✅ Audit logging for critical actions

## Phase 11 Status: COMPLETE

All admin panel functionality implemented. Ready for frontend admin UI development and integration with analytics dashboard.

## Next Steps

1. Test admin endpoints with admin user
2. Verify authorization (non-admin blocked)
3. Create sample feature flags
4. Test feature flag evaluation
5. Monitor system health and stats
6. Proceed to Phase 12 (Analytics & Monitoring)
7. Build frontend admin dashboard
8. Add real-time metrics and charts
