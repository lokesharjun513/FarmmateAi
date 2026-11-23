# Architecture

## High-Level Architecture

FarmMate AI follows a **layered client-server architecture** with a clear separation between the Flutter mobile frontend and the Python FastAPI backend.

```mermaid
graph TD
    subgraph Client ["Flutter Mobile App"]
        direction TB
        UI[UI Widgets & Screens]
        Provider[State Management]
        Navigator[Navigation/Routing]
    end

    subgraph Server ["FastAPI Backend"]
        direction TB
        Main[main.py - App Entry Point]
        Router[API Router (v1)]
        Modules[Module Routers]
        Services[Business Services]
        Repositories[Data Repositories]
        Models[SQLAlchemy Models]
        DB[(PostgreSQL)]
    end

    subgraph External ["External Services"]
        WeatherAPI[Weather Provider API]
        FCM[Firebase Cloud Messaging]
    end

    %% Connections
    UI -->|HTTP Requests| Router
    Router -->|Module Routing| Modules
    Modules -->|Service Calls| Services
    Services -->|Repository Calls| Repositories
    Repositories -->|SQLAlchemy ORM| Models
    Models -->|CRUD Operations| DB
    Services -->|API Calls| WeatherAPI
    Services -->|FCM Calls| FCM
    UI -->|Push Notifications| FCM
```

## Component Interactions

```mermaid
sequenceDiagram
    participant F as Flutter Frontend
    participant A as API Gateway
    participant R as API Router
    participant S as Services
    participant DB as Database
    participant W as Weather Service

    F->>A: HTTP Request (e.g., GET /dashboard)
    A->>R: Route to appropriate module
    R->>S: Call business service
    S->>DB: Query/Update data
    DB-->>S: Return data
    S->>W: Get weather data (if needed)
    W-->>S: Weather response
    S-->>R: Return API response
    R-->>A: JSON response
    A-->>F: Display data
```

## Request-Response Lifecycle

```mermaid
flowchart TD
    subgraph Request Life Cycle
        A[Client Request] -->|HTTP Method & Path| B{Route Matching}
        B -->|Auth Endpoints| C[Identity Module]
        B -->|Farm Endpoints| D[Farm Module]
        B -->|Crop Endpoints| E[Crop Season Module]
        B -->|Dashboard| F[Dashboard Module]
        B -->|AI Chat| G[Chat Module]
        B -->|Scheduler| H[Scheduler Job]
        
        C -->|Validate Input| I[Service Layer]
        D -->|Validate Input| I
        E -->|Validate Input| I
        F -->|Validate Input| I
        G -->|Validate Input| I
        
        I -->|DB Operations| J[Repository Layer]
        J -->|SQLAlchemy ORM| K[Database]
        K -->|Return Data| I
        I -->|Transform Data| L[Schema Validation]
        L -->|JSON Response| M[API Response]
        M -->|HTTP Response| A
    end
```

## Data Flow

```mermaid
graph LR
    subgraph Data Flow
        direction TB
        
        Farmer["Farmer Data"] -->|User ID| User["User Auth"]
        User -->|1:1 Relation| FarmerProfile["Farmer Profile"]
        FarmerProfile -->|Owns| Farms["Farms Table"]
        Farms -->|1:N| CropSeasons["Crop Seasons"]
        CropSeasons -->|1:N| CropStages["Crop Stages"]
        CropSeasons -->|1:N| Activities["Activities"]
        
        Farms -->|GPS Coords| WeatherService["Weather Service"]
        WeatherService -->|Current Conditions| Dashboard["Dashboard"]
        Dashboard -->|AI Context| AIEngine["AI Engine"]
        AIEngine -->|Advice| Advisor["Advisor Service"]
        Advisor -->|Notifications| NotificationService["Notification Service"]
        NotificationService -->|FCM| Mobile["Mobile App"]
    end
```

## Authentication Flow

```mermaid
stateDiagram-v2
    [*] --> Registered: User registers
    Registered --> LoggedIn: User logs in
    LoggedIn --> Authenticated: JWT Token validated
    Authenticated --> Disabled: Account deactivated
    Disabled --> [*]: Login rejected
    
    state "Authenticated Session" as AuthSession {
        [*] --> |JWT Access Token| TokenStore
        TokenStore -->|Token sent with each request| ProtectedEndpoints
        ProtectedEndpoints -->|get_current_user() dependency| UserInfo
        UserInfo -->|Farmer profile access| FarmerData
    }
    
    note right of TokenStore: 
        - HttpOnly cookie or Authorization header
        - Expires in 15 minutes
        - Refresh via re-authentication
    note right of Authenticated: 
        - get_current_user() checks is_active
        - Farmer profile required for most operations
        - Token invalidated on logout
end note
```

## Module Structure

The backend is organized into **independent modules**, each with its own:

- Router (API endpoints)
- Service (business logic)
- Repository (database access)
- Models (SQLAlchemy models)
- Schemas (Pydantic validation)
- Tests

```mermaid
graph TB
    subgraph Modules
        direction TB
        Identity["identity/ - Auth"] 
        Farmer["farmer/ - Farmer profiles"]
        Farm["farm/ - Farm management"]
        CropSeason["crop_season/ - Crop lifecycle"]
        CropStage["crop_stage/ - Crop stages"]
        Activity["activity/ - Farm activities"]
        Dashboard["dashboard/ - Dashboard data"]
        Chat["chat/ - AI Q&A (Ask FM)"]
        Weather["weather/ - Weather integration"]
        AIEngine["ai_engine/ - AI planning"]
        Scheduler["scheduler/ - Background jobs"]
        Notifications["notifications/ - Push notifications"]
    end
    
    Identity -->|includes| MainApp
    Farmer -->|includes| MainApp
    Farm -->|includes| MainApp
    CropSeason -->|includes| MainApp
    CropStage -->|includes| MainApp
    Activity -->|includes| MainApp
    Dashboard -->|includes| MainApp
    Chat -->|includes| MainApp
    Weather -->|includes| MainApp
    AIEngine -->|includes| MainApp
    Scheduler -->|includes| MainApp
    Notifications -->|includes| MainApp
```

## Technology Stack Diagram

```mermaid
graph TB
    subgraph Frontend ["Frontend Layer"]
        direction TB
        Flutter["Flutter (Dart)"]
        Provider["Provider State Mgmt"]
        HTTP["HTTP Client"]
        SharedWidgets["Shared Widgets"]
    end
    
    subgraph Backend ["Backend Layer"]
        direction TB
        FastAPI["FastAPI (Python)"]
        SQLAlchemy["SQLAlchemy ORM"]
        Pydantic["Pydantic Schemas"]
        JWT["JWT Authentication"]
    end
    
    subgraph Database ["Database Layer"]
        direction TB
        PostgreSQL["PostgreSQL"]
        UUIDs["UUID Primary Keys"]
        JSONB["JSONB Columns"]
        Enums["SQL Enums"]
    end
    
    subgraph External ["External Services"]
        direction TB
        WeatherAPI["Weather Provider API"]
        FCM["Firebase Cloud Messaging"]
        OpenAI["OpenAI (optional)"]
    end
    
    Flutter -->|HTTP/JSON| FastAPI
    FastAPI -->|SQL/ORM| PostgreSQL
    FastAPI -->|REST API| WeatherAPI
    FastAPI -->|FCM| FCM
    Provider -->|State Changes| SharedWidgets
```

## Dependencies Diagram

```mermaid
graph TD
    main[main.py] -->|includes| api_router
    api_router -->|includes| identity_router
    api_router -->|includes| farmer_router
    api_router -->|includes| farm_router
    api_router -->|includes| crop_season_router
    api_router -->|includes| crop_stage_router
    api_router -->|includes| activity_router
    api_router -->|includes| dashboard_router
    api_router -->|includes| weather_router
    api_router -->|includes| chat_router
    api_router -->|includes| notifications_router
    api_router -->|includes| crop_recommendation_router
    api_router -->|includes| farming_router
    api_router -->|includes| scheduler_router
    
    main -->|lifespan| scheduler[start_scheduler]
    main -->|middleware| RequestLoggingMiddleware
    main -->|error handling| register_exception_handlers
    
    style main fill:#f9f,stroke:#333,stroke-width:2px
    style api_router fill:#bbf,stroke:#333,stroke-width:1px
    style modules fill:#ccf,stroke:#333,stroke-width:1px
```