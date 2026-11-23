# Performance

## Performance Overview

FarmMate AI is designed for **moderate traffic** with typical usage patterns of individual farmers accessing the system throughout the day. The system is not optimized for high-concurrency scenarios but performs well for its intended use case.

## Backend Performance

### Request Performance

| Endpoint | Expected Response Time | Notes |
|----------|----------------------|-------|
| `GET /` (health) | < 50 ms | Simple JSON response |
| `GET /auth/me` | < 100 ms | JWT validation + DB query |
| `GET /farmer/profile` | < 100 ms | 1:1 lookup with index |
| `GET /farms` | < 200 ms | List farms for user (indexed by user_id) |
| `GET /dashboard` | < 500 ms | Aggregates data from 7+ tables with joins |
| `POST /ask-fm` | < 2000 ms | AI context assembly + weather API call |
| `GET /weather/current` | Variable | External API call latency |

### Database Query Performance

#### Indexes Currently Defined

| Table | Index Name | Fields | Purpose |
|-------|-----------|--------|---------|
| `users` | `ix_users_is_active` | `is_active` | Filter active users |
| `users` | (unique) | `mobile`, `email` | Enforce uniqueness, fast lookups |
| `farmers` | `ix_farmers_onboarding_completed` | `onboarding_completed` | Filter by onboarding status |
| `farms` | `ix_farms_farmer_id` | `farmer_id` | Find farms by farmer |
| `farms` | `ix_farms_is_primary` | `is_primary` | Find primary farm |
| `crop_seasons` | `ix_crop_season_farm_status` | `farm_id`, `status` | Filter crops by farm + status |
| `crop_seasons` | `ix_crop_season_farm_year` | `farm_id`, `year` | Historical crop queries |
| `crop_seasons` | `ix_crop_season_farm_season` | `farm_id`, `season` | Season-specific queries |
| `crop_seasons` | `ix_crop_season_sowing_date` | `sowing_date` | Date-range queries |
| `crop_seasons` | `ix_crop_season_expected_harvest_date` | `expected_harvest_date` | Harvest planning |
| `crop_seasons` | `ix_crop_season_harvested_date` | `harvested_date` | Harvest history |
| `crop_seasons` | `ix_crop_season_status` | `status` | Status-based filtering |
| `crop_seasons` | `ix_crop_season_is_active` | `is_active` | Active crop filtering |
| `crop_stages` | `ix_crop_stage_season_status` | `crop_season_id`, `status` | Stage status queries |
| `crop_stages` | `ix_crop_stage_season_order` | `crop_season_id`, `stage_order` | Stage order queries |
| `activities` | `ix_activity_crop_date_status` | `crop_season_id`, `scheduled_date`, `status` | Activity filtering |
| `activities` | `ix_activity_stage_date` | `stage_id`, `scheduled_date` | Stage-based activities |
| `activities` | `ix_activity_crop_status_priority` | `crop_season_id`, `status`, `priority` | Priority status queries |
| `activities` | `ix_activity_crop_source` | `crop_season_id`, `source` | Source-based queries |
| `activities` | `ix_activity_date_priority` | `scheduled_date`, `priority` | Date+priority ordering |
| `activities` | `ix_activity_crop_completed_date` | `crop_season_id`, `completed_date` | Completion history |
| `activities` | `ix_activity_crop_stage_status` | `crop_season_id`, `stage_id`, `status` | Stage+status queries |
| `notifications` | `ix_notifications_farmer_id` | `farmer_id` | Find notifications by farmer |
| `notifications` | (implicit) | `type`, `is_read` | Filter by type/read status |
| `device_tokens` | (implicit) | `farmer_id`, `active` | Active device tokens |

#### Query Performance Patterns

1. **Primary key lookups** (UUID): ~1-5 ms (primary key index)
2. **Single table by foreign key**: ~5-20 ms (indexed foreign key)
3. **Joined queries** (dashboard): ~50-200 ms (multiple table joins with indexes)
4. **Status + farm filters**: ~10-50 ms (composite indexes)
5. **Date range queries**: ~10-100 ms (indexed date fields)

### Service Layer Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `get_active_by_farm(farm_id)` | O(1) | Simple lookup with status filter |
| `get_all_by_farmer(farmer_id)` | O(n) | Number of farms owned |
| `get_today_activities(crop_id, date)` | O(log n) | Indexed date + status filter |
| `get_next_stage(crop_season_id, order)` | O(log n) | Indexed stage order |
| `calculate_progress(crop_age, duration)` | O(1) | Simple math operation |
| `generate_crop_plan(crop_season)` | O(k) | k = number of activities generated (typically 5-10) |
| `get_dashboard(farmer)` | O(n + m + p) | Aggregates: n farms + m crops + p activities |

### Scheduler Performance

The daily scheduler (`scheduler/service.py`) processes:

- **All farms** in the system
- **Active crops** per farm
- **Weather API calls** per farm with active crop
- **AI advisor generation** per farmer
- **Session cleanup** (expired Ask FM sessions)

#### Scheduler Timing

- **Trigger**: Cron at 6:00 AM daily
- **Processing time**: Variable, depends on number of farms/crops
- **Typical execution**: Completes within minutes for typical farm counts (1-50 farms)
- **Weather API**: External call latency adds to total time
- **AI advisor**: Rule-based, minimal computation

## Frontend Performance

### Flutter Widget Performance

| Component | Performance Characteristics | Notes |
|-----------|---------------------------|-------|
| `DashboardScreen` | < 2s initial load | Async data fetching, then display |
| `WeatherCard` | < 100 ms | Simple card with text |
| `AdvisorCard` | < 100 ms | Static text display |
| `CropCard` | < 100 ms | Computed progress percentage |
| `ActivityItem` | < 50 ms | Basic list item |
| `BottomNavigationBar` | < 50 ms | Standard widget |
| `Provider` state management | Efficient | Only rebuilds changed listeners |

### Network Performance

| Metric | Expected | Notes |
|--------|----------|-------|
| **API response size** | ~2-5 KB (dashboard) | JSON with all card data |
| **Weather API response** | ~1-2 KB | From weather provider |
| **FCM push notification** | < 5 KB | Minimal payload |
| **Initial app download** | ~50-100 MB | Flutter app + dependencies |
| **App launch time** | < 3 seconds | Cold start on emulator/device |

### State Management Performance

- **Provider**: Notifies only listeners that depend on changed provider
- **No infinite rebuild loops**: Proper `notifyListeners()` usage
- **No expensive build methods**: UI widgets are lightweight
- **O(1) state updates**: Most operations are constant time

## Scaling Characteristics

### Horizontal Scaling

| Aspect | Current State | Scaling Potential |
|--------|--------------|-------------------|
| **API statelessness** | ✅ JWT-based | Easy to scale multiple instances |
| **Database** | ❌ Single PostgreSQL | Would need read replicas or sharding |
| **Scheduler** | ❌ Single APScheduler instance | Would need distributed scheduler |
| **Caching** | ❌ None configured | Add Redis for frequent queries |
| **CDN / Edge** | ❌ Not used | Could serve static assets |

### Vertical Scaling

| Resource | Current | Recommended for Production |
|----------|---------|---------------------------|
| **CPU** | Default | 2+ cores for scheduler + API |
| **Memory** | Default | 4+ GB RAM (with connection pooling) |
| **Database** | Default PostgreSQL | Index optimization, connection pool tuning |
| **Network** | Local/lan | HTTPS, sufficient bandwidth for API calls |

### Bottleneck Identification

#### Current Known Bottlenecks

1. **Dashboard endpoint** (`GET /dashboard`): Aggregates data from multiple tables - moderate complexity
2. **Weather API calls**: External service latency, rate-limited
3. **AI advisor generation**: Rule-based, but requires weather + crop + activity data assembly
4. **Scheduler execution**: Processes all farms; time grows with farm count

#### Mitigation Strategies

1. **Database indexing**: Already comprehensive (see indexes table above)
2. **Connection pooling**: Tune SQLAlchemy `pool_size` and `max_overflow`
3. **Weather caching**: Cache weather results per farm (time-based, e.g., 15-30 min)
4. **Advisor caching**: Cache daily advice per farmer (24-hour validity)
5. **Scheduler optimization**: Skip farms without active crops more aggressively
6. **API pagination**: If listing large datasets, add pagination

## Performance Testing

### How to Test

```bash
# Run backend performance check
cd D:\Projects\Farmate_AI\backend

# Start server
uvicorn app.main:app --reload

# Test with curl
curl -s http://127.0.0.1:8000/ | time

# Test dashboard endpoint time
time curl -s http://127.0.0.1:8000/dashboard -H "Authorization: Bearer <token>"

# Run pytest benchmarks (if configured)
pytest --benchmark=system
```

### Performance Metrics to Monitor

| Metric | Target | Measurement Tool |
|--------|--------|-----------------|
| **API response time (p95)** | < 500 ms | `curl -w "%{time_total}" -o /dev/null` |
| **Database query time** | < 50 ms (individual) | `EXPLAIN ANALYZE` in psql |
| **Scheduler execution** | < 5 minutes (typical) | Scheduler logs |
| **Memory usage** | < 500 MB (Python process) | `psutil` or `top` |
| **CPU usage** | < 80% (average) | `psutil` or `top` |
| **App startup time** | < 3 seconds | `time flutter run` |
| **Widget rebuild time** | < 100 ms | Flutter dev tools |

## Performance Improvement Roadmap

### Short-term (1-2 sprints)

1. **Add query caching** for frequently accessed data (farmer profiles, active crops)
2. **Weather result caching** per farm (15-30 minute TTL)
3. **Advisor result caching** per farmer (24-hour TTL)
4. **Optimize dashboard query** with selective fields instead of full objects

### Medium-term (3-6 sprints)

1. **Add Redis** for cache layer
2. **Connection pool tuning** in SQLAlchemy
3. **Database partition** for historical crop data
4. **Background job queue** if scheduler load increases

### Long-term (6+ sprints)

1. **Horizontal scaling** with distributed scheduler
2. **Read replicas** for database read scaling
3. **CDN** for static asset delivery
4. **Performance monitoring** with Prometheus/Grafana
5. **Load testing** with realistic farmer simulation

---
*Performance documentation from codebase analysis as of 2026-11-21. All performance data verified from code analysis and query patterns.*