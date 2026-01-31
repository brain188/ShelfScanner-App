# ShelfScanner - Technical Documentation (Part 2)

**Continuation from Part 1**

---

# 4. Integration Requirements

## 4.1 External Service Integrations

### 4.1.1 OpenAI Integration

**Purpose:** AI-powered recommendations and text embeddings

**Configuration:**
```yaml
Service: OpenAI API
Endpoint: https://api.openai.com/v1
Authentication: API Key (Bearer token)
Models Used:
  - gpt-4-turbo-preview (Recommendations)
  - text-embedding-3-small (Vector embeddings)
```

**API Calls:**
```python
# Embeddings
POST https://api.openai.com/v1/embeddings
{
  "model": "text-embedding-3-small",
  "input": "Book title and description",
  "dimensions": 1536
}

# Chat Completions (Recommendations)
POST https://api.openai.com/v1/chat/completions
{
  "model": "gpt-4-turbo-preview",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Rate Limits:**
- Embeddings: 3,000 requests/minute
- GPT-4: 500 requests/minute
- Token limits: 150,000 tokens/minute

**Error Handling:**
- Retry with exponential backoff (3 attempts)
- Fallback to cached recommendations
- Circuit breaker after 5 consecutive failures

**Cost Management:**
- Monthly budget: $50 (MVP)
- Alert at 80% budget consumption
- Automatic downgrade to cheaper models if needed

### 4.1.2 Supabase Integration

**Purpose:** Authentication, database, and file storage

**Configuration:**
```yaml
Services:
  - Auth: User authentication and session management
  - Database: PostgreSQL 15
  - Storage: File storage for book images
  
Endpoints:
  - Auth: https://PROJECT_ID.supabase.co/auth/v1
  - Database: https://PROJECT_ID.supabase.co/rest/v1
  - Storage: https://PROJECT_ID.supabase.co/storage/v1
```

**Authentication Flow:**
```javascript
// Sign up
POST /auth/v1/signup
{
  "email": "user@example.com",
  "password": "password",
  "data": {
    "username": "johndoe",
    "full_name": "John Doe"
  }
}

// Sign in
POST /auth/v1/token?grant_type=password
{
  "email": "user@example.com",
  "password": "password"
}

// Refresh token
POST /auth/v1/token?grant_type=refresh_token
{
  "refresh_token": "..."
}
```

**Row Level Security (RLS):**
- All tables have RLS enabled
- Users can only access their own data
- Service role key bypasses RLS for admin operations

**Storage Buckets:**
```yaml
Buckets:
  - images: Public bucket for book covers
  - scans: Private bucket for uploaded scans
  - avatars: Public bucket for user profile pictures
  
Security:
  - Max file size: 10MB
  - Allowed types: image/jpeg, image/png, image/webp
  - Automatic image optimization
```

### 4.1.3 Google Books API

**Purpose:** Book metadata lookup by ISBN and title

**Configuration:**
```yaml
Service: Google Books API v1
Endpoint: https://www.googleapis.com/books/v1
Authentication: API Key (optional for higher limits)
Rate Limit: 1,000 requests/day (free), 10,000/day (with key)
```

**API Calls:**
```python
# Search by ISBN
GET /volumes?q=isbn:9780743273565

# Search by title and author
GET /volumes?q=intitle:Gatsby+inauthor:Fitzgerald

# Get volume details
GET /volumes/{volumeId}
```

**Response Mapping:**
```json
{
  "volumeInfo": {
    "title": "The Great Gatsby",
    "authors": ["F. Scott Fitzgerald"],
    "publisher": "Scribner",
    "publishedDate": "2004-09-30",
    "description": "...",
    "pageCount": 180,
    "categories": ["Fiction"],
    "imageLinks": {
      "thumbnail": "http://...",
      "large": "http://..."
    },
    "industryIdentifiers": [
      {"type": "ISBN_13", "identifier": "9780743273565"}
    ]
  }
}
```

**Fallback Strategy:**
1. Try Google Books API
2. If not found, try OpenLibrary API
3. If still not found, return partial match from OCR

### 4.1.4 OpenLibrary API

**Purpose:** Alternative book metadata source

**Configuration:**
```yaml
Service: OpenLibrary API
Endpoint: https://openlibrary.org/api
Authentication: None (public API)
Rate Limit: None specified (use responsibly)
```

**API Calls:**
```python
# Search by ISBN
GET https://openlibrary.org/isbn/9780743273565.json

# Search by title
GET https://openlibrary.org/search.json?title=Great+Gatsby

# Get work details
GET https://openlibrary.org/works/OL468516W.json
```

**Advantages:**
- No authentication required
- More comprehensive catalog for older books
- Public domain works

**Limitations:**
- Slower response times
- Less consistent data format
- No official SLA

### 4.1.5 Qdrant Vector Database

**Purpose:** Store and search book embeddings for recommendations

**Configuration:**
```yaml
Service: Qdrant
Deployment: Self-hosted (Docker) or Qdrant Cloud
Endpoint: http://localhost:6333 or https://cluster.qdrant.io
Authentication: API Key (cloud only)
```

**Collection Setup:**
```python
# Create collection
PUT /collections/books_embeddings
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}

# Upsert embedding
PUT /collections/books_embeddings/points
{
  "points": [
    {
      "id": "book-uuid",
      "vector": [0.1, 0.2, ...],
      "payload": {
        "title": "Book Title",
        "authors": ["Author"],
        "user_id": "user-uuid"
      }
    }
  ]
}

# Search similar
POST /collections/books_embeddings/points/search
{
  "vector": [0.1, 0.2, ...],
  "limit": 10,
  "score_threshold": 0.7,
  "filter": {
    "must": [
      {"key": "user_id", "match": {"value": "user-uuid"}}
    ]
  }
}
```

**Performance Tuning:**
- HNSW index for fast approximate search
- Quantization for reduced memory usage
- Sharding for horizontal scaling

### 4.1.6 Redis Cache

**Purpose:** Cache API responses and session data

**Configuration:**
```yaml
Service: Redis 7
Deployment: Self-hosted or Redis Cloud
Endpoint: redis://localhost:6379
Authentication: Password (production)
```

**Caching Strategy:**
```python
# Cache patterns
book:{user_id}:{book_id}  # TTL: 1 hour
scan:{scan_id}  # TTL: 24 hours
user:{user_id}:stats  # TTL: 5 minutes
recommendations:{user_id}  # TTL: 1 hour

# Cache invalidation
- On book update: DELETE book:{user_id}:{book_id}
- On book create/delete: DELETE user:{user_id}:stats
- On scan complete: UPDATE scan:{scan_id}
```

**Eviction Policy:**
```yaml
maxmemory: 256mb
maxmemory-policy: allkeys-lru
```

### 4.1.7 Tesseract OCR

**Purpose:** Extract text from book images

**Configuration:**
```yaml
Service: Tesseract OCR 5.x
Deployment: Self-hosted (system package)
Language: English (eng)
PSM Mode: 6 (Assume uniform block of text)
```

**Preprocessing Pipeline:**
```python
1. Resize to max 1920x1080
2. Convert to grayscale
3. Enhance contrast (1.5x)
4. Adaptive thresholding
5. Noise reduction (fastNlMeansDenoising)
6. Extract text with Tesseract
```

**Performance:**
- Average processing time: 3-5 seconds
- Confidence threshold: 0.5 (minimum)
- Parallel processing via Celery workers

## 4.2 Webhook Integrations (Future)

### 4.2.1 Outgoing Webhooks

**Events to Send:**
```yaml
Events:
  - book.created
  - book.updated
  - book.deleted
  - scan.completed
  - recommendation.generated
  
Payload Format:
{
  "event": "book.created",
  "timestamp": "2024-01-27T16:00:00Z",
  "user_id": "user-uuid",
  "data": {...}
}
```

**Retry Policy:**
- 3 retry attempts
- Exponential backoff: 1s, 2s, 4s
- Mark as failed after all retries

### 4.2.2 Incoming Webhooks (OAuth Callbacks)

**Supported Providers (Future):**
```yaml
OAuth Providers:
  - Google: OAuth 2.0
  - GitHub: OAuth 2.0
  - Apple: Sign in with Apple
  
Callback URL:
  https://api.shelfscanner.com/api/v1/auth/callback/{provider}
```

---

# 5. Data Synchronization

## 5.1 Real-time Requirements

### 5.1.1 WebSocket Connections (Future)

**Use Cases:**
- Real-time scan progress updates
- Live recommendation updates
- Multi-device synchronization

**Implementation:**
```yaml
Protocol: WebSocket (WSS)
Library: FastAPI WebSockets
Authentication: JWT token in query parameter

Connection:
  wss://api.shelfscanner.com/ws?token=<jwt_token>

Events:
  - scan:progress
  - scan:completed
  - book:updated
  - recommendation:ready
```

**Message Format:**
```json
{
  "event": "scan:progress",
  "data": {
    "scan_id": "uuid",
    "progress": 45,
    "status": "processing"
  },
  "timestamp": "2024-01-27T16:00:00Z"
}
```

### 5.1.2 Server-Sent Events (SSE)

**Alternative to WebSockets:**
```python
# Endpoint
GET /api/v1/events/stream

# Response
Content-Type: text/event-stream

event: scan_update
data: {"scan_id": "uuid", "status": "completed"}
id: 1

event: recommendation_ready
data: {"count": 10}
id: 2
```

**Advantages:**
- Simpler than WebSockets
- Automatic reconnection
- Works with HTTP/2

## 5.2 Offline Support

### 5.2.1 Client-Side Caching Strategy

**Cacheable Resources:**
```yaml
User Profile: 24 hours
Book List: 1 hour
Book Details: 4 hours
Scan History: 1 hour
Recommendations: 30 minutes
```

**Service Worker (Future Web App):**
```javascript
// Cache-first strategy for static assets
// Network-first strategy for API calls
// Background sync for offline mutations

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/v1/books')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
```

### 5.2.2 Offline Queue

**Queued Operations:**
```yaml
Supported:
  - Create book
  - Update book
  - Delete book
  - Update reading progress

Not Supported (Requires Network):
  - Image scanning (requires server)
  - AI recommendations (requires OpenAI)
  - User authentication
```

**Queue Storage:**
```javascript
// IndexedDB for offline queue
const offlineQueue = {
  operations: [
    {
      id: "uuid",
      type: "UPDATE_BOOK",
      payload: {...},
      timestamp: "2024-01-27T16:00:00Z",
      retries: 0
    }
  ]
};
```

## 5.3 Background Sync

### 5.3.1 Sync Triggers

**Automatic Sync:**
```yaml
Triggers:
  - Network reconnection
  - App foreground (mobile)
  - Tab visibility change (web)
  - Periodic sync (every 15 minutes)
  - Manual refresh
```

**Sync Priority:**
```yaml
High Priority:
  - User authentication
  - Book updates
  - Scan results

Medium Priority:
  - Book list refresh
  - Statistics update

Low Priority:
  - Recommendation refresh
  - Profile updates
```

### 5.3.2 Conflict Resolution

**Conflict Scenarios:**

```yaml
Scenario 1: Same book updated on multiple devices
Resolution: Last-write-wins (based on updated_at timestamp)

Scenario 2: Book deleted on one device, updated on another
Resolution: Delete takes precedence

Scenario 3: Different fields updated on different devices
Resolution: Merge non-conflicting fields

Scenario 4: Network partition during scan
Resolution: Retry scan upload, maintain scan ID
```

**Conflict Detection:**
```python
def resolve_conflict(server_version, client_version):
    # Compare timestamps
    if server_version['updated_at'] > client_version['updated_at']:
        return server_version  # Server wins
    elif server_version['updated_at'] < client_version['updated_at']:
        return client_version  # Client wins
    else:
        # Same timestamp - merge
        return merge_versions(server_version, client_version)
```

### 5.3.3 Sync API Endpoints

**Bulk Sync Endpoint:**
```http
POST /api/v1/sync/bulk HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "since": "2024-01-27T12:00:00Z",
  "operations": [
    {
      "type": "UPDATE_BOOK",
      "book_id": "uuid",
      "data": {...},
      "client_timestamp": "2024-01-27T15:30:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "synced": 5,
  "conflicts": [
    {
      "operation_id": 0,
      "reason": "NEWER_VERSION_ON_SERVER",
      "server_version": {...},
      "client_version": {...}
    }
  ],
  "server_timestamp": "2024-01-27T16:00:00Z"
}
```

---

# 6. Security and Compliance

## 6.1 Authentication and Authorization

### 6.1.1 Authentication Configuration

**JWT Configuration:**
```yaml
Algorithm: HS256
Access Token:
  Expiry: 30 minutes
  Refresh: Not allowed
  
Refresh Token:
  Expiry: 7 days
  Rotation: New refresh token on each refresh
  
Token Payload:
  sub: User ID (UUID)
  email: User email
  role: User role
  type: "access" or "refresh"
  iat: Issued at timestamp
  exp: Expiration timestamp
```

**Password Requirements:**
```yaml
Minimum Length: 8 characters
Required:
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character (optional)
  
Forbidden:
  - Common passwords (top 10,000 list)
  - User's email or username
  - Sequential characters (123456, abcdef)
  
Hashing: bcrypt with cost factor 12
```

**Session Management:**
```yaml
Storage: Redis
TTL: 30 minutes (access), 7 days (refresh)
Invalidation:
  - On logout
  - On password change
  - On user deactivation
  - On token expiry
```

### 6.1.2 Permission Levels

**Role-Based Access Control (RBAC):**

| Role | Permissions | Limits |
|------|------------|--------|
| **User (Free)** | • Own book CRUD<br>• Scan upload (10/day)<br>• Basic recommendations<br>• Read-only public data | • 10 scans/day<br>• 500 books max<br>• Basic support |
| **Premium** | • All User permissions<br>• Unlimited scans<br>• Advanced recommendations<br>• Export data<br>• API access | • Unlimited scans<br>• Unlimited books<br>• Priority support |
| **Admin** | • All Premium permissions<br>• User management<br>• System configuration<br>• View all data<br>• Analytics access | • No limits<br>• Full system access |

**Permission Matrix:**

| Resource | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
| **Own Books** | User+ | User+ | User+ | User+ |
| **Own Scans** | User+ | User+ | User+ | User+ |
| **Own Profile** | - | User+ | User+ | - |
| **Other Users** | - | - | - | Admin |
| **System Config** | - | Admin | Admin | Admin |

**API Scopes (Future):**
```yaml
Scopes:
  - read:books
  - write:books
  - read:scans
  - write:scans
  - read:profile
  - write:profile
  - admin:users
  - admin:system
```

### 6.1.3 Multi-Factor Authentication (Future)

**MFA Options:**
```yaml
Methods:
  - TOTP (Google Authenticator, Authy)
  - SMS (via Twilio)
  - Email codes
  - Recovery codes

Implementation:
  - Optional for users
  - Mandatory for admins
  - Backup codes (10 per user)
```

## 6.2 Data Encryption

### 6.2.1 Data at Rest

**Database Encryption:**
```yaml
Provider: Supabase (PostgreSQL)
Method: AES-256 encryption
Scope: 
  - All database tables
  - Backup files
  - WAL files
  
Key Management:
  - AWS KMS (Supabase managed)
  - Automatic key rotation
  - Separate keys per environment
```

**File Storage Encryption:**
```yaml
Provider: Supabase Storage
Method: AES-256 encryption
Scope:
  - Uploaded images
  - Book covers
  - User avatars
  
Access:
  - Signed URLs with expiry
  - Row Level Security integration
```

**Environment Variables:**
```yaml
Storage: Environment files (.env)
Production: AWS Secrets Manager / Vault
Rotation: Manual (quarterly recommended)

Sensitive Variables:
  - SECRET_KEY
  - SUPABASE_SERVICE_KEY
  - OPENAI_API_KEY
  - Database credentials
  - API keys
```

### 6.2.2 Data in Transit

**TLS/SSL Configuration:**
```yaml
Protocol: TLS 1.3 (minimum TLS 1.2)
Ciphers: 
  - TLS_AES_256_GCM_SHA384
  - TLS_CHACHA20_POLY1305_SHA256
  - TLS_AES_128_GCM_SHA256
  
Certificate: Let's Encrypt (auto-renewal)
HSTS: Enabled (max-age=31536000)
```

**API Communication:**
```yaml
All API Calls: HTTPS only
HTTP Redirect: 301 to HTTPS
Certificate Pinning: Recommended for mobile apps

External Services:
  - OpenAI: TLS 1.2+
  - Supabase: TLS 1.2+
  - Google Books: TLS 1.2+
```

## 6.3 GDPR Compliance

### 6.3.1 Data Subject Rights

**Right to Access:**
```http
GET /api/v1/gdpr/export HTTP/1.1
Authorization: Bearer <token>

Response: ZIP file containing:
  - profile.json (user data)
  - books.json (all books)
  - scans.json (scan history)
  - reading_sessions.json
  - metadata.json (creation dates, IPs)
```

**Right to Rectification:**
```http
PUT /api/v1/users/me
{
  "email": "newemail@example.com",
  "full_name": "Updated Name"
}
```

**Right to Erasure (Right to be Forgotten):**
```http
DELETE /api/v1/gdpr/delete-account
{
  "password": "user_password",
  "confirmation": "DELETE MY ACCOUNT"
}

Process:
1. Verify password
2. Mark account for deletion
3. 30-day grace period
4. Permanent deletion:
   - User data
   - Books
   - Scans
   - Images (Supabase Storage)
   - Vector embeddings
   - Cache entries
5. Anonymize logs (replace user_id with "deleted_user")
```

**Right to Data Portability:**
```http
GET /api/v1/gdpr/export?format=json
GET /api/v1/gdpr/export?format=csv

Formats supported:
  - JSON (default)
  - CSV (for books and scans)
  - XML (optional)
```

**Right to Object:**
```yaml
Marketing Emails: Unsubscribe link in all emails
Data Processing: Opt-out in user preferences
Analytics: Cookie consent banner
```

### 6.3.2 Data Retention

**Retention Periods:**
```yaml
Active Users:
  - Profile: Indefinite (until account deletion)
  - Books: Indefinite
  - Scans: 1 year (then archived)
  - Logs: 90 days
  
Inactive Users (no login for 2 years):
  - Email notification at 18 months
  - Final warning at 23 months
  - Account deletion at 24 months
  
Deleted Accounts:
  - Grace period: 30 days
  - Permanent deletion: After grace period
  - Backup retention: 30 days post-deletion
```

**Data Minimization:**
```yaml
Collect Only:
  - Email (required for auth)
  - Username (optional)
  - Full name (optional)
  - Book preferences (user-provided)
  
Do Not Collect:
  - Physical address
  - Phone number (unless MFA enabled)
  - Payment info (handled by Stripe if applicable)
  - Unnecessary metadata
```

### 6.3.3 Privacy Policy

**Key Points:**
```yaml
Data Collected:
  - Email, username, password (hashed)
  - Book library data
  - Reading preferences
  - Scan images (temporarily)
  - Usage analytics (anonymized)
  
Data Processing:
  - OpenAI: Book recommendations (no PII sent)
  - Supabase: Data storage and auth
  - Google Books: Book metadata lookup
  
Data Sharing:
  - No sharing with third parties
  - OpenAI receives only book titles/descriptions
  - No advertising or tracking
  
User Rights:
  - Access, rectify, delete, export data
  - Opt-out of analytics
  - Contact: privacy@shelfscanner.com
```

## 6.4 PCI Compliance

### 6.4.1 Payment Processing (Future)

**Approach: PCI DSS SAQ A**

```yaml
Strategy: Never handle card data
Provider: Stripe / PayPal
Method: Hosted payment page or Stripe.js

Compliance Level:
  - SAQ A (simplest)
  - No card data touches our servers
  - Stripe handles PCI compliance
```

**Implementation:**
```javascript
// Client-side only
import {loadStripe} from '@stripe/stripe-js';

const stripe = await loadStripe('pk_...');
const {error} = await stripe.confirmCardPayment(clientSecret, {
  payment_method: {
    card: cardElement,
  }
});
```

**Subscription Handling:**
```yaml
Webhook Events:
  - checkout.session.completed
  - customer.subscription.created
  - customer.subscription.updated
  - customer.subscription.deleted
  
Stored in DB:
  - Stripe customer ID
  - Subscription ID
  - Status (active, canceled, past_due)
  - Plan (free, premium)
  - No card details
```

### 6.4.2 Security Measures

**PCI-Adjacent Requirements:**
```yaml
TLS: Required for all traffic
Logging: No sensitive data in logs
Access: Role-based access control
Monitoring: Real-time fraud detection
Backups: Encrypted, no payment data
```

---

# 7. Performance Requirements

## 7.1 Response Time Targets

### 7.1.1 API Endpoint SLAs

| Endpoint Category | P50 | P95 | P99 | Max Timeout |
|-------------------|-----|-----|-----|-------------|
| **Authentication** |
| POST /auth/register | <200ms | <500ms | <1s | 5s |
| POST /auth/login | <200ms | <500ms | <1s | 5s |
| POST /auth/refresh | <100ms | <200ms | <500ms | 2s |
| **Books** |
| GET /books/ (list) | <200ms | <400ms | <800ms | 5s |
| GET /books/{id} | <100ms | <200ms | <400ms | 2s |
| POST /books/ | <300ms | <600ms | <1s | 5s |
| PUT /books/{id} | <200ms | <400ms | <800ms | 5s |
| **Scan** |
| POST /scan/upload | <500ms | <1s | <2s | 10s |
| GET /scan/{id} | <100ms | <200ms | <400ms | 2s |
| **Recommendations** |
| GET /recommendations/* | <500ms | <1s | <2s | 10s |

### 7.1.2 Background Job SLAs

| Job Type | Target Duration | P95 | Alert Threshold |
|----------|----------------|-----|-----------------|
| OCR Processing | 3-5s | 10s | 15s |
| Embedding Generation | 1-2s | 5s | 10s |
| Book Lookup | 500ms-1s | 2s | 5s |
| Recommendation Batch | 5-10s | 20s | 30s |

### 7.1.3 Database Query Performance

```yaml
Simple Queries (Single table, indexed):
  Target: <10ms
  P95: <50ms
  Example: SELECT * FROM books WHERE id = 'uuid'

Complex Queries (Joins, aggregations):
  Target: <100ms
  P95: <500ms
  Example: User stats with aggregations

Full-Text Search:
  Target: <200ms
  P95: <1s
  Example: Book title search across library
```

## 7.2 Scalability Targets

### 7.2.1 User Growth Projections

```yaml
Phase 1 (MVP - Month 1-3):
  Users: 100-1,000
  Daily Active: 50-500
  Requests/day: 10,000
  Storage: 10GB
  
Phase 2 (Growth - Month 4-12):
  Users: 1,000-10,000
  Daily Active: 500-5,000
  Requests/day: 100,000
  Storage: 100GB
  
Phase 3 (Scale - Year 2):
  Users: 10,000-100,000
  Daily Active: 5,000-50,000
  Requests/day: 1,000,000
  Storage: 1TB
```

### 7.2.2 Infrastructure Scaling Plan

**Horizontal Scaling:**
```yaml
API Servers:
  Current: 1 instance (4 workers)
  Phase 1: 1-2 instances
  Phase 2: 2-5 instances
  Phase 3: 5-20 instances (auto-scaling)
  
Celery Workers:
  Current: 1 worker
  Phase 1: 1-2 workers
  Phase 2: 2-5 workers
  Phase 3: 5-20 workers (auto-scaling)

Load Balancer:
  Algorithm: Round-robin
  Health checks: Every 30s
  Failover: Automatic
```

**Vertical Scaling:**
```yaml
Current (MVP):
  API: 2 CPU, 4GB RAM
  Database: Supabase Free (500MB)
  Redis: 256MB
  
Phase 2:
  API: 4 CPU, 8GB RAM
  Database: Supabase Pro (8GB)
  Redis: 1GB
  
Phase 3:
  API: 8 CPU, 16GB RAM
  Database: Dedicated (100GB+)
  Redis: 4GB (clustered)
```

### 7.2.3 Database Scaling Strategy

**Read Scaling:**
```yaml
Current: Single instance
Phase 2: Read replicas (1-2)
Phase 3: Read replicas (2-5) + Connection pooling

Connection Pool:
  Min connections: 5
  Max connections: 20 per instance
  Timeout: 30s
```

**Write Scaling:**
```yaml
Current: All writes to primary
Phase 2: Async writes to queue
Phase 3: Sharding by user_id hash

Sharding Strategy:
  Shard key: user_id
  Shards: 4 initially, expand to 16
  Rebalancing: Automatic with pg_shard
```

## 7.3 Database Optimization

### 7.3.1 Indexing Strategy

**Primary Indexes (Already Created):**
```sql
-- Users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Books table
CREATE INDEX idx_books_user_id ON books(user_id);
CREATE INDEX idx_books_user_status_created ON books(user_id, status, created_at DESC);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_search_vector ON books USING gin(search_vector);

-- Scans table
CREATE INDEX idx_scans_user_created ON scans(user_id, created_at DESC);
CREATE INDEX idx_scans_status ON scans(status);
```

**Additional Indexes (For Phase 2):**
```sql
-- Covering indexes for common queries
CREATE INDEX idx_books_user_list 
  ON books(user_id, status, created_at DESC) 
  INCLUDE (title, authors, rating);

-- Partial indexes for active data
CREATE INDEX idx_users_active ON users(id) 
  WHERE is_active = true;

CREATE INDEX idx_scans_pending ON scans(user_id, created_at) 
  WHERE status = 'pending';

-- Multi-column indexes for filtering
CREATE INDEX idx_books_user_category 
  ON books(user_id, categories);
```

### 7.3.2 Query Optimization

**Slow Query Detection:**
```yaml
Tool: pg_stat_statements
Threshold: Queries > 100ms
Action: Add to optimization queue

Monitoring:
  - Query execution time
  - Number of rows scanned
  - Index usage
  - Lock contention
```

**Common Query Patterns:**

```sql
-- Optimized: Use index
SELECT * FROM books 
WHERE user_id = 'uuid' 
  AND status = 'reading' 
ORDER BY created_at DESC 
LIMIT 20;

-- Avoid: Table scan
SELECT * FROM books 
WHERE lower(title) LIKE '%gatsby%';  -- Use full-text search instead

-- Better: Full-text search
SELECT * FROM books 
WHERE search_vector @@ to_tsquery('gatsby')
ORDER BY ts_rank(search_vector, to_tsquery('gatsby')) DESC;
```

**Query Caching:**
```python
# Application-level query cache
@cache(ttl=3600, key="user:{user_id}:books")
def get_user_books(user_id: str) -> List[Book]:
    return db.query(Book).filter_by(user_id=user_id).all()
```

### 7.3.3 Database Partitioning

**Table Partitioning (Phase 3):**
```sql
-- Partition scans table by date
CREATE TABLE scans_2024_01 PARTITION OF scans
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE scans_2024_02 PARTITION OF scans
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Automatic partition creation
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    partition_name := 'scans_' || to_char(partition_date, 'YYYY_MM');
    start_date := partition_date::TEXT;
    end_date := (partition_date + interval '1 month')::TEXT;
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF scans FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule via cron
SELECT cron.schedule('create-partition', '0 0 1 * *', 'SELECT create_monthly_partition()');
```

**Archival Strategy:**
```yaml
Scans older than 1 year:
  Action: Move to archive table
  Frequency: Monthly
  Access: Read-only via separate endpoint
  
Archive table:
  Name: scans_archive
  Compression: Enabled
  Indexes: Minimal (user_id, created_at only)
```

---

**Document continues in next file due to length...**

Would you like me to continue with:
- 8. Monitoring and Logging
- 9. Testing Requirements
- 10. Deployment and CI/CD
- 11. Edge Cases and Error Handling
- 12. Future Considerations
- Appendix
