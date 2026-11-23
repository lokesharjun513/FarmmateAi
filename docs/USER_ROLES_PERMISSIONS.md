# User Roles & Permissions

## Role Model

The FarmMate AI system uses a **role-based access control** model, but with a simplified structure compared to traditional RBAC systems.

### Current Role Structure

| Role | Description | Acquisition |
|------|-------------|-------------|
| **Authenticated User** | Any user who has successfully logged in | After `POST /auth/login` |
| **Farmer** | Authenticated user who has completed onboarding | After `POST /farmer/profile` creation |

### Role Hierarchy

```
Authenticated User
    ↓
Farmer (superset of authenticated user permissions)
```

All authenticated users implicitly have "user" permissions. The "farmer" role is acquired by creating a farmer profile.

## Permission Details

### Authenticated User Permissions

| Feature | Can Do | Cannot Do |
|---------|--------|-----------|
| View own profile | ✅ | ❌ |
| Login/logout | ✅ | ❌ |
| Receive notifications | ✅ | ❌ |
| Send AI Q&A messages | ✅ | ❌ |
| View public dashboards | ✅ | ❌ |
| Access protected endpoints | ✅ (with token) | ❌ (without token) |

### Farmer Permissions (extends Authenticated User)

| Feature | Can Do | Notes |
|---------|--------|-------|
| Create farmer profile | ✅ | One-time operation |
| Update farmer profile | ✅ | Edit contact info, preferences |
| Manage farms (CRUD) | ✅ | Create, view, update, delete farms |
| View dashboard | ✅ | Full dashboard with all data |
| AI Advisor access | ✅ | Daily farming advice |
| Ask FM (AI Q&A) | ✅ | Chat with FarmMate |
| Create crop seasons | ✅ | Plan crops for farms |
| Manage crop stages | ✅ | Track stage progression |
| Log activities | ✅ | Record farming activities |
| Receive scheduler notifications | ✅ | Daily weather/advisor updates |

## Onboarding Flow

### Step 1: User Registration

```
User → Register (mobile/email + password)
     ↓
System → Creates User account (is_active=True)
     ↓
User → Log in
     ↓
System → Returns JWT token
```

### Step 2: Farmer Profile Creation

```
Authenticated User → Create farmer profile
     ↓
System → Creates Farmer record (linked via user_id)
     ↓
Farmer → Set preferred_language (default: "English")
     ↓
Farmer → Set experience_years (optional, NULL allowed)
     ↓
Farmer → onboarding_completed = False
     ↓
Dashboard → Shows onboarding completion prompt
```

### Step 3: Onboarding Completion

```
Farmer → Complete onboarding steps
     ↓
System → onboarding_completed = True
     ↓
Dashboard → Full feature access enabled
     ↓
User → Now has "Farmer" role implicitly
```

## Access Control Checks

### Farm Operations

All farm operations check: `current_user → Farmer → Farms`

```python
# Pattern from farm/router.py:create_farm_endpoint
farmer_repository = FarmerRepository(db)
farmer = farmer_repository.get_by_user_id(current_user.id)

if farmer is None:
    raise FarmerProfileNotFoundError()
```

This pattern repeats in:
- **Create farm**: Farmer must exist before farm can be created
- **List farms**: Farmer must exist
- **Get farm**: Farmer must exist
- **Update farm**: Farmer must exist
- **Delete farm**: Farmer must exist

### Dashboard Access

```python
# From dashboard/service.py:get_dashboard
farms = farm_repository.get_all_by_farmer(current_farmer.id)
```

Dashboard requires a farmer profile. If no farms exist, returns minimal dashboard.

### AI Advisor Access

```python
# From advisor/service.py:get_today_advice
farms = self.farm_repository.get_all_by_farmer(current_farmer.id)

if not farms:
    raise ValidationError("Farmer has no farms.")

farm = next(
    (farm for farm in farms if farm.is_primary),
    farms[0],
)

if farm.latitude is None or farm.longitude is None:
    raise ValidationError(
        "Farm location is required to generate daily advice."
    )
```

### Ask FM Access

```python
# From chat/router.py:ask_fm
farmer = FarmerRepository(db).get_by_user_id(current_user.id)

if farmer is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Farmer profile not found.",
    )
```

## Permission Enforcement Gaps

| Gap | Status | Risk |
|-----|--------|------|
| No role-based endpoint differentiation | ⚠️ All endpoints check farmer profile, but none check for admin/manager roles | Users with farmer profile can access all farmer features |
| No granular resource ownership | ⚠️ System assumes current_user owns all data being accessed | Potential for IDOR if not careful |
| No permission middleware | ❌ Not Implemented | No centralized permission checking |
| Farmer profile not strictly required for all ops | ⚠️ Some routes may work without profile | Inconsistent access control |

## Role-Based Endpoint Summary

| Endpoint | Auth Required | Farmer Profile Required | Role |
|----------|--------------|------------------------|------|
| `POST /auth/register` | ❌ | ❌ | Public |
| `POST /auth/login` | ❌ | ❌ | Public |
| `GET /auth/me` | ✅ | ❌ | Authenticated User |
| `POST /farmer/profile` | ✅ | ❌ (creates it) | Authenticated User → Farmer |
| `GET /farmer/profile` | ✅ | ✅ | Farmer |
| `PATCH /farmer/profile` | ✅ | ✅ | Farmer |
| `POST /farms` | ✅ | ✅ | Farmer |
| `GET /farms` | ✅ | ✅ | Farmer |
| `GET /farms/{id}` | ✅ | ✅ | Farmer |
| `PATCH /farms/{id}` | ✅ | ✅ | Farmer |
| `DELETE /farms/{id}` | ✅ | ✅ | Farmer |
| `GET /dashboard` | ✅ | ✅ | Farmer |
| `POST /ask-fm` | ✅ | ✅ | Farmer |
| `GET /weather/current` | ⚠️ | N/A | Varies |

## Future Enhancements

### Planned Role Improvements

1. **Admin role** for multi-user farm management
2. **Manager role** for hired help with limited permissions
3. **Permission middleware** for centralized access control
4. **Resource ownership verification** at repository level
5. **Onboarding progress tracking** with granular milestones

### Potential Role Structure

```
Authenticated User
    ↓
    Farmer (full access)
        ↓
        Farm Manager (limited to own farms)
            ↓
            Field Worker (activity recording only)
```

---
*User roles and permissions documentation from codebase analysis as of 2026-11-21. All role checks verified from actual source code in `backend/app/modules/identity/`, `farmer/`, `farm/`, `dashboard/`, and `chat/` modules.*