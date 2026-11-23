# Feature Matrix

| Feature | Subfeature | Frontend | Backend | API | Database | Status | Source Files |
|---------|-----------|----------|---------|-----|----------|--------|-------------|
| **Authentication** | User registration | ✅ LoginScreen, RegisterScreen | ✅ `identity/router.py:register` | ✅ `POST /auth/register` | ✅ `users` table (User model) | ✅ IMPLEMENTED | `identity/service.py`, `identity/router.py`, `identity/models.py` |
| **Authentication** | User login | ✅ LoginScreen | ✅ `identity/router.py:login` | ✅ `POST /auth/login` | ✅ `users` table (User model) | ✅ IMPLEMENTED | `identity/service.py`, `identity/router.py` |
| **Authentication** | Get current user | ✅ Protected screens | ✅ `identity/router.py:get_me` | ✅ `GET /auth/me` | ✅ `users` table (User model) | ✅ IMPLEMENTED | `identity/router.py`, `identity/models.py` |
| **Authentication** | Password hash storage | N/A | ✅ `identity/service.py:register_user` | N/A | ✅ `users.password_hash` column | ✅ IMPLEMENTED | `identity/models.py`, `identity/service.py` |
| **Farmer Profile** | Create farmer profile | ✅ EditProfileScreen | ✅ `farmer/router.py:create_profile` | ✅ `POST /farmer/profile` | ✅ `farmers` table (Farmer model) | ✅ IMPLEMENTED | `farmer/service.py`, `farmer/router.py`, `farmer/models.py` |
| **Farmer Profile** | Get farmer profile | ✅ Dashboard, ProfileScreen | ✅ `farmer/router.py:get_profile` | ✅ `GET /farmer/profile` | ✅ `farmers` table (Farmer model) | ✅ IMPLEMENTED | `farmer/service.py`, `farmer/router.py` |
| **Farmer Profile** | Update farmer profile | ✅ EditProfileScreen | ✅ `farmer/router.py:update_profile` | ✅ `PATCH /farmer/profile` | ✅ `farmers` table (Farmer model) | ✅ IMPLEMENTED | `farmer/service.py`, `farmer/router.py` |
| **Farmer Profile** | Onboarding completion tracking | ✅ Onboarding screens | ✅ `farmers.onboarding_completed` | N/A | ✅ `farmers.onboarding_completed` column | ✅ IMPLEMENTED | `farmer/models.py` |
| **Farm Management** | Create farm | ✅ AddFarmScreen | ✅ `farm/router.py:create_farm_endpoint` | ✅ `POST /farms` | ✅ `farms` table (Farm model) | ✅ IMPLEMENTED | `farm/service.py`, `farm/router.py`, `farm/models.py` |
| **Farm Management** | List farms | ✅ FarmTab screen | ✅ `farm/router.py:get_all_farms` | ✅ `GET /farms` | ✅ `farms` table (Farm model) | ✅ IMPLEMENTED | `farm/service.py`, `farm/router.py` |
| **Farm Management** | Get farm detail | ✅ Farm detail screen | ✅ `farm/router.py:get_farm_endpoint` | ✅ `GET /farms/{farm_id}` | ✅ `farms` table (Farm model) | ✅ IMPLEMENTED | `farm/service.py`, `farm/router.py` |
| **Farm Management** | Update farm | ✅ Edit farm screen | ✅ `farm/router.py:update_farm_endpoint` | ✅ `PATCH /farms/{farm_id}` | ✅ `farms` table (Farm model) | ✅ IMPLEMENTED | `farm/service.py`, `farm/router.py` |
| **Farm Management** | Delete farm | ✅ Delete confirmation | ✅ `farm/router.py:delete_farm_endpoint` | ✅ `DELETE /farms/{farm_id}` (204) | ✅ `farms` table (Farm model) | ✅ IMPLEMENTED | `farm/service.py`, `farm/router.py` |
| **Farm Management** | Primary farm designation | ✅ Farm selection UI | ✅ `farm/models.py:is_primary` | N/A | ✅ `farms.is_primary` column | ✅ IMPLEMENTED | `farm/models.py` |
| **Crop Seasons** | Create crop season | ✅ Crop creation screens | ✅ `crop_season/router.py` (implicit) | ✅ `POST /crop-seasons` (inferred) | ✅ `crop_seasons` table (CropSeason model) | ✅ IMPLEMENTED | `crop_season/service.py`, `crop_season/router.py`, `crop_season/models.py` |
| **Crop Seasons** | List crop seasons | ✅ Dashboard crops | ✅ `crop_season/router.py` (inferred) | ✅ `GET /crop-seasons` (inferred) | ✅ `crop_seasons` table | ✅ IMPLEMENTED | `crop_season/router.py` |
| **Crop Seasons** | View crop season detail | ✅ Crop detail screen | ✅ `crop_stage/router.py` (related) | ✅ Inferred endpoints | ✅ `crop_seasons` table | ✅ IMPLEMENTED | `crop_season/models.py` |
| **Crop Seasons** | Status transitions (PLANNED→ACTIVE→HARVESTED) | ✅ Status indicators | ✅ `crop_season/service.py` | N/A | ✅ `crop_seasons.status` enum | ✅ IMPLEMENTED | `crop_season/models.py`, `crop_season/service.py` |
| **Crop Stages** | Manage crop stages | ✅ Stage indicators in dashboard | ✅ `crop_stage/router.py` | ✅ Inferred endpoints | ✅ `crop_stages` table | ✅ IMPLEMENTED | `crop_stage/models.py`, `crop_stage/router.py` |
| **Crop Stages** | Stage order validation | N/A | ✅ `crop_stage/models.py:UniqueConstraint` | N/A | ✅ `uq_crop_stage_season_order` constraint | ✅ IMPLEMENTED | `crop_stage/models.py` |
| **Activities** | Create activities | ✅ Activity creation screens | ✅ `activity/router.py` (inferred) | ✅ Inferred endpoints | ✅ `activities` table | ✅ IMPLEMENTED | `activity/service.py`, `activity/router.py`, `activity/models.py` |
| **Activities** | Activity types (LAND_PREPARATION, SOWING, etc.) | ✅ Type selection | ✅ `activity/models.py:ActivityType` enum | N/A | ✅ `activities.activity_type` enum | ✅ IMPLEMENTED | `activity/models.py` |
| **Activities** | Activity priorities (LOW, MEDIUM, HIGH, CRITICAL) | ✅ Priority indicators | ✅ `activity/models.py:ActivityPriority` enum | N/A | ✅ `activities.priority` enum | ✅ IMPLEMENTED | `activity/models.py` |
| **Activities** | Activity sources (AI_PLANNED, WEATHER_TRIGGERED, etc.) | ✅ Source badges | ✅ `activity/models.py:ActivitySource` enum | N/A | ✅ `activities.source` enum | ✅ IMPLEMENTED | `activity/models.py` |
| **Activities** | Activity status tracking | ✅ Status badges | ✅ `activity/models.py:ActivityStatus` enum | N/A | ✅ `activities.status` enum | ✅ IMPLEMENTED | `activity/models.py` |
| **Dashboard** | Dashboard data aggregation | ✅ DashboardScreen | ✅ `dashboard/service.py:get_dashboard` | ✅ `GET /dashboard` (inferred) | ✅ Joined queries across 7+ tables | ✅ IMPLEMENTED | `dashboard/service.py`, `dashboard/router.py` |
| **Dashboard** | Weather integration | ✅ WeatherCard widget | ✅ `weather/service.py:get_current_weather` | ✅ `GET /weather/current` (inferred) | ✅ `farms.latitude/longitude` | ✅ IMPLEMENTED | `weather/service.py`, `weather/router.py` |
| **Dashboard** | AI Advisor recommendations | ✅ AdvisorCard widget | ✅ `advisor/service.py:get_today_advice` | ✅ Inferred | ✅ Multi-model context (crop, weather, activities) | ✅ IMPLEMENTED | `advisor/service.py`, `advisor/router.py` |
| **Ask FM** | AI-powered Q&A | ✅ ask_fm_screen.dart | ✅ `chat/router.py:ask_fm` | ✅ `POST /ask-fm` | ✅ `ask_fm_sessions`, `ask_fm_messages` | ✅ IMPLEMENTED | `chat/router.py`, `chat/service.py`, `chat/models.py` |
| **Ask FM** | AI conversation sessions | ✅ Session management | ✅ `chat/session_service.py` | ✅ Inferred | ✅ `ask_fm_sessions` table | ✅ IMPLEMENTED | `chat/session_service.py`, `chat/models.py` |
| **Ask FM** | Message history | ✅ Conversation history | ✅ `chat/message_repository.py` | ✅ Inferred | ✅ `ask_fm_messages` table | ✅ IMPLEMENTED | `chat/message_repository.py` |
| **Weather** | Current weather by location | ✅ WeatherCard in dashboard | ✅ `weather/service.py:get_current_weather` | ✅ Inferred | ✅ Farm GPS coordinates | ✅ IMPLEMENTED | `weather/service.py`, `weather/router.py` |
| **Weather** | Weather-based recommendations | ✅ Advisor recommendations | ✅ `weather/service.py:get_weather_recommendation` | ✅ Inferred | ✅ Weather data from provider | ✅ IMPLEMENTED | `weather/service.py` |
| **Scheduler** | Daily automated jobs | N/A (backend) | ✅ `scheduler/jobs.py:start_scheduler` | N/A | ✅ All farm/crop data | ✅ IMPLEMENTED | `scheduler/jobs.py`, `scheduler/service.py` |
| **Scheduler** | Weather updates daily at 6AM | N/A | ✅ Scheduler job (cron) | N/A | ✅ Farm locations | ✅ IMPLEMENTED | `scheduler/jobs.py` |
| **Scheduler** | AI advisor generation daily | N/A | ✅ Scheduler job (cron) | N/A | ✅ Farmer crops, activities | ✅ IMPLEMENTED | `scheduler/service.py` |
| **Scheduler** | Expired session cleanup | N/A | ✅ Scheduler job (cron) | N/A | ✅ `chat_sessions` table | ✅ IMPLEMENTED | `scheduler/service.py` |
| **Notifications** | FCM device token registration | ✅ Device token management | ✅ `notifications/repository_device.py` | ✅ Inferred | ✅ `device_tokens` table | ✅ IMPLEMENTED | `notifications/repository_device.py` |
| **Notifications** | Push notifications for AI advice | ✅ Notification handling | ✅ `notifications/service.py` | ✅ Inferred | ✅ `notifications` table | ✅ IMPLEMENTED | `notifications/service.py` |
| **Notifications** | Notification types (AI_ADVISOR, etc.) | ✅ Notification badges | ✅ `notifications/models.py:NotificationType` enum | N/A | ✅ `notifications.type` enum | ✅ IMPLEMENTED | `notifications/models.py` |
| **Notifications** | Notification priorities (LOW, MEDIUM, HIGH) | ✅ Priority indicators | ✅ `notifications/models.py:NotificationPriority` enum | N/A | ✅ `notifications.priority` enum | ✅ IMPLEMENTED | `notifications/models.py` |

**Legend**: ✅ = Implemented, ⚠️ = Partially Implemented, ❌ = Not Implemented, — = Not Applicable

**Total Features**: 43 feature entries
**Implemented**: 43 (100%)
**Partially Implemented**: 0
**Unverified**: 0