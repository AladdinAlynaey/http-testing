# 🚀 HTTP Playground — Production-Grade API Training Platform

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)
![Security](https://img.shields.io/badge/security-hardened-critical.svg)

**A production-grade educational platform for mastering HTTP requests, REST APIs, CURL commands, authentication, security, and automation — with real endpoints you can test right now.**

🌐 **Live:** [https://n8nhttp.alaadin-alynaey.site](https://n8nhttp.alaadin-alynaey.site) &nbsp;|&nbsp; 📖 **Docs:** [https://n8nhttp.alaadin-alynaey.site/docs](https://n8nhttp.alaadin-alynaey.site/docs)

</div>

---

## 🎯 What Is This?

HTTP Playground is a **hands-on learning platform** designed for students, developers, and anyone who wants to understand how real-world APIs work. Instead of just reading about HTTP methods — you actually use them against live, production-grade endpoints.

The platform features **10 fully-functional API modules**, **35+ tested CURL examples**, **role-based access control**, **AI-powered endpoints**, and enterprise-grade security — all running on a real server with real authentication.

### Why This Platform?

| Traditional Learning | HTTP Playground |
|:---|:---|
| Read about GET, POST, PUT, DELETE | Actually send GET, POST, PUT, DELETE requests |
| Theory-only API keys | Get a real API key after admin approval |
| Fake endpoints | Production server with real data |
| No security context | Learn JWT, rate limiting, CORS hands-on |
| No AI integration | AI-powered text generation, classification, validation |

---

## ⚡ Quick Start

Open your terminal and try these commands right now — **zero setup, zero auth**:

```bash
# Get all books in the library
curl https://n8nhttp.alaadin-alynaey.site/api/books

# Check the weather in Tokyo
curl "https://n8nhttp.alaadin-alynaey.site/api/weather?city=tokyo"

# Create a new task
curl -X POST https://n8nhttp.alaadin-alynaey.site/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn REST APIs","priority":"high"}'

# See your full request details (echo endpoint)
curl https://n8nhttp.alaadin-alynaey.site/api/echo

# Learn HTTP status codes
curl https://n8nhttp.alaadin-alynaey.site/api/status-codes/404

# View your request headers
curl https://n8nhttp.alaadin-alynaey.site/api/headers
```

---

## 📚 10 API Modules

| # | Module | Level | Auth Required | Endpoint |
|:--|:-------|:------|:-------------|:---------|
| 1 | 📚 **Library System** | 🟢 Beginner | None | `/api/books` |
| 2 | 🍽️ **Restaurant Menu** | 🟢 Beginner | None | `/api/menu` |
| 3 | ✅ **Task Manager** | 🟢 Beginner | None | `/api/tasks` |
| 4 | 📝 **Notes System** | 🟢 Beginner | None | `/api/notes` |
| 5 | 🌤️ **Weather API** | 🟢 Beginner | None | `/api/weather` |
| 6 | ✍️ **Blog Platform** | 🟢/🟡 | None / API Key | `/api/blog` |
| 7 | 🎓 **Student Management** | 🟡 Intermediate | API Key | `/api/students` |
| 8 | 📁 **File Manager** | 🟡 Intermediate | API Key | `/api/files` |
| 9 | 📦 **Inventory System** | 🟡 Intermediate | API Key | `/api/inventory` |
| 10 | 🤖 **AI Assistant** | 🔴 Advanced | JWT Login | `/api/ai/*` |

### Utility Endpoints
| Endpoint | Description |
|:---------|:-----------|
| `/api/echo` | Echoes back your full request details |
| `/api/headers` | Shows all your request headers |
| `/api/status-codes/:code` | Learn HTTP status codes |
| `/api/health` | Server health check |
| `/api/info` | Platform and modules info |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (Reverse Proxy)                 │
│                 SSL/TLS Termination                      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Gunicorn (4 gevent workers)                 │
│           ~2000 concurrent connections                   │
│              Managed by PM2                              │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   Flask Application                      │
│  ┌─────────────┐ ┌──────────┐ ┌───────────────────┐    │
│  │ Security    │ │ Auth     │ │ Rate Limiting     │    │
│  │ Headers     │ │ JWT/Key  │ │ Per IP/User       │    │
│  └─────────────┘ └──────────┘ └───────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │          10 API Module Blueprints                │    │
│  │  Books · Menu · Tasks · Students · Notes        │    │
│  │  Files · Blog · Inventory · Weather · AI        │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────┐ ┌──────────┐ ┌───────────────────┐    │
│  │ SQLite DB   │ │ Audit    │ │ OpenRouter AI     │    │
│  │ (WAL mode)  │ │ Logging  │ │ Integration       │    │
│  └─────────────┘ └──────────┘ └───────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Security (Enterprise-Grade)

This platform is publicly exposed and hardened against attack:

### Authentication & Authorization
- **JWT Sessions** with secure rotation (access + refresh tokens)
- **API Key Authentication** (scoped, auto-generated on approval)
- **Role-Based Access Control** (Super Admin → Admin → User → Visitor)
- **Request Fingerprinting** for session validation

### Attack Prevention
- **Rate Limiting** per IP and per endpoint (configurable)
- **Brute-Force Protection** — auto-lockout after 5 failed attempts (15 min)
- **Input Sanitization** with Bleach on all user inputs
- **Secure File Uploads** — type validation, size limits (5MB), secure naming
- **CORS Whitelisting** — strict origin control

### Security Headers
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### Audit Trail
Every sensitive action (login, registration, approval, deletion, AI request) is logged with IP, user agent, and timestamp.

---

## 👥 Role System

```
┌────────────────────────────────────────────────────┐
│  Super Admin (defined in .env only)                │
│  └── Full platform control                         │
│      └── Admin (promoted by super admin)           │
│          └── Manage users, approve/reject, keys    │
│              └── User (register → admin approves)  │
│                  └── API key, intermediate access   │
│                      └── Visitor (no login)         │
│                          └── Public endpoints only  │
└────────────────────────────────────────────────────┘
```

| Role | How to Get | Access |
|:-----|:-----------|:-------|
| **Visitor** | No login needed | Public endpoints (beginner) |
| **User** | Register → Admin approves | API key + intermediate endpoints |
| **Admin** | Super admin promotes | User management, key management |
| **Super Admin** | `.env` file only | Full platform control |

---

## 🤖 AI Integration (OpenRouter)

5 AI-powered endpoints using [OpenRouter](https://openrouter.ai):

| Endpoint | Function | Input |
|:---------|:---------|:------|
| `POST /api/ai/generate` | Text generation | `prompt` (max 2000 chars) |
| `POST /api/ai/summarize` | Summarization | `text` (20-5000 chars) |
| `POST /api/ai/classify` | Classification | `text`, optional `categories` |
| `POST /api/ai/validate` | Validation | `text`, `type` (grammar/code/email/api) |
| `POST /api/ai/chat` | Interactive chat | `message`, `context` (general/api/security/python) |

**Safety measures:** Input sanitization, output length limits, 10 req/min rate limit, full audit logging.

---

## 📊 Performance

Load testing results (200 concurrent users):

| Metric | Result |
|:-------|:-------|
| **Concurrent Users** | 200 |
| **Success Rate** | ✅ 100% |
| **Requests/sec** | 365.9 |
| **Avg Response Time** | 51.5ms |
| **P95 Response Time** | 127.8ms |
| **P99 Response Time** | 162.8ms |

**Server Configuration:**
- 4 Gunicorn workers with gevent async (2000+ concurrent connections)
- Auto-recycling workers every 10K requests
- Managed by PM2 with auto-restart on crash/reboot

---

## 🛠️ Tech Stack

| Layer | Technology |
|:------|:-----------|
| **Backend** | Python 3.12 + Flask 3.1 |
| **Server** | Gunicorn 23 (gevent workers) |
| **Database** | SQLite (WAL mode for concurrency) |
| **Auth** | PyJWT + Custom API Key System |
| **Security** | Flask-Limiter, Bleach, Flask-CORS |
| **AI** | OpenRouter API |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Process Manager** | PM2 |
| **Reverse Proxy** | Nginx |

---

## 📁 Project Structure

```
n8nhttp/
├── app.py                 # Main Flask application
├── auth.py                # JWT, API keys, RBAC decorators
├── database.py            # SQLite schema, seed data
├── modules.py             # 10 API modules (50+ endpoints)
├── load_test.py           # Concurrent load testing
├── start.sh               # Gunicorn launcher
├── ecosystem.config.js    # PM2 configuration
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (not in repo)
├── .gitignore
├── static/
│   ├── css/style.css      # Dark/light theme design system
│   └── js/app.js          # Frontend logic
└── templates/
    ├── index.html          # Landing page with module cards
    ├── login.html          # Login form
    ├── register.html       # Registration form
    ├── admin.html          # Admin dashboard
    └── docs.html           # Full documentation (35+ CURL examples)
```

---

## 🚀 Deployment

### Local Development
```bash
git clone https://github.com/YOUR_USERNAME/http-testing.git
cd http-testing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
python app.py
```

### Production (PM2 + Gunicorn)
```bash
chmod +x start.sh
pm2 start ecosystem.config.js
pm2 save
```

### Environment Variables
```ini
SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=your_secure_password
SUPER_ADMIN_EMAIL=admin@your-domain.com
JWT_SECRET_KEY=your_jwt_secret
OPENROUTER_API_KEY=your_openrouter_key
SERVER_PORT=5050
```

---

## 📖 Documentation

Full documentation available at [`/docs`](https://n8nhttp.alaadin-alynaey.site/docs):

- ✅ Platform overview & quick start
- ✅ Role system & authentication guide
- ✅ API reference for all 10 modules
- ✅ 35+ tested CURL examples (beginner → advanced)
- ✅ Error codes reference
- ✅ Rate limits documentation
- ✅ Security headers & protection measures
- ✅ n8n workflow automation examples
- ✅ AI usage guide & safety measures

---

## 🔗 n8n Integration Examples

### Auto-create tasks from Telegram
```
Telegram Trigger → HTTP Request (POST /api/tasks) → Done
```

### Monitor inventory and alert
```
Schedule (hourly) → GET /api/inventory?low_stock=true → IF count > 0 → Send Alert
```

### Blog to social media
```
Webhook → POST /api/blog → Share to Twitter/Telegram
```

---

## 📝 License

MIT License — Built by **Alaadin** | Powered by AI via [OpenRouter](https://openrouter.ai)

---

<div align="center">

**⭐ Star this repo if you found it useful!**

*Designed for students learning web development, API design, and cybersecurity.*

</div>
