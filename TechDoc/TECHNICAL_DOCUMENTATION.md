# ShelfScanner - Technical Documentation

**Version:** 1.0.0  
**Last Updated:** January 2024  
**Document Owner:** Tendong Brain
**Status:** MVP Production Ready

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Database Schema](#2-database-schema)
3. [API Specifications](#3-api-specifications)
4. [Integration Requirements](#4-integration-requirements)
5. [Data Synchronization](#5-data-synchronization)
6. [Security and Compliance](#6-security-and-compliance)
7. [Performance Requirements](#7-performance-requirements)
8. [Monitoring and Logging](#8-monitoring-and-logging)
9. [Testing Requirements](#9-testing-requirements)
10. [Deployment and CI/CD](#10-deployment-and-cicd)
11. [Edge Cases and Error Handling](#11-edge-cases-and-error-handling)
12. [Future Considerations](#12-future-considerations)
13. [Appendix](#appendix)

---

# 1. System Architecture

## 1.1 Application Overview

**ShelfScanner** is an AI-powered book scanning and management platform that enables users to:

- Digitize physical book collections through image scanning
- Automatically extract book information using OCR technology
- Organize and manage personal libraries
- Receive AI-powered book recommendations based on reading history

### Key Capabilities

| Feature | Description | Technology |
|---------|-------------|------------|

| **Image Scanning** | Upload book cover/spine images | FastAPI, Tesseract OCR |
| **Text Extraction** | OCR processing with 95%+ accuracy | Python-tesseract, OpenCV |
| **Book Lookup** | Automatic metadata retrieval | Google Books API, OpenLibrary |
| **Library Management** | CRUD operations for book collections | Supabase PostgreSQL |
| **AI Recommendations** | Semantic similarity and GPT-powered suggestions | OpenAI Embeddings, Qdrant |
| **User Authentication** | Secure JWT-based auth | Supabase Auth, JWT |

### Target Users

- Book collectors and enthusiasts
- Personal library managers
- Reading clubs and communities
- Academic researchers

### Business Metrics

- **User Onboarding Time:** < 2 minutes
- **Scan Success Rate:** > 90%
- **Recommendation Accuracy:** > 80% user satisfaction
- **System Uptime:** 99.9% SLA

## 1.2 Technology Stack

### Backend Framework

```yaml
Primary Framework: FastAPI 0.109.0
Language: Python 3.11+
ASGI Server: Uvicorn with Gunicorn workers
API Documentation: OpenAPI 3.0 (Swagger/ReDoc)
Validation: Pydantic 2.5+
```

### Frontend (Future - Not in MVP)

```yaml
Framework: React 18+ / Next.js 14
State Management: Redux Toolkit / Zustand
UI Library: Tailwind CSS + shadcn/ui
API Client: TanStack Query (React Query)
```

### Infrastructure

#### Databases

```yaml
Primary Database:
  Service: Supabase (PostgreSQL 15)
  Purpose: User data, books, scans
  Hosting: Supabase Cloud / Self-hosted
  
Vector Database:
  Service: Qdrant
  Purpose: Book embeddings for recommendations
  Hosting: Qdrant Cloud / Docker
  
Cache Layer:
  Service: Redis 7
  Purpose: API responses, session data
  Hosting: Redis Cloud / Self-hosted
```

#### Compute & Storage

```yaml
Application Hosting:
  Platform: Docker containers
  Orchestration: Docker Compose (MVP) / Kubernetes (Production)
  
File Storage:
  Service: Supabase Storage
  Purpose: Book cover images, scan uploads
  CDN: Cloudflare (optional)
  
Background Jobs:
  Queue: Celery with Redis broker
  Worker: Celery workers
  Monitoring: Flower
```

#### Monitoring & Observability

```yaml
Metrics: Prometheus + Grafana
Logging: Structlog (JSON format)
APM: New Relic / Datadog (optional)
Error Tracking: Sentry (optional)
Uptime Monitoring: UptimeRobot / Pingdom
```

### Third-Party Integrations

#### AI & Machine Learning

```yaml
OpenAI:
  Services: GPT-4, text-embedding-3-small
  Purpose: Recommendations, embeddings
  Cost: Pay-per-use (~$10-50/month MVP)
  
Tesseract OCR:
  Service: Open-source OCR engine
  Purpose: Text extraction from images
  Cost: Free (self-hosted)
```

#### External APIs

```yaml
Google Books API:
  Purpose: Book metadata lookup
  Rate Limit: 1000 requests/day (free)
  Fallback: OpenLibrary API
  
OpenLibrary API:
  Purpose: Book metadata (alternative)
  Rate Limit: None specified
  Cost: Free
  
Goodreads API:
  Status: Deprecated (no new keys)
  Alternative: Web scraping (not implemented)
```

#### Authentication & Database

```yaml
Supabase:
  Services: Auth, PostgreSQL, Storage
  Purpose: User management, data storage
  Pricing: Free tier (50K MAU) / $25/month Pro
  
Supabase Auth:
  Providers: Email/Password, OAuth (future)
  JWT: HS256 algorithm
  Session: Access token (30min) + Refresh token (7 days)
```

#### Development & DevOps

```yaml
Version Control: Git + GitHub
CI/CD: GitHub Actions / GitLab CI
Container Registry: Docker Hub / GitHub Container Registry
Secret Management: Environment variables / Vault (production)
```

## 1.3 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Web Browser  │  │ Mobile App   │  │ API Clients  │                  │
│  │  (Future)    │  │  (Future)    │  │   (cURL)     │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                  │                  │                          │
│         └──────────────────┴──────────────────┘                          │
│                            │                                             │
│                   HTTPS (TLS 1.3)                                       │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────┐
│                    API GATEWAY / LOAD BALANCER                          │
│                    (Nginx / Cloudflare)                                 │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────┐
│                      APPLICATION LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │             FastAPI Application (Uvicorn)                 │          │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │          │
│  │  │   Auth     │  │   Scan     │  │   Books    │         │          │
│  │  │ Endpoints  │  │ Endpoints  │  │ Endpoints  │         │          │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘         │          │
│  │        │               │               │                 │          │
│  │  ┌─────┴───────────────┴───────────────┴──────┐         │          │
│  │  │          Middleware Layer                   │         │          │
│  │  │  • Rate Limiting (SlowAPI)                  │         │          │
│  │  │  • Authentication (JWT)                     │         │          │
│  │  │  • Logging (Structlog)                      │         │          │
│  │  │  • CORS                                     │         │          │
│  │  │  • Error Handling                           │         │          │
│  │  └─────────────────┬───────────────────────────┘         │          │
│  │                    │                                      │          │
│  │  ┌─────────────────┴───────────────────────────┐         │          │
│  │  │          Service Layer                       │         │          │
│  │  │  • OCR Service                               │         │          │
│  │  │  • Book Lookup Service                       │         │          │
│  │  │  • Embedding Service                         │         │          │
│  │  │  • Recommendation Engine                     │         │          │
│  │  └─────────────────┬───────────────────────────┘         │          │
│  └──────────────────────────────────────────────────────────┘          │
└────────────────────────┼────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
│              │ │             │ │            │
│   CACHE      │ │  DATABASE   │ │  STORAGE   │
│   LAYER      │ │   LAYER     │ │   LAYER    │
│              │ │             │ │            │
│ ┌──────────┐ │ │┌──────────┐ │ │┌─────────┐│
│ │  Redis   │ │ ││Supabase  │ │ ││Supabase ││
│ │  Cache   │ │ ││PostgreSQL│ │ ││ Storage ││
│ └──────────┘ │ │└──────────┘ │ │└─────────┘│
│              │ │             │ │           ││
│              │ │┌──────────┐ │ │           ││
│              │ ││  Qdrant  │ │ │           ││
│              │ ││  Vector  │ │ │           ││
│              │ ││    DB    │ │ │           ││
│              │ │└──────────┘ │ │           ││
└──────────────┘ └─────────────┘ └───────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────────────┐
│                 BACKGROUND PROCESSING                                   │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │              Celery Workers                               │          │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │          │
│  │  │OCR Worker  │  │Embedding   │  │Email       │         │          │
│  │  │            │  │Worker      │  │Worker      │         │          │
│  │  └────────────┘  └────────────┘  └────────────┘         │          │
│  └──────────────────────────────────────────────────────────┘          │
│                           │                                             │
│                  ┌────────▼────────┐                                    │
│                  │  Redis Queue    │                                    │
│                  │  (Broker)       │                                    │
│                  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────────────┐
│               EXTERNAL SERVICES                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ OpenAI   │  │ Google   │  │OpenLibr. │  │Supabase  │              │
│  │ API      │  │ Books    │  │ API      │  │  Auth    │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────────────┐
│                 MONITORING & LOGGING                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Prometheus│  │ Grafana  │  │  Sentry  │  │  Flower  │              │
│  │(Metrics) │  │(Dashbrd) │  │ (Errors) │  │ (Celery) │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Scan & OCR Process

```
┌──────────┐     1. Upload      ┌──────────────┐
│  Client  │─────────────────────▶│ API Gateway  │
└──────────┘                      └──────┬───────┘
                                         │ 2. Validate & Auth
                                         ▼
                                  ┌──────────────┐
                                  │ Scan API     │
                                  │ Endpoint     │
                                  └──────┬───────┘
                                         │ 3. Store Image
                                         ▼
                                  ┌──────────────┐
                                  │ Supabase     │
                                  │ Storage      │
                                  └──────┬───────┘
                                         │ 4. Queue Job
                                         ▼
                                  ┌──────────────┐
                                  │ Redis Queue  │
                                  └──────┬───────┘
                                         │ 5. Process
                                         ▼
                         ┌────────────────────────────┐
                         │ Celery Worker (OCR)        │
                         │  • Preprocess image        │
                         │  • Extract text (Tesseract)│
                         │  • Parse titles/ISBNs      │
                         └───────────┬────────────────┘
                                     │ 6. Lookup
                         ┌───────────┴────────────┐
                         ▼                        ▼
                  ┌──────────────┐        ┌──────────────┐
                  │ Google Books │        │ OpenLibrary  │
                  │     API      │        │     API      │
                  └──────┬───────┘        └──────┬───────┘
                         │ 7. Return           │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────┐
                         │ Embedding Service│
                         │ (OpenAI)         │
                         └──────┬───────────┘
                                │ 8. Store Vector
                                ▼
                         ┌──────────────────┐
                         │ Qdrant Vector DB │
                         └──────┬───────────┘
                                │ 9. Update Record
                                ▼
                         ┌──────────────────┐
                         │ Supabase DB      │
                         │ (Scan Result)    │
                         └──────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Scalability |

| **API Gateway** | Request routing, SSL termination, DDoS protection | Horizontal (Nginx/CDN) |
| **FastAPI App** | Business logic, validation, orchestration | Horizontal (stateless) |
| **Redis Cache** | Session storage, API response caching | Vertical + Clustering |
| **PostgreSQL** | Persistent data storage, ACID transactions | Read replicas, sharding |
| **Qdrant** | Vector similarity search | Horizontal sharding |
| **Celery Workers** | Async task processing | Horizontal (add workers) |
| **Supabase Storage** | File storage with CDN | Managed service |

---

# 2. Database Schema

## 2.1 Core Tables

### 2.1.1 Users Table

**Purpose:** Store user account information and authentication data

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'premium', 'admin')),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
    ON users FOR UPDATE
    USING (auth.uid() = id);
```

### 2.1.2 Books Table

**Purpose:** Store book information and user's library data

```sql
-- Books table
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Book metadata
    title VARCHAR(500) NOT NULL,
    authors TEXT[] DEFAULT ARRAY[]::TEXT[],
    isbn VARCHAR(13),
    isbn13 VARCHAR(13),
    publisher VARCHAR(200),
    published_date VARCHAR(50),
    description TEXT,
    page_count INTEGER CHECK (page_count >= 0),
    language VARCHAR(10) DEFAULT 'en',
    categories TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Images
    thumbnail_url TEXT,
    cover_url TEXT,
    
    -- User-specific data
    status VARCHAR(20) DEFAULT 'to_read' 
        CHECK (status IN ('to_read', 'reading', 'completed', 'did_not_finish')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    current_page INTEGER DEFAULT 0 CHECK (current_page >= 0),
    reading_format VARCHAR(20) CHECK (reading_format IN ('physical', 'ebook', 'audiobook')),
    
    -- Reading dates
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Search vector for full-text search
    search_vector tsvector
);

-- Indexes for books table
CREATE INDEX idx_books_user_id ON books(user_id);
CREATE INDEX idx_books_title ON books USING gin(to_tsvector('english', title));
CREATE INDEX idx_books_authors ON books USING gin(authors);
CREATE INDEX idx_books_isbn ON books(isbn) WHERE isbn IS NOT NULL;
CREATE INDEX idx_books_isbn13 ON books(isbn13) WHERE isbn13 IS NOT NULL;
CREATE INDEX idx_books_status ON books(user_id, status);
CREATE INDEX idx_books_categories ON books USING gin(categories);
CREATE INDEX idx_books_created_at ON books(created_at DESC);
CREATE INDEX idx_books_search_vector ON books USING gin(search_vector);

-- Composite index for common queries
CREATE INDEX idx_books_user_status_created ON books(user_id, status, created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER update_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for search vector
CREATE OR REPLACE FUNCTION books_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.authors, ' '), '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.categories, ' '), '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER books_search_vector_update
    BEFORE INSERT OR UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION books_search_vector_update();

-- Row Level Security
ALTER TABLE books ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own books"
    ON books FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own books"
    ON books FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own books"
    ON books FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own books"
    ON books FOR DELETE
    USING (auth.uid() = user_id);
```

### 2.1.3 Scans Table

**Purpose:** Store OCR scan results and processing status

```sql
-- Scans table
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Scan metadata
    scan_type VARCHAR(20) DEFAULT 'single_book' 
        CHECK (scan_type IN ('single_book', 'bookshelf', 'batch')),
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    
    -- Image data
    image_url TEXT,
    image_metadata JSONB,
    
    -- OCR results
    ocr_result JSONB,
    detected_books_count INTEGER DEFAULT 0,
    matched_books UUID[] DEFAULT ARRAY[]::UUID[],
    
    -- Processing data
    error_message TEXT,
    processing_time_seconds DECIMAL(10, 3),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes for scans table
CREATE INDEX idx_scans_user_id ON scans(user_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_created_at ON scans(created_at DESC);
CREATE INDEX idx_scans_user_created ON scans(user_id, created_at DESC);
CREATE INDEX idx_scans_user_status ON scans(user_id, status);

-- Trigger for updated_at
CREATE TRIGGER update_scans_updated_at
    BEFORE UPDATE ON scans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own scans"
    ON scans FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scans"
    ON scans FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scans"
    ON scans FOR UPDATE
    USING (auth.uid() = user_id);
```

### 2.1.4 User Preferences Table

**Purpose:** Store user settings and preferences

```sql
-- User preferences table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- UI Preferences
    theme VARCHAR(20) DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    language VARCHAR(10) DEFAULT 'en',
    
    -- Notification settings
    notification_enabled BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT false,
    
    -- Feature preferences
    auto_scan BOOLEAN DEFAULT false,
    favorite_genres TEXT[] DEFAULT ARRAY[]::TEXT[],
    reading_goal_pages INTEGER,
    reading_goal_books INTEGER,
    
    -- Privacy settings
    profile_public BOOLEAN DEFAULT false,
    show_reading_stats BOOLEAN DEFAULT true,
    
    -- Custom preferences
    custom_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Trigger for updated_at
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own preferences"
    ON user_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON user_preferences FOR UPDATE
    USING (auth.uid() = user_id);
```

### 2.1.5 Reading Sessions Table

**Purpose:** Track reading sessions for analytics

```sql
-- Reading sessions table
CREATE TABLE reading_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    
    -- Session data
    start_page INTEGER NOT NULL CHECK (start_page >= 0),
    end_page INTEGER NOT NULL CHECK (end_page >= start_page),
    pages_read INTEGER GENERATED ALWAYS AS (end_page - start_page) STORED,
    duration_minutes INTEGER CHECK (duration_minutes >= 0),
    
    -- Session metadata
    device VARCHAR(50),
    location VARCHAR(100),
    notes TEXT,
    
    -- Timestamps
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reading_sessions_user_id ON reading_sessions(user_id);
CREATE INDEX idx_reading_sessions_book_id ON reading_sessions(book_id);
CREATE INDEX idx_reading_sessions_started_at ON reading_sessions(started_at DESC);
CREATE INDEX idx_reading_sessions_user_started ON reading_sessions(user_id, started_at DESC);

-- Row Level Security
ALTER TABLE reading_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own reading sessions"
    ON reading_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own reading sessions"
    ON reading_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

### 2.1.6 API Keys Table (Future)

**Purpose:** Manage API access for third-party integrations

```sql
-- API keys table (for future API access)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Key data
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(10) NOT NULL, -- First 8 chars for identification
    name VARCHAR(100) NOT NULL,
    
    -- Permissions
    scopes TEXT[] DEFAULT ARRAY['read']::TEXT[],
    rate_limit INTEGER DEFAULT 1000, -- requests per hour
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active) WHERE is_active = true;

-- Trigger for updated_at
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## 2.2 Relationship Summary

### Entity Relationship Diagram (ERD)

```
┌─────────────────┐
│     USERS       │
│─────────────────│
│ id (PK)         │
│ email           │
│ username        │
│ hashed_password │
│ role            │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴──────────────────┬──────────────────┬───────────────────┐
    │                       │                  │                   │
    ▼                       ▼                  ▼                   ▼
┌───────────┐      ┌─────────────┐    ┌──────────────┐   ┌──────────────┐
│  BOOKS    │      │   SCANS     │    │USER_PREFS    │   │  API_KEYS    │
│───────────│      │─────────────│    │──────────────│   │──────────────│
│ id (PK)   │      │ id (PK)     │    │ id (PK)      │   │ id (PK)      │
│ user_id   │◀─┐   │ user_id     │    │ user_id      │   │ user_id      │
│ title     │  │   │ scan_type   │    │ theme        │   │ key_hash     │
│ authors   │  │   │ status      │    │ language     │   │ scopes       │
│ isbn      │  │   │ ocr_result  │    │ settings     │   │ is_active    │
│ status    │  │   └─────────────┘    └──────────────┘   └──────────────┘
│ rating    │  │
└─────┬─────┘  │
      │        │
      │ 1:N    │ N:N (via matched_books array)
      │        │
      ▼        │
┌──────────────┴──┐
│ READING_SESSIONS│
│─────────────────│
│ id (PK)         │
│ user_id         │
│ book_id         │
│ start_page      │
│ end_page        │
│ started_at      │
└─────────────────┘
```

### Relationship Details

| Relationship | Type | Description | Cascade |

| **users → books** | 1:N | One user has many books | DELETE CASCADE |
| **users → scans** | 1:N | One user has many scans | DELETE CASCADE |
| **users → user_preferences** | 1:1 | One user has one preferences record | DELETE CASCADE |
| **users → reading_sessions** | 1:N | One user has many reading sessions | DELETE CASCADE |
| **users → api_keys** | 1:N | One user has many API keys | DELETE CASCADE |
| **books → reading_sessions** | 1:N | One book has many reading sessions | DELETE CASCADE |
| **scans → books** | N:N | Scans can match multiple books (via array) | No direct FK |

### Key Database Constraints

```sql
-- Email uniqueness and format
ALTER TABLE users ADD CONSTRAINT users_email_check 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- ISBN format validation
ALTER TABLE books ADD CONSTRAINT books_isbn_check 
    CHECK (isbn IS NULL OR isbn ~ '^\d{10}$');
ALTER TABLE books ADD CONSTRAINT books_isbn13_check 
    CHECK (isbn13 IS NULL OR isbn13 ~ '^\d{13}$');

-- Rating range
ALTER TABLE books ADD CONSTRAINT books_rating_range 
    CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));

-- Date logic
ALTER TABLE books ADD CONSTRAINT books_dates_check 
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at);

-- Reading session page logic
ALTER TABLE reading_sessions ADD CONSTRAINT reading_sessions_pages_check 
    CHECK (end_page >= start_page);
```

### Database Performance Optimizations

```sql
-- Materialized view for user statistics (refreshed periodically)
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT b.id) as total_books,
    COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'reading') as books_reading,
    COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') as books_completed,
    AVG(b.rating) FILTER (WHERE b.rating IS NOT NULL) as average_rating,
    SUM(b.page_count) FILTER (WHERE b.status = 'completed') as total_pages_read,
    COUNT(DISTINCT s.id) as total_scans,
    MAX(b.created_at) as last_book_added
FROM users u
LEFT JOIN books b ON u.id = b.user_id
LEFT JOIN scans s ON u.id = s.user_id
GROUP BY u.id, u.username;

CREATE UNIQUE INDEX idx_user_stats_user_id ON user_stats(user_id);

-- Refresh schedule (run via cron/scheduler)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY user_stats;
```

---


# 3. API Specifications

## 3.1 Authentication

### Authentication Headers

All authenticated endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Header Structure

```yaml
Required Headers:
  Authorization: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  Content-Type: "application/json"

Optional Headers:
  X-Request-ID: "550e8400-e29b-41d4-a716-446655440000"  # For request tracking
  X-API-Version: "v1"  # API version
  Accept-Language: "en-US"  # Preferred language
  User-Agent: "ShelfScanner-iOS/1.0.0"  # Client identification
```

### JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid-here",
    "email": "user@example.com",
    "role": "user",
    "type": "access",
    "iat": 1640995200,
    "exp": 1640997000
  },
  "signature": "HMACSHA256(...)"
}
```

## 3.2 Base URLs

### Environment-Specific URLs

```yaml
Development:
  Base URL: http://localhost:8000
  API URL: http://localhost:8000/api/v1
  Docs URL: http://localhost:8000/docs
  
Staging:
  Base URL: https://staging-api.shelfscanner.com
  API URL: https://staging-api.shelfscanner.com/api/v1
  Docs URL: https://staging-api.shelfscanner.com/docs
  
Production:
  Base URL: https://api.shelfscanner.com
  API URL: https://api.shelfscanner.com/api/v1
  Docs URL: None (disabled in production)
```

## 3.3 Core Endpoints

### 3.3.1 Authentication Endpoints

#### POST /api/v1/auth/register

**Description:** Register a new user account

**Request:**

```http
POST /api/v1/auth/register HTTP/1.1
Host: api.shelfscanner.com
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "username": "johndoe",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Validation Rules:**

- Email: Valid email format, unique
- Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit
- Username: 3-50 chars, alphanumeric + underscore, unique
- Full name: Optional, max 100 chars

#### POST /api/v1/auth/login

**Description:** Authenticate user and receive tokens

**Request:**

```http
POST /api/v1/auth/login HTTP/1.1
Host: api.shelfscanner.com
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/v1/auth/refresh

**Description:** Refresh access token using refresh token

**Request:**

```http
POST /api/v1/auth/refresh HTTP/1.1
Host: api.shelfscanner.com
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /api/v1/auth/me

**Description:** Get current authenticated user information

**Request:**

```http
GET /api/v1/auth/me HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "email_verified": true,
  "created_at": "2024-01-27T10:00:00Z",
  "updated_at": "2024-01-27T10:00:00Z",
  "last_login": "2024-01-27T15:30:00Z"
}
```

### 3.3.2 Scan Endpoints

#### POST /api/v1/scan/upload

**Description:** Upload image for OCR scanning

**Request:**

```http
POST /api/v1/scan/upload HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="book_cover.jpg"
Content-Type: image/jpeg

[Binary image data]
------WebKitFormBoundary
Content-Disposition: form-data; name="scan_type"

single_book
------WebKitFormBoundary
Content-Disposition: form-data; name="process_async"

true
------WebKitFormBoundary--
```

**Query Parameters:**

- `scan_type`: "single_book" | "bookshelf" | "batch" (default: "single_book")
- `process_async`: boolean (default: true)
- `auto_add_books`: boolean (default: false)

**Response:** `202 Accepted`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "scan_type": "single_book",
  "image_url": "https://storage.supabase.co/v1/object/scans/...",
  "status": "pending",
  "detected_books_count": 0,
  "created_at": "2024-01-27T16:00:00Z",
  "image_metadata": {
    "filename": "book_cover.jpg",
    "size_bytes": 1048576,
    "mime_type": "image/jpeg",
    "width": 1920,
    "height": 1080
  }
}
```

#### GET /api/v1/scan/{scan_id}

**Description:** Get scan result by ID

**Request:**

```http
GET /api/v1/scan/660e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "scan_type": "single_book",
  "image_url": "https://storage.supabase.co/v1/object/scans/...",
  "status": "completed",
  "detected_books_count": 1,
  "processing_time_seconds": 4.237,
  "completed_at": "2024-01-27T16:00:05Z",
  "ocr_result": {
    "raw_text": "The Great Gatsby\nF. Scott Fitzgerald\nISBN: 9780743273565",
    "confidence": 0.95,
    "detected_titles": ["The Great Gatsby"],
    "detected_authors": ["F. Scott Fitzgerald"],
    "detected_isbns": ["9780743273565"],
    "language": "eng"
  },
  "book_matches": [
    {
      "title": "The Great Gatsby",
      "authors": ["F. Scott Fitzgerald"],
      "isbn": "9780743273565",
      "confidence": 0.98,
      "source": "google",
      "book_id": null
    }
  ]
}
```

#### GET /api/v1/scan/

**Description:** List user's scans with pagination

**Request:**

```http
GET /api/v1/scan/?limit=20&offset=0 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**

- `limit`: integer (1-100, default: 20)
- `offset`: integer (default: 0)
- `status`: "pending" | "processing" | "completed" | "failed" (optional filter)

**Response:** `200 OK`

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "scan_type": "single_book",
    "detected_books_count": 1,
    "created_at": "2024-01-27T16:00:00Z"
  }
]
```

### 3.3.3 Books Endpoints

#### POST /api/v1/books/

**Description:** Create a new book in library

**Request:**

```http
POST /api/v1/books/ HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "The Great Gatsby",
  "authors": ["F. Scott Fitzgerald"],
  "isbn": "9780743273565",
  "publisher": "Scribner",
  "published_date": "2004-09-30",
  "description": "A novel set in the Jazz Age...",
  "page_count": 180,
  "categories": ["Fiction", "Classic"],
  "status": "reading",
  "rating": 5,
  "notes": "Amazing book!",
  "tags": ["classic", "american-literature"]
}
```

**Response:** `201 Created`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "authors": ["F. Scott Fitzgerald"],
  "isbn": "9780743273565",
  "publisher": "Scribner",
  "published_date": "2004-09-30",
  "description": "A novel set in the Jazz Age...",
  "page_count": 180,
  "categories": ["Fiction", "Classic"],
  "language": "en",
  "thumbnail_url": null,
  "cover_url": null,
  "status": "reading",
  "rating": 5,
  "notes": "Amazing book!",
  "tags": ["classic", "american-literature"],
  "current_page": 0,
  "reading_format": null,
  "started_at": null,
  "completed_at": null,
  "created_at": "2024-01-27T16:10:00Z",
  "updated_at": "2024-01-27T16:10:00Z"
}
```

#### GET /api/v1/books/{book_id}

**Description:** Get book by ID

**Request:**

```http
GET /api/v1/books/770e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "authors": ["F. Scott Fitzgerald"],
  "status": "reading",
  "rating": 5,
  "created_at": "2024-01-27T16:10:00Z"
}
```

#### PUT /api/v1/books/{book_id}

**Description:** Update book information

**Request:**

```http
PUT /api/v1/books/770e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "completed",
  "rating": 5,
  "current_page": 180,
  "notes": "One of the best books I've ever read!"
}
```

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "rating": 5,
  "current_page": 180,
  "notes": "One of the best books I've ever read!",
  "completed_at": "2024-01-27T16:30:00Z",
  "updated_at": "2024-01-27T16:30:00Z"
}
```

#### DELETE /api/v1/books/{book_id}

**Description:** Delete book from library

**Request:**

```http
DELETE /api/v1/books/770e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `204 No Content`

#### GET /api/v1/books/

**Description:** List books with pagination and filtering

**Request:**

```http
GET /api/v1/books/?status=reading&page=1&page_size=20 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**

- `status`: "to_read" | "reading" | "completed" | "did_not_finish" (optional)
- `page`: integer (min: 1, default: 1)
- `page_size`: integer (1-100, default: 20)
- `sort`: "title" | "created_at" | "rating" (default: "created_at")
- `order`: "asc" | "desc" (default: "desc")

**Response:** `200 OK`

```json
{
  "books": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "title": "The Great Gatsby",
      "authors": ["F. Scott Fitzgerald"],
      "status": "reading",
      "rating": 5,
      "created_at": "2024-01-27T16:10:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

#### GET /api/v1/books/stats/summary

**Description:** Get user's book statistics

**Request:**

```http
GET /api/v1/books/stats/summary HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`

```json
{
  "total_books": 42,
  "books_by_status": {
    "reading": 5,
    "completed": 30,
    "to_read": 7,
    "did_not_finish": 0
  },
  "books_by_genre": {
    "Fiction": 20,
    "Non-Fiction": 15,
    "Science": 7
  },
  "average_rating": 4.2,
  "total_pages_read": 5400
}
```

### 3.3.4 Recommendations Endpoints

#### GET /api/v1/recommendations/similar/{book_id}

**Description:** Get books similar to a specific book

**Request:**

```http
GET /api/v1/recommendations/similar/770e8400-e29b-41d4-a716-446655440000?limit=10 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**

- `limit`: integer (1-50, default: 10)

**Response:** `200 OK`

```json
[
  {
    "book": {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "title": "Tender Is the Night",
      "authors": ["F. Scott Fitzgerald"],
      "categories": ["Fiction", "Classic"]
    },
    "similarity_score": 0.92,
    "reason": "Similar to your book based on content and genre"
  }
]
```

#### GET /api/v1/recommendations/personalized

**Description:** Get personalized recommendations based on reading history

**Request:**

```http
GET /api/v1/recommendations/personalized?limit=10 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**

- `limit`: integer (1-50, default: 10)

**Response:** `200 OK`

```json
[
  {
    "book": {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "title": "The Sun Also Rises",
      "authors": ["Ernest Hemingway"],
      "categories": ["Fiction", "Classic"]
    },
    "similarity_score": 0.88,
    "reason": "Based on your reading history and preferences"
  }
]
```

#### GET /api/v1/recommendations/ai

**Description:** Get AI-powered recommendations with explanations

**Request:**

```http
GET /api/v1/recommendations/ai?limit=5 HTTP/1.1
Host: api.shelfscanner.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**

- `limit`: integer (1-10, default: 5)

**Response:** `200 OK`

```json
{
  "recommendations": [
    {
      "text": "Based on your love of classic American literature, particularly F. Scott Fitzgerald, I recommend:\n\n1. 'The Sun Also Rises' by Ernest Hemingway - A masterpiece of the Lost Generation that shares Fitzgerald's Jazz Age setting...",
      "source": "ai"
    }
  ],
  "count": 1
}
```

## 3.4 Error Responses

### Error Response Format

All error responses follow this standard format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-27T16:00:00Z",
  "path": "/api/v1/books/invalid-id",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### HTTP Status Codes

| Status Code | Description | Example Use Case |

| **200 OK** | Success | GET requests |
| **201 Created** | Resource created | POST requests |
| **202 Accepted** | Async processing | Scan upload |
| **204 No Content** | Success, no body | DELETE requests |
| **400 Bad Request** | Invalid input | Malformed JSON |
| **401 Unauthorized** | Auth required | Missing/invalid token |
| **403 Forbidden** | Access denied | Insufficient permissions |
| **404 Not Found** | Resource not found | Invalid book ID |
| **409 Conflict** | Resource conflict | Duplicate email |
| **422 Unprocessable Entity** | Validation error | Invalid email format |
| **429 Too Many Requests** | Rate limit exceeded | Too many requests |
| **500 Internal Server Error** | Server error | Database connection failed |
| **503 Service Unavailable** | Service down | Maintenance mode |

### Error Code Reference

#### Authentication Errors (AUTH_*)

```json
{
  "detail": "Could not validate credentials",
  "error_code": "AUTH_INVALID_TOKEN",
  "timestamp": "2024-01-27T16:00:00Z"
}
```

**Error Codes:**

- `AUTH_INVALID_TOKEN`: Invalid or expired JWT token
- `AUTH_INVALID_CREDENTIALS`: Wrong email/password
- `AUTH_TOKEN_EXPIRED`: Access token expired
- `AUTH_REFRESH_TOKEN_INVALID`: Invalid refresh token
- `AUTH_USER_NOT_FOUND`: User does not exist
- `AUTH_EMAIL_NOT_VERIFIED`: Email verification required

#### Validation Errors (VAL_*)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ],
  "error_code": "VAL_VALIDATION_ERROR",
  "timestamp": "2024-01-27T16:00:00Z"
}
```

**Error Codes:**

- `VAL_VALIDATION_ERROR`: Pydantic validation failed
- `VAL_MISSING_FIELD`: Required field missing
- `VAL_INVALID_FORMAT`: Invalid data format
- `VAL_OUT_OF_RANGE`: Value out of acceptable range

#### Resource Errors (RES_*)

```json
{
  "detail": "Book not found",
  "error_code": "RES_NOT_FOUND",
  "timestamp": "2024-01-27T16:00:00Z"
}
```

**Error Codes:**

- `RES_NOT_FOUND`: Resource does not exist
- `RES_ALREADY_EXISTS`: Duplicate resource
- `RES_PERMISSION_DENIED`: Not authorized to access resource
- `RES_CONFLICT`: Resource state conflict

#### Rate Limit Errors (RATE_*)

```json
{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45,
  "timestamp": "2024-01-27T16:00:00Z"
}
```

**Error Codes:**

- `RATE_LIMIT_EXCEEDED`: Too many requests
- `RATE_DAILY_LIMIT`: Daily limit reached
- `RATE_HOURLY_LIMIT`: Hourly limit reached

#### Service Errors (SVC_*)

```json
{
  "detail": "OCR service temporarily unavailable",
  "error_code": "SVC_OCR_UNAVAILABLE",
  "timestamp": "2024-01-27T16:00:00Z"
}
```

**Error Codes:**

- `SVC_OCR_UNAVAILABLE`: OCR service down
- `SVC_OPENAI_ERROR`: OpenAI API error
- `SVC_EXTERNAL_API_ERROR`: External API failure
- `SVC_DATABASE_ERROR`: Database connection error

## 3.5 Rate Limiting

### Rate Limit Configuration

| Endpoint Pattern | Per Minute | Per Hour | Per Day |

| **Authentication** |
| POST /auth/register | 5 | 20 | 50 |
| POST /auth/login | 10 | 100 | 500 |
| POST /auth/refresh | 30 | 500 | 5000 |

| **Scan Operations** |
| POST /scan/upload | 10 | 50 | 200 |
| GET /scan/* | 60 | 1000 | 10000 |

| **Book Operations** |
| POST /books/ | 30 | 500 | 5000 |
| GET /books/* | 60 | 1000 | 10000 |
| PUT /books/* | 30 | 500 | 5000 |
| DELETE /books/* | 20 | 200 | 1000 |

| **Recommendations** |
| GET /recommendations/* | 20 | 200 | 1000 |
| **Default** | 60 | 1000 | 10000 |

### Rate Limit Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640997000
X-RateLimit-Reset-After: 45
Retry-After: 45
```

### Rate Limit Response

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640997000
Retry-After: 45
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45,
  "timestamp": "2024-01-27T16:00:00Z"
}
```

### Rate Limit Bypass (Premium Users)

Premium users have higher limits:

| Tier | Multiplier | Limits |

| Free | 1x | Standard limits |
| Premium | 5x | 5x all limits |
| Enterprise | Custom | Negotiated SLA |

---

*[Document continues with sections 4-12 in next message due to length...]*

**Next sections to follow:**

- Integration Requirements
- Data Synchronization
- Security and Compliance
- Performance Requirements
- Monitoring and Logging
- Testing Requirements
- Deployment and CI/CD
- Edge Cases and Error Handling
- Future Considerations
- Appendix
