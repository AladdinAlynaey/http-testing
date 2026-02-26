<div align="center">

# 🚀 HTTP Playground & API Training Platform v2.0

**A production-grade educational platform for mastering HTTP, REST APIs, CURL, authentication, and API security — with real endpoints you can test instantly.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Live-22c55e)](https://n8nhttp.alaadin-alynaey.site)
[![Version](https://img.shields.io/badge/Version-2.0.0-6366f1)](https://n8nhttp.alaadin-alynaey.site/api/health)

**🌐 Live Demo:** [https://n8nhttp.alaadin-alynaey.site](https://n8nhttp.alaadin-alynaey.site)

</div>

---

## ⚡ Try It Right Now — No Setup Required

```bash
# Get all books
curl https://n8nhttp.alaadin-alynaey.site/api/books

# Create a new book (public — no API key needed)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/books \
  -H "Content-Type: application/json" \
  -d '{"title":"My First API Book","author":"You","genre":"Technology"}'

# Check the weather in Dubai
curl "https://n8nhttp.alaadin-alynaey.site/api/weather?city=dubai"

# Compare weather between cities
curl "https://n8nhttp.alaadin-alynaey.site/api/weather/compare?city1=tokyo&city2=london"

# Search for books
curl "https://n8nhttp.alaadin-alynaey.site/api/books?search=python"

# Get platform health status
curl https://n8nhttp.alaadin-alynaey.site/api/health
```

Every `GET` and `POST` endpoint is **100% public** — no API key, no registration, no setup. Just copy, paste, and learn.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [API Modules](#-api-modules-10-modules)
- [Deep Freeze System](#-deep-freeze-system)
- [Authentication & API Keys](#-authentication--api-keys)
- [Security](#-security)
- [Quick Start](#-quick-start-guide)
- [CURL Examples](#-complete-curl-reference)
- [Deployment](#-deployment)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🎯 Features

### 🧊 Deep Freeze Data Sandbox
The platform uses a unique **Deep Freeze** system that keeps data pristine for all users:

| Operation | What Happens | Auto-Revert Time |
|-----------|-------------|-----------------|
| `POST` | Creates a new record (tagged as user-created) | **Auto-deleted after 2 hours** |
| `PUT` | Updates a record (original is snapshot-saved) | **Auto-reverted after 1 hour** |
| `DELETE` | Soft-deletes a record (marked for restoration) | **Auto-restored after 1 hour** |

- A background daemon checks every 60 seconds and reverts expired changes
- **Frozen baseline data** (seed data) is permanent and protected
- Every user's changes are isolated and temporary — the database always returns to its clean state

### 🔑 API Key Usage Tracking
Each API key has a **20-request limit** for PUT/DELETE operations:
- `X-API-Requests-Remaining` header on every authenticated response
- `X-API-Requests-Max` header shows total allowed
- Keys auto-deactivate when exhausted
- One-click key regeneration at `POST /api/auth/regenerate-key`

### 📊 Interactive Module Pages
Each of the 10 modules has its own **dedicated interactive page** at `/module/<name>`:
- **Live data table** with frozen/user-created badges
- **Create form** (public — no API key needed)
- **Update & Delete forms** with API key input
- **Copy-paste CURL examples** for every HTTP method
- **Real-time response viewer** showing JSON responses
- **Toast notifications** for success/error feedback

### 🔒 Enterprise-Grade Security
- **File upload validation**: Extension whitelist + magic byte verification + 2MB limit
- **Input sanitization**: `bleach` HTML stripping + length limits
- **Rate limiting**: 200 req/min general, 10/min login, 5/min registration
- **Security headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **SQL injection prevention**: 100% parameterized queries
- **Account lockout**: After 5 failed login attempts

### 🌐 Bilingual Support
Full **English & Arabic** support with automatic RTL layout switching.

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    HTTP Playground v2.0                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Flask   │  │ Gunicorn │  │  PM2     │  │  Nginx   │   │
│  │ App     │──│ WSGI     │──│ Process  │──│ Reverse  │   │
│  │         │  │ Server   │  │ Manager  │  │ Proxy    │   │
│  └────┬────┘  └──────────┘  └──────────┘  └──────────┘   │
│       │                                                  │
│  ┌────┴────────────────────────────────────────┐         │
│  │              Core Modules                   │         │
│  │                                             │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │         │
│  │  │ modules  │  │   auth   │  │ freeze   │   │         │
│  │  │ .py      │  │   .py    │  │ .py      │   │         │
│  │  │ 10 APIs  │  │ JWT/Keys │  │ Daemon   │   │         │
│  │  └──────────┘  └──────────┘  └──────────┘   │         │
│  │                                             │         │
│  │  ┌──────────┐  ┌──────────┐                 │         │
│  │  │database  │  │   AI     │                 │         │
│  │  │.py       │  │OpenRouter│                 │         │
│  │  │SQLite    │  │  API     │                 │         │
│  │  └──────────┘  └──────────┘                 │         │
│  └─────────────────────────────────────────────┘         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📦 API Modules (10 Modules)

### Beginner Level — No Authentication Required

| Module | Endpoint | Description |
|--------|----------|-------------|
| 📚 **Library System** | `/api/books` | Full CRUD on books. Search, filter by genre, author, year. 15 seed books. |
| 🍽️ **Restaurant Menu** | `/api/menu` | Manage menu items with categories, prices, availability. 15 seed items. |
| ✅ **Task Manager** | `/api/tasks` | Organize with priority, status, due dates, assignments. 12 seed tasks. |
| 📝 **Notes System** | `/api/notes` | Create, categorize, and pin notes. 8 seed notes. |
| ✍️ **Blog Platform** | `/api/blog` | Posts with tags, publishing workflow. 6 seed posts. |
| 🌤️ **Weather API** | `/api/weather` | Mock weather for 10 cities. Compare temperatures. Read-only. |

### Intermediate Level — API Key for PUT/DELETE

| Module | Endpoint | Description |
|--------|----------|-------------|
| 🎓 **Student Management** | `/api/students` | Student records with GPA, major, enrollment year. 10 seed students. |
| 📁 **File Manager** | `/api/files` | Secure file upload/download. Extension & magic byte validation. |
| 📦 **Inventory System** | `/api/inventory` | Track stock, SKUs, warehouses, pricing. 12 seed items. |

### Advanced Level — Login Required

| Module | Endpoint | Description |
|--------|----------|-------------|
| 🤖 **AI Assistant** | `/api/ai/*` | Text generation, summarization, classification, chat via OpenRouter. |

---

## 🧊 Deep Freeze System

### How It Works

The Deep Freeze system ensures the platform always returns to a clean state, making it safe for educational use:

```
User creates a book (POST)
  └── Record tagged: created_by_user=true, expires_at=now+2h
  └── After 2 hours → Record automatically deleted

User updates a book (PUT)  
  └── Original state snapshot saved in user_modifications table
  └── After 1 hour → Record automatically reverted to original

User deletes a book (DELETE)
  └── Record soft-deleted, snapshot saved
  └── After 1 hour → Record automatically restored
```

### Freeze Daemon Process

```python
# Background thread runs every 60 seconds
while True:
    # Find expired modifications
    expired = get_expired_modifications()
    
    for mod in expired:
        if mod.action == 'create':
            delete_user_created_record(mod)
        elif mod.action == 'update':
            revert_to_original_snapshot(mod)
        elif mod.action == 'delete':
            restore_deleted_record(mod)
    
    time.sleep(60)
```

### Frozen Baseline Data

Seed data (78+ records) is marked as `is_frozen=1` — these records are **permanent** and cannot be deleted. Superadmins can freeze additional records via `POST /api/<module>/freeze/<id>`.

---

## 🔑 Authentication & API Keys

### Access Levels

| Operation | Authentication | Details |
|-----------|---------------|---------|
| `GET` | ❌ None | All GET endpoints are fully public |
| `POST` | ❌ None | Create records freely (auto-deleted after 2h) |
| `PUT` | ✅ API Key | `X-API-Key` header required |
| `DELETE` | ✅ API Key | `X-API-Key` header required |
| AI Endpoints | ✅ Login (JWT) | Bearer token authentication |

### Getting an API Key

1. **Register** at `/register` (or via `POST /api/auth/register`)
2. **Wait for admin approval** (accounts are manually reviewed)
3. **Login** at `/login` — your API key is returned in the response
4. **Use the key** in the `X-API-Key` header for PUT/DELETE requests

### API Key Endpoints

```bash
# Check your key status
curl https://n8nhttp.alaadin-alynaey.site/api/auth/key-status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Regenerate your key (20 fresh requests)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/auth/regenerate-key \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Usage Limits

- **20 requests** per API key (PUT/DELETE operations)
- Key auto-deactivates when exhausted
- Response headers show remaining count:
  ```
  X-API-Requests-Remaining: 15
  X-API-Requests-Max: 20
  ```

---

## 🔒 Security

### File Upload Protection

| Check | Details |
|-------|---------|
| Extension Whitelist | `.txt`, `.csv`, `.json`, `.xml`, `.pdf`, `.png`, `.jpg`, `.gif` |
| Magic Byte Validation | File content verified against declared extension |
| Size Limit | Maximum 2MB per file |
| Filename Sanitization | Werkzeug `secure_filename` + length limit |

### Input Validation

- All text inputs sanitized with `bleach.clean()` (HTML tags stripped)
- Field length limits: 500 characters (standard), 5000 characters (content fields)
- 100% parameterized SQL queries — zero injection risk

### Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: [full CSP policy]
```

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.10+
- pip

### Local Setup

```bash
# Clone the repository
git clone https://github.com/AladdinAlynaey/http-testing.git
cd http-testing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
JWT_SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-key-here
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=your-admin-password
SUPER_ADMIN_EMAIL=admin@example.com
SERVER_PORT=5050
EOF

# Run the application
python3 app.py
```

The app starts at `http://localhost:5050` with the database auto-initialized and seeded with 78+ records.

### Production Deployment with PM2

```bash
# Install gunicorn
pip install gunicorn

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "n8nhttp",
    script: "venv/bin/gunicorn",
    args: "-w 4 -b 127.0.0.1:5050 app:app --timeout 120",
    cwd: "/path/to/http-testing",
    env: { PYTHONPATH: "." }
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 📋 Complete CURL Reference

### 📚 Books API

```bash
# List all books
curl https://n8nhttp.alaadin-alynaey.site/api/books

# Get single book
curl https://n8nhttp.alaadin-alynaey.site/api/books/1

# Search books by title or author
curl "https://n8nhttp.alaadin-alynaey.site/api/books?search=python"

# Filter by genre
curl "https://n8nhttp.alaadin-alynaey.site/api/books?genre=Fiction"

# Create a book (public)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Clean Code","author":"Robert Martin","genre":"Technology","year":2008}'

# Update a book (API key required)
curl -X PUT https://n8nhttp.alaadin-alynaey.site/api/books/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: nhk_your_key_here" \
  -d '{"title":"Updated Title","year":2026}'

# Delete a book (API key required)
curl -X DELETE https://n8nhttp.alaadin-alynaey.site/api/books/1 \
  -H "X-API-Key: nhk_your_key_here"
```

### 🍽️ Menu API

```bash
# All menu items
curl https://n8nhttp.alaadin-alynaey.site/api/menu

# Filter by category
curl "https://n8nhttp.alaadin-alynaey.site/api/menu?category=Main Course"

# Create menu item
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/menu \
  -H "Content-Type: application/json" \
  -d '{"name":"Grilled Salmon","price":24.99,"category":"Main Course","description":"Fresh Atlantic salmon"}'
```

### ✅ Tasks API

```bash
# All tasks
curl https://n8nhttp.alaadin-alynaey.site/api/tasks

# Filter by status
curl "https://n8nhttp.alaadin-alynaey.site/api/tasks?status=pending"

# Filter by priority
curl "https://n8nhttp.alaadin-alynaey.site/api/tasks?priority=high"

# Create a task
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn REST APIs","priority":"high","status":"pending","assigned_to":"Student"}'
```

### 🎓 Students API

```bash
# All students
curl https://n8nhttp.alaadin-alynaey.site/api/students

# Filter by major
curl "https://n8nhttp.alaadin-alynaey.site/api/students?major=Computer Science"

# Create student
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","email":"jane@uni.edu","major":"Data Science","gpa":3.8}'
```

### 📝 Notes API

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/notes

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"API Notes","content":"REST uses HTTP methods","category":"Learning"}'
```

### ✍️ Blog API

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/blog

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/blog \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Post","content":"Hello World!","author":"Me","tags":"api,learning"}'
```

### 📦 Inventory API

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/inventory

# Low stock items
curl "https://n8nhttp.alaadin-alynaey.site/api/inventory?low_stock=true"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/inventory \
  -H "Content-Type: application/json" \
  -d '{"name":"USB-C Cable","sku":"CABLE-001","quantity":200,"price":9.99,"category":"Electronics"}'
```

### 🌤️ Weather API

```bash
# All cities
curl https://n8nhttp.alaadin-alynaey.site/api/weather

# Specific city
curl "https://n8nhttp.alaadin-alynaey.site/api/weather?city=dubai"

# Compare two cities
curl "https://n8nhttp.alaadin-alynaey.site/api/weather/compare?city1=tokyo&city2=london"
```

### 📁 File Upload

```bash
# List files
curl https://n8nhttp.alaadin-alynaey.site/api/files

# Upload a file (max 2MB, allowed: txt,csv,json,xml,pdf,png,jpg,gif)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/files/upload \
  -F "file=@document.txt"

# Download a file
curl https://n8nhttp.alaadin-alynaey.site/api/files/download/1 -O
```

### 🤖 AI Assistant

```bash
# Generate text
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain REST APIs in 3 sentences"}'

# Summarize text
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/ai/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"Your long text here..."}'

# Chat
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the difference between PUT and PATCH?"}'

# Classify text
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/ai/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"Great product!","categories":["positive","negative","neutral"]}'
```

### 🛠️ Utility Endpoints

```bash
# Health check
curl https://n8nhttp.alaadin-alynaey.site/api/health

# Platform info
curl https://n8nhttp.alaadin-alynaey.site/api/info

# Echo (see your own request)
curl https://n8nhttp.alaadin-alynaey.site/api/echo

# See your headers
curl https://n8nhttp.alaadin-alynaey.site/api/headers

# HTTP status codes
curl https://n8nhttp.alaadin-alynaey.site/api/status-codes
```

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+, Flask 3.0 |
| **Database** | SQLite (WAL mode, foreign keys) |
| **WSGI Server** | Gunicorn (4 workers) |
| **Process Manager** | PM2 |
| **Reverse Proxy** | Nginx |
| **AI Provider** | OpenRouter API |
| **Auth** | JWT (access + refresh tokens) + API Keys |
| **Security** | bleach, werkzeug, CORS, CSP headers |
| **Frontend** | Vanilla HTML/CSS/JS (no frameworks) |
| **i18n** | Custom EN/AR with RTL support |

---

## 📁 Project Structure

```
http-testing/
├── app.py               # Main Flask application, routes, middleware
├── database.py          # SQLite schema, migrations, seed data (78+ records)
├── auth.py              # JWT auth, API key management, usage tracking
├── modules.py           # All 10 API module endpoints + file security
├── freeze.py            # Deep Freeze daemon (auto-revert background thread)
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
├── ecosystem.config.js  # PM2 configuration
├── templates/
│   ├── index.html       # Homepage with module cards
│   ├── module.html      # Interactive module page template
│   ├── login.html       # Login form
│   ├── register.html    # Registration form
│   ├── admin.html       # Admin dashboard
│   └── docs.html        # API documentation
├── static/
│   ├── css/
│   │   └── style.css    # Full CSS with dark/light themes
│   ├── js/
│   │   ├── app.js       # Main JavaScript (cards, auth, theme)
│   │   └── i18n.js      # Translations engine (EN/AR)
│   └── images/
│       └── http.png     # Platform favicon/logo
└── uploads/             # File upload directory (gitignored)
```

---

## 🌍 API Response Format

All endpoints return consistent JSON:

```json
{
  "data": [...],           // Array of records (GET list)
  "count": 15,             // Total record count
  "module": "books",       // Module name
  "message": "Success"     // Status message
}
```

### Error Response

```json
{
  "error": "API key required for this operation",
  "code": 401
}
```

### Deep Freeze Response (POST)

```json
{
  "message": "Book created (auto-deletes in 2 hours)",
  "data": { "id": 16, "title": "New Book", ... },
  "deep_freeze": {
    "notice": "This record will be auto-deleted in 2 hours",
    "expires_at": "2026-02-27T03:30:00Z"
  }
}
```

---

## 🤝 Contributing

Contributions welcome! This is an educational platform — improvements to documentation, new modules, and security enhancements are especially valued.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-module`)
3. Commit your changes (`git commit -m 'Add new module'`)
4. Push to the branch (`git push origin feature/new-module`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by [Alaadin](https://github.com/AladdinAlynaey) — Powered by AI via [OpenRouter](https://openrouter.ai)**

🧊 *Deep Freeze keeps your data safe* • 🔑 *20 requests per key* • 📊 *10 interactive modules*

</div>
