<div align="center">

# 🚀 HTTP Playground — The Ultimate API Training Platform

### Master HTTP, REST, CURL, Authentication & AI — with 100+ live endpoints

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/v3.0-Production-6366f1?style=for-the-badge)](https://n8nhttp.alaadin-alynaey.site)
[![Status](https://img.shields.io/badge/Status-🟢_Live-22c55e?style=for-the-badge)](https://n8nhttp.alaadin-alynaey.site/api/health)

---

**🌐 [Live Demo](https://n8nhttp.alaadin-alynaey.site)** &nbsp;·&nbsp; **📖 [Documentation](https://n8nhttp.alaadin-alynaey.site/docs)** &nbsp;·&nbsp; **⭐ [Star on GitHub](https://github.com/AladdinAlynaey/http-testing)**

---

*Zero setup. No API key needed. Open your terminal and go.*

</div>

---

## ⚡ Try It in 10 Seconds

```bash
# Fetch all books
curl https://n8nhttp.alaadin-alynaey.site/api/books

# Create a movie (no auth needed)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/movies \
  -H "Content-Type: application/json" \
  -d '{"title":"Inception","director":"Christopher Nolan","genre":"Sci-Fi","year":2010,"rating":8.8}'

# Get weather in Dubai
curl "https://n8nhttp.alaadin-alynaey.site/api/weather?city=dubai"

# Ask AI to explain REST
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain REST APIs in 3 sentences"}'
```

**Every `GET` and `POST` endpoint is 100% public.** No sign-up, no tokens, no rate walls. Just `curl` and learn.

---

## 📋 Table of Contents

- [Why This Exists](#-why-this-exists)
- [Features](#-features)
- [All 22 Modules](#-all-22-modules)
- [Deep Freeze System](#-deep-freeze-system)
- [Dual API Key System](#-dual-api-key-system)
- [Security](#-security)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [CURL Cheat Sheet](#-curl-cheat-sheet)
- [Production Deployment](#-production-deployment)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [API Response Format](#-api-response-format)
- [Contributing](#-contributing)

---

## 💡 Why This Exists

Learning HTTP and APIs shouldn't require spinning up a server. **HTTP Playground** gives you:

- ✅ **100+ live endpoints** you can hit right now
- ✅ **20 real-world CRUD modules** (books, movies, recipes, pets, vehicles…)
- ✅ **AI-powered endpoints** via OpenRouter (generate text, summarize, chat, classify)
- ✅ **Self-healing data** — the Deep Freeze system auto-reverts any changes
- ✅ **Dual API keys** — standard keys for CRUD, AI keys for AI endpoints
- ✅ **Interactive module pages** with live data tables, forms, and CURL examples
- ✅ **Dark/Light themes** with premium glassmorphism UI
- ✅ **Bilingual** — full English & Arabic support with RTL

Whether you're a student learning CURL, a developer testing n8n workflows, or a teacher setting up a classroom lab — this platform was built for you.

---

## 🎯 Features

### 🧊 Deep Freeze — Self-Healing Data

Your changes are always temporary. The database auto-reverts to a clean state.

| You Do | What Happens | Auto-Revert |
|--------|-------------|-------------|
| `POST` | Record tagged as user-created | **Deleted after 2 hours** |
| `PUT` | Original state snapshot saved | **Reverted after 1 hour** |
| `DELETE` | Record soft-deleted | **Restored after 1 hour** |

> A background daemon checks every 60 seconds. Seed data (100+ records) is permanently frozen.

### 🔑 Dual API Key System

| Key Type | Purpose | How to Get |
|----------|---------|-----------|
| **Standard Key** (`nhk_...`) | PUT/DELETE on CRUD modules | Register + Admin approval |
| **AI Key** (`nhai_...`) | AI endpoints (generate, chat, summarize) | Same account, separate key |

Each key has **20 requests**. Exhausted? Regenerate with one API call.

### 📊 Interactive Module Pages

Every module at `/module/<name>` features:
- Live data table with frozen/user badges
- Create, Update, Delete forms
- Copy-paste CURL examples for every method
- Real-time JSON response viewer
- Toast notifications

### 🌐 Premium UI

- **Dark/Light mode** with smooth transitions
- **Glassmorphism** cards with accent-colored hover glow
- **Custom-styled dropdowns** (no ugly OS selects)
- **Fixed footer** with quick links
- **Responsive** — works on mobile, tablet, desktop

### 🌍 Bilingual Support

Full English & Arabic (عربي) with automatic RTL layout switching.

---

## 📦 All 22 Modules

### 🟢 Beginner — No Authentication

| # | Module | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | 📚 **Library System** | `/api/books` | Books with genre, author, year. Search & filter. 15 seed records. |
| 2 | 🍽️ **Restaurant Menu** | `/api/menu` | Menu items with categories, prices, availability. 15 seed records. |
| 3 | ✅ **Task Manager** | `/api/tasks` | Tasks with priority, status, due dates. 12 seed records. |
| 4 | 📝 **Notes** | `/api/notes` | Create, categorize, pin notes. 8 seed records. |
| 5 | ✍️ **Blog Platform** | `/api/blog` | Posts with tags and publishing workflow. 6 seed records. |
| 6 | 🛍️ **Product Store** | `/api/products` | E-commerce products with brands, ratings, stock. |
| 7 | 🎬 **Movie Database** | `/api/movies` | Movies with directors, genres, ratings, runtime. |
| 8 | 🧑‍🍳 **Recipe Book** | `/api/recipes` | Recipes with cuisine, difficulty, prep & cook times. |
| 9 | 📅 **Event Calendar** | `/api/events` | Events with dates, locations, capacity. |
| 10 | 📇 **Address Book** | `/api/contacts` | Contacts with company, job title, location. |
| 11 | 🎵 **Music Library** | `/api/songs` | Songs with artists, albums, genres, durations. |
| 12 | 💬 **Quotes** | `/api/quotes` | Inspirational quotes with random endpoint. |
| 13 | 🌍 **World Countries** | `/api/countries` | Country data with capitals, populations, currencies. |
| 14 | 😂 **Joke API** | `/api/jokes` | Programming jokes with setup/punchline. |
| 15 | 🚗 **Vehicle Market** | `/api/vehicles` | Cars with make, model, year, fuel type. |
| 16 | 🎓 **Online Courses** | `/api/courses` | Courses with instructors, ratings, enrollment. |
| 17 | 🐾 **Pet Adoption** | `/api/pets` | Pets with breeds, ages, shelters, availability. |

### 🟡 Intermediate — API Key for PUT/DELETE

| # | Module | Endpoint | Description |
|---|--------|----------|-------------|
| 18 | 🎓 **Student Management** | `/api/students` | Student records with GPA, major, enrollment year. |
| 19 | 📁 **File Manager** | `/api/files` | Secure file upload/download with magic byte validation. |
| 20 | 📦 **Inventory System** | `/api/inventory` | Stock tracking with SKUs, warehouses, pricing. |

### 🔴 Advanced — Special Access

| # | Module | Endpoint | Description |
|---|--------|----------|-------------|
| 21 | 🌤️ **Weather API** | `/api/weather` | Mock weather for 10 cities. Compare temperatures. Read-only. |
| 22 | 🤖 **AI Assistant** | `/api/ai/*` | Text generation, summarization, classification, chat via OpenRouter. AI Key required. |

---

## 🧊 Deep Freeze System

### How It Works

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

### Freeze Daemon

A background thread runs every 60 seconds:

```python
while True:
    expired = get_expired_modifications()
    for mod in expired:
        if mod.action == 'create':   delete_user_created_record(mod)
        elif mod.action == 'update': revert_to_original_snapshot(mod)
        elif mod.action == 'delete': restore_deleted_record(mod)
    time.sleep(60)
```

All 20 CRUD module tables are covered by freeze. Seed data is marked `is_frozen=1` and cannot be permanently deleted.

---

## 🔑 Dual API Key System

### Access Matrix

| Operation | Auth Required | Details |
|-----------|:------------:|---------|
| `GET` | ❌ | All GET endpoints are fully public |
| `POST` | ❌ | Create records freely (auto-deleted after 2h) |
| `PUT` | 🔑 Standard Key | `X-API-Key` header required |
| `DELETE` | 🔑 Standard Key | `X-API-Key` header required |
| AI Endpoints | 🤖 AI Key | `X-AI-Key` header required |

### Getting Your Keys

```bash
# 1. Register
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"SecurePass123!","email":"you@example.com"}'

# 2. Login (returns both keys)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"SecurePass123!"}'

# 3. Check key status
curl https://n8nhttp.alaadin-alynaey.site/api/auth/key-status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Regenerate key (20 fresh requests)
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/auth/regenerate-key \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Usage Tracking Headers

Every authenticated response includes:
```
X-API-Requests-Remaining: 15
X-API-Requests-Max: 20
```

---

## 🔒 Security

| Layer | Implementation |
|-------|---------------|
| **File Uploads** | Extension whitelist + magic byte verification + 2MB limit |
| **Input Sanitization** | `bleach.clean()` HTML stripping + length limits |
| **Rate Limiting** | 200/min general, 10/min login, 5/min registration |
| **Security Headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| **SQL Injection** | 100% parameterized queries — zero risk |
| **Account Lockout** | 5 failed attempts → temporary lock |
| **CORS** | Configurable allowed origins |
| **JWT** | Access + refresh token rotation |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   HTTP Playground v3.0                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Flask   │  │ Gunicorn │  │   PM2    │  │  Nginx   │     │
│  │  App     │──│  WSGI    │──│ Process  │──│ Reverse  │     │
│  │ (Python) │  │  Server  │  │ Manager  │  │  Proxy   │     │
│  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘     │
│       │                                                     │
│  ┌────┴─────────────────────────────────────────────┐       │
│  │                 Core Modules                     │       │
│  │                                                  │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │       │
│  │  │modules.py│  │  auth.py │  │freeze.py │        │       │
│  │  │ 20 APIs  │  │JWT + Keys│  │ Daemon   │        │       │
│  │  └──────────┘  └──────────┘  └──────────┘        │       │
│  │                                                  │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │       │
│  │  │database  │  │    AI    │  │ weather  │        │       │
│  │  │  .py     │  │OpenRouter│  │  .py     │        │       │
│  │  │ SQLite   │  │  API     │  │ 10 cities│        │       │
│  │  └──────────┘  └──────────┘  └──────────┘        │       │
│  └──────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Local Setup

```bash
# Clone
git clone https://github.com/AladdinAlynaey/http-testing.git
cd http-testing

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << 'EOF'
JWT_SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-key-here
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=your-admin-password
SUPER_ADMIN_EMAIL=admin@example.com
SERVER_PORT=5050
EOF

# Run
python3 app.py
```

App starts at `http://localhost:5050` with database auto-initialized and seeded with 100+ records across 20 tables.

---

## 📋 CURL Cheat Sheet

<details>
<summary><strong>📚 Books API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/books
curl https://n8nhttp.alaadin-alynaey.site/api/books/1
curl "https://n8nhttp.alaadin-alynaey.site/api/books?search=python"
curl "https://n8nhttp.alaadin-alynaey.site/api/books?genre=Fiction"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Clean Code","author":"Robert Martin","genre":"Technology","year":2008}'

curl -X PUT https://n8nhttp.alaadin-alynaey.site/api/books/1 \
  -H "X-API-Key: nhk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Title"}'

curl -X DELETE https://n8nhttp.alaadin-alynaey.site/api/books/1 \
  -H "X-API-Key: nhk_your_key"
```
</details>

<details>
<summary><strong>🍽️ Menu API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/menu
curl "https://n8nhttp.alaadin-alynaey.site/api/menu?category=Main Course"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/menu \
  -H "Content-Type: application/json" \
  -d '{"name":"Grilled Salmon","price":24.99,"category":"Main Course"}'
```
</details>

<details>
<summary><strong>✅ Tasks API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/tasks
curl "https://n8nhttp.alaadin-alynaey.site/api/tasks?status=pending"
curl "https://n8nhttp.alaadin-alynaey.site/api/tasks?priority=high"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn REST APIs","priority":"high","status":"pending"}'
```
</details>

<details>
<summary><strong>🛍️ Products API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/products

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Wireless Headphones","brand":"TechCo","price":79.99,"category":"Electronics"}'
```
</details>

<details>
<summary><strong>🎬 Movies API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/movies
curl "https://n8nhttp.alaadin-alynaey.site/api/movies?genre=Action"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/movies \
  -H "Content-Type: application/json" \
  -d '{"title":"Interstellar","director":"Christopher Nolan","genre":"Sci-Fi","year":2014,"rating":8.6}'
```
</details>

<details>
<summary><strong>🧑‍🍳 Recipes API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/recipes
curl "https://n8nhttp.alaadin-alynaey.site/api/recipes?cuisine=Italian"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/recipes \
  -H "Content-Type: application/json" \
  -d '{"name":"Chicken Shawarma","cuisine":"Middle Eastern","difficulty":"Medium","prep_time":30}'
```
</details>

<details>
<summary><strong>📅 Events API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/events

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/events \
  -H "Content-Type: application/json" \
  -d '{"title":"Tech Meetup","date":"2026-04-01","location":"Dubai","capacity":100}'
```
</details>

<details>
<summary><strong>📇 Contacts API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/contacts

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/contacts \
  -H "Content-Type: application/json" \
  -d '{"name":"Sara Ahmed","email":"sara@example.com","company":"TechCorp","job_title":"Engineer"}'
```
</details>

<details>
<summary><strong>🎵 Songs API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/songs

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/songs \
  -H "Content-Type: application/json" \
  -d '{"title":"Blinding Lights","artist":"The Weeknd","album":"After Hours","genre":"Pop"}'
```
</details>

<details>
<summary><strong>💬 Quotes API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/quotes

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"quote":"The only way to do great work is to love what you do.","author":"Steve Jobs"}'
```
</details>

<details>
<summary><strong>🌍 Countries API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/countries
curl "https://n8nhttp.alaadin-alynaey.site/api/countries?continent=Asia"
```
</details>

<details>
<summary><strong>😂 Jokes API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/jokes

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/jokes \
  -H "Content-Type: application/json" \
  -d '{"setup":"Why do programmers prefer dark mode?","punchline":"Because light attracts bugs!"}'
```
</details>

<details>
<summary><strong>🚗 Vehicles API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/vehicles
curl "https://n8nhttp.alaadin-alynaey.site/api/vehicles?fuel_type=Electric"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/vehicles \
  -H "Content-Type: application/json" \
  -d '{"make":"Tesla","model":"Model 3","year":2026,"color":"White","fuel_type":"Electric"}'
```
</details>

<details>
<summary><strong>🎓 Courses API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/courses

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/courses \
  -H "Content-Type: application/json" \
  -d '{"title":"REST API Mastery","instructor":"Alaadin","category":"Web Development","price":0}'
```
</details>

<details>
<summary><strong>🐾 Pets API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/pets
curl "https://n8nhttp.alaadin-alynaey.site/api/pets?available=true"

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/pets \
  -H "Content-Type: application/json" \
  -d '{"name":"Luna","species":"Cat","breed":"Persian","age":2,"shelter":"Happy Paws","available":true}'
```
</details>

<details>
<summary><strong>🌤️ Weather API</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/weather
curl "https://n8nhttp.alaadin-alynaey.site/api/weather?city=dubai"
curl "https://n8nhttp.alaadin-alynaey.site/api/weather/compare?city1=tokyo&city2=london"
```
</details>

<details>
<summary><strong>📁 File Upload</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/files

curl -X POST https://n8nhttp.alaadin-alynaey.site/api/files/upload \
  -F "file=@document.txt"

curl https://n8nhttp.alaadin-alynaey.site/api/files/download/1 -O
```
</details>

<details>
<summary><strong>🤖 AI Assistant</strong></summary>

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
</details>

<details>
<summary><strong>🛠️ Utility Endpoints</strong></summary>

```bash
curl https://n8nhttp.alaadin-alynaey.site/api/health
curl https://n8nhttp.alaadin-alynaey.site/api/info
curl https://n8nhttp.alaadin-alynaey.site/api/echo
curl https://n8nhttp.alaadin-alynaey.site/api/headers
curl https://n8nhttp.alaadin-alynaey.site/api/status-codes
```
</details>

---

## 🚢 Production Deployment

### With PM2 + Gunicorn + Nginx

```bash
# Install Gunicorn
pip install gunicorn

# PM2 ecosystem
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

pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Nginx Configuration

```nginx
server {
    server_name n8nhttp.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10+, Flask 3.0 |
| **Database** | SQLite (WAL mode, foreign keys, 20 tables) |
| **WSGI** | Gunicorn (4 workers) |
| **Process Manager** | PM2 |
| **Reverse Proxy** | Nginx |
| **AI** | OpenRouter API (GPT/Claude/Llama) |
| **Auth** | JWT (access + refresh) + Dual API Keys |
| **Security** | bleach, werkzeug, CORS, CSP, HSTS |
| **Frontend** | Vanilla HTML/CSS/JS — no frameworks |
| **i18n** | Custom EN/AR with RTL support |

---

## 📁 Project Structure

```
http-testing/
├── app.py                # Flask app, routes, middleware, security headers
├── database.py           # SQLite schema, migrations, 100+ seed records
├── auth.py               # JWT auth, dual API key system, usage tracking
├── modules.py            # 20 CRUD API modules + file upload security
├── freeze.py             # Deep Freeze daemon (auto-revert for all 20 tables)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in repo)
├── ecosystem.config.js   # PM2 configuration
├── templates/
│   ├── index.html        # Homepage with 22 module cards
│   ├── module.html       # Interactive module page template
│   ├── docs.html         # Full API documentation
│   ├── login.html        # Premium login form
│   ├── register.html     # Premium registration form
│   └── admin.html        # Admin dashboard
├── static/
│   ├── css/style.css     # Design system (dark/light, glassmorphism)
│   ├── js/
│   │   ├── app.js        # Card rendering, auth, theme, filters
│   │   ├── module-config.js  # Module field configs & CURL templates
│   │   └── i18n.js       # EN/AR translation engine
│   └── images/
└── uploads/              # File upload directory (gitignored)
```

---

## 📊 API Response Format

### Success

```json
{
  "data": [...],
  "count": 15,
  "module": "books",
  "message": "Success"
}
```

### Deep Freeze Notice (POST)

```json
{
  "message": "Book created (auto-deletes in 2 hours)",
  "data": { "id": 16, "title": "New Book" },
  "deep_freeze": {
    "notice": "This record will be auto-deleted in 2 hours",
    "expires_at": "2026-02-27T15:30:00Z"
  }
}
```

### Error

```json
{
  "error": "API key required for this operation",
  "code": 401
}
```

---

## 🤝 Contributing

Contributions welcome! This is an educational platform — improvements to documentation, new modules, and accessibility enhancements are especially valued.

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

**Built by [Alaadin](https://alaadin-alynaey.site)**

🧊 Deep Freeze keeps your data safe &nbsp;·&nbsp; 🔑 Dual API keys &nbsp;·&nbsp; 📦 22 modules &nbsp;·&nbsp; 🤖 AI-powered

**[⭐ Star this repo](https://github.com/AladdinAlynaey/http-testing)** if it helped you learn!

</div>
