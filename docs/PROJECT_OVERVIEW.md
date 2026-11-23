# Project Overview - FarmMate AI

## Purpose

FarmMate AI is an **AI-powered personal farming assistant** designed to help farmers manage their crops, farms, and farming activities more effectively. The application combines traditional farm management features with AI-generated advice, weather integration, and automated scheduling.

## Core Philosophy

- **Practical AI**: AI assistance that addresses real farming problems (crop planning, daily advice, weather impact)
- **Farmer-first**: All features designed with farmer workflows in mind, including support for limited connectivity and varying technical literacy
- **Data-driven**: All farming decisions grounded in crop lifecycle data, soil information, and weather patterns
- **Offline-capable**: Mobile app designed to work with intermittent connectivity

## Problem Solved

Farmers face several challenges:
- Manual tracking of crop cycles, stages, and activities
- Limited access to timely weather information and recommendations
- No centralized record of farming activities and progress
- Difficulty getting AI-powered advice specific to their context
- Complex farm management without dedicated agricultural software

## Key Features

| Category | Features |
|----------|----------|
| **Farm Management** | Create/manage farms, track land area, location, irrigation, and water sources |
| **Crop Lifecycle** | Plan crop seasons, track stages (PLANNED → ACTIVE → HARVESTED/CANCELLED), record activities |
| **AI Assistance** | AI-powered crop planning, daily farming advice, weather-based recommendations |
| **Dashboard** | Central overview with weather, active crops, upcoming activities, AI advisor |
| **Authentication** | Secure registration/login, user profiles, farmer onboarding |
| **Notifications** | Push notifications for AI advice, weather updates, activity reminders |

## Architecture

The system follows a **clean architecture** pattern with separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐ │
│  │  Flutter    │  │  FastAPI    │  │  PostgreSQL        │ │
│  │  Mobile App │  │  Backend    │  │  Database          │ │
│  └─────────────┘  └─────────────┘  └────────────────────┘ │
│           │                  │                      │       │
│           └───── HTTP/API ─────┘                      │       │
│                       └──────────────────────────────┘       │
│                    LAYERED ARCHITECTURE                    │
│  ┌─────────────┐  ┌─────────────────────┐  ┌────────────┐ │
│  │  Routes     │  │  Services/Use Cases │  │  Repositories │ │
│  │  (API)      │  │  (Business Logic)   │  │  (DB Access) │ │
│  └─────────────┘  └─────────────────────┘  └────────────┘ │
│           │                  │                      │       │
│           └───── Dependencies ──────────────────────┘       │
│                 │                                              │
│        ┌─────────────────┐  ┌─────────────────────┐              │
│        │  Shared         │  │  External Services  │              │
│        │  Utilities      │  │  (Weather APIs, FCM)│              │
│        └─────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Mobile** | Flutter, Dart, Provider state management |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy ORM |
| **Database** | PostgreSQL with UUID primary keys |
| **AI/ML** | Rule-based planning (AdvisorPlanner), context-aware advice generation |
| **Scheduling** | APScheduler (cron-based daily jobs) |
| **Notifications** | Firebase Cloud Messaging (FCM) |
| **API** | RESTful with JSON, FastAPI auto-generated docs |
| **Testing** | Pytest, test database fixtures |

## Deployment

- **Development**: `uvicorn app.main:app --reload` on port 8000
- **Production**: Uvicorn with gunicorn, behind reverse proxy (nginx)
- **Container**: Docker with render.yaml configuration
- **Mobile**: Flutter build (iOS, Android, Web, Desktop)

## Current Status

- **Backend**: Fully implemented with 20+ API endpoints
- **Frontend**: Flutter mobile app with core screens implemented
- **Database**: PostgreSQL schema with 9+ core models
- **AI Features**: Crop planning and daily advisor implemented
- **Scheduler**: Daily job runs at 6 AM for weather and advisor updates
- **Notifications**: FCM integration for push notifications

---
*This overview is based on codebase analysis as of 2026-11-21. For the latest status, see COMPLETE_FEATURES.md.*