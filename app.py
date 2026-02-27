"""
HTTP Playground v3.0 — Main Application
20 modules, dual API keys, Deep Freeze daemon, per-user isolation
"""
import os
import threading
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from database import init_db, get_db
from auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, generate_api_key, get_current_user, require_role,
    track_login_attempt, is_locked_out, log_audit,
    STANDARD_KEY_LIMIT, AI_KEY_LIMIT
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=[
    "X-API-Requests-Remaining", "X-API-Requests-Max", "X-API-Key-Type",
    "X-AI-Requests-Remaining", "X-AI-Requests-Max"
])

# ============ RATE LIMITING ============
from collections import defaultdict
import time

rate_limits = defaultdict(list)

def rate_limit(max_calls, window_seconds):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = f"{request.remote_addr}:{f.__name__}"
            now = time.time()
            rate_limits[key] = [t for t in rate_limits[key] if now - t < window_seconds]
            if len(rate_limits[key]) >= max_calls:
                return jsonify({'error': 'Rate limit exceeded', 'retry_after': window_seconds}), 429
            rate_limits[key].append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============ SECURITY HEADERS ============
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# ============ REQUEST LOGGING ============
@app.before_request
def log_request():
    g.request_start = datetime.utcnow()


# ============ REGISTER MODULES ============
from modules import modules_bp
app.register_blueprint(modules_bp)


# ============ AUTH ROUTES ============
@app.route('/api/auth/register', methods=['POST'])
@rate_limit(5, 60)
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'username, email, and password are required'}), 400
    if len(username) < 3 or len(username) > 50:
        return jsonify({'error': 'Username must be 3-50 characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 409

    pw_hash = hash_password(password)
    conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, pw_hash))
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Registration successful! Your account is pending admin approval.',
        'status': 'pending',
        'next_steps': 'An admin will review and approve your account. Once approved, login to get your API keys.'
    }), 201


@app.route('/api/auth/login', methods=['POST'])
@rate_limit(10, 60)
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    if is_locked_out(username):
        return jsonify({'error': 'Account locked due to too many failed attempts. Try again in 15 minutes.'}), 423

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user or not verify_password(password, user['password_hash']):
        track_login_attempt(username, False, request.remote_addr)
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401

    if user['status'] != 'approved':
        conn.close()
        return jsonify({'error': 'Account not approved yet', 'status': user['status']}), 403

    track_login_attempt(username, True, request.remote_addr)

    # Generate/fetch both API keys
    standard_key = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? AND key_type = 'standard' AND is_active = 1",
        (user['id'],)
    ).fetchone()

    if not standard_key:
        new_key = generate_api_key('standard')
        conn.execute(
            "INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'standard', ?)",
            (user['id'], new_key, STANDARD_KEY_LIMIT)
        )
        standard_key_str = new_key
        standard_remaining = STANDARD_KEY_LIMIT
    else:
        standard_key_str = standard_key['key']
        standard_remaining = standard_key['max_requests'] - standard_key['request_count']

    ai_key = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? AND key_type = 'ai'",
        (user['id'],)
    ).fetchone()

    if not ai_key:
        new_ai_key = generate_api_key('ai')
        conn.execute(
            "INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'ai', ?)",
            (user['id'], new_ai_key, AI_KEY_LIMIT)
        )
        ai_key_str = new_ai_key
        ai_remaining = AI_KEY_LIMIT
    else:
        ai_key_str = ai_key['key']
        ai_remaining = max(0, ai_key['max_requests'] - ai_key['request_count'])

    conn.commit()
    conn.close()

    access_token = create_access_token(user['id'], user['username'], user['role'])
    refresh_token = create_refresh_token(user['id'])

    log_audit(user['id'], 'login', 'auth', f'IP: {request.remote_addr}')

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {'id': user['id'], 'username': user['username'], 'role': user['role']},
        'api_keys': {
            'standard': {
                'key': standard_key_str,
                'type': 'standard',
                'prefix': 'nhk_',
                'requests_remaining': standard_remaining,
                'max_requests': STANDARD_KEY_LIMIT,
                'usage': 'For PUT and DELETE on all modules (except AI)',
                'regenerable': True
            },
            'ai': {
                'key': ai_key_str,
                'type': 'ai',
                'prefix': 'nai_',
                'requests_remaining': ai_remaining,
                'max_requests': AI_KEY_LIMIT,
                'usage': 'For AI endpoints only (generate, summarize, chat, classify)',
                'regenerable': False,
                'note': f'You get exactly {AI_KEY_LIMIT} AI requests total. No regeneration.'
            }
        }
    })


@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'refresh_token required'}), 400

    payload = decode_token(data['refresh_token'])
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (payload['user_id'],)).fetchone()
    conn.close()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    access_token = create_access_token(user['id'], user['username'], user['role'])
    return jsonify({'access_token': access_token})


@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    keys = conn.execute("SELECT key, key_type, request_count, max_requests, is_active FROM api_keys WHERE user_id = ?", (user['id'],)).fetchall()
    conn.close()

    return jsonify({
        'user': {'id': user['id'], 'username': user['username'], 'email': user['email'], 'role': user['role']},
        'api_keys': [dict(k) for k in keys]
    })


# ============ KEY MANAGEMENT ============
@app.route('/api/auth/key-status', methods=['GET'])
def key_status():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required (Bearer token)'}), 401

    conn = get_db()
    keys = conn.execute("SELECT key, key_type, request_count, max_requests, is_active, created_at, last_used FROM api_keys WHERE user_id = ?", (user['id'],)).fetchall()
    conn.close()

    result = {'standard': None, 'ai': None}
    for k in keys:
        kd = dict(k)
        kd['requests_remaining'] = max(0, kd['max_requests'] - kd['request_count'])
        if kd['key_type'] == 'standard' and kd['is_active']:
            result['standard'] = kd
        elif kd['key_type'] == 'ai':
            result['ai'] = kd

    return jsonify({'api_keys': result})


@app.route('/api/auth/regenerate-key', methods=['POST'])
def regenerate_standard_key():
    """Regenerate STANDARD API key only. AI keys cannot be regenerated."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required (Bearer token)'}), 401

    conn = get_db()
    # Deactivate all existing standard keys
    conn.execute("UPDATE api_keys SET is_active = 0 WHERE user_id = ? AND key_type = 'standard'", (user['id'],))
    # Create new standard key
    new_key = generate_api_key('standard')
    conn.execute(
        "INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'standard', ?)",
        (user['id'], new_key, STANDARD_KEY_LIMIT)
    )
    conn.commit()
    conn.close()

    log_audit(user['id'], 'regenerate_standard_key', 'auth')

    return jsonify({
        'message': 'New standard API key generated',
        'standard_key': {
            'key': new_key,
            'type': 'standard',
            'prefix': 'nhk_',
            'requests_remaining': STANDARD_KEY_LIMIT,
            'max_requests': STANDARD_KEY_LIMIT
        },
        'note': 'Your old standard key has been deactivated. AI key is not affected.'
    })


# ============ ADMIN ROUTES ============
@app.route('/api/admin/users', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_users():
    conn = get_db()
    users = conn.execute("SELECT id, username, email, role, status, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({'data': [dict(u) for u in users]})

@app.route('/api/admin/approve/<int:user_id>', methods=['POST'])
@require_role('admin', 'superadmin')
def approve_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    conn.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))

    # Auto-generate both keys for approved user
    existing_standard = conn.execute("SELECT id FROM api_keys WHERE user_id = ? AND key_type = 'standard' AND is_active = 1", (user_id,)).fetchone()
    if not existing_standard:
        conn.execute("INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'standard', ?)",
                     (user_id, generate_api_key('standard'), STANDARD_KEY_LIMIT))

    existing_ai = conn.execute("SELECT id FROM api_keys WHERE user_id = ? AND key_type = 'ai'", (user_id,)).fetchone()
    if not existing_ai:
        conn.execute("INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'ai', ?)",
                     (user_id, generate_api_key('ai'), AI_KEY_LIMIT))

    conn.commit()
    conn.close()
    log_audit(g.current_user['id'], 'approve_user', 'admin', f'Approved user {user_id}')
    return jsonify({'message': f'User {user["username"]} approved with both standard and AI API keys'})

@app.route('/api/admin/reject/<int:user_id>', methods=['POST'])
@require_role('admin', 'superadmin')
def reject_user(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User rejected'})

@app.route('/api/admin/stats', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_stats():
    conn = get_db()
    stats = {
        'users': {
            'total': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            'approved': conn.execute("SELECT COUNT(*) FROM users WHERE status = 'approved'").fetchone()[0],
            'pending': conn.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'").fetchone()[0],
        },
        'api_keys': {
            'standard_active': conn.execute("SELECT COUNT(*) FROM api_keys WHERE key_type = 'standard' AND is_active = 1").fetchone()[0],
            'ai_active': conn.execute("SELECT COUNT(*) FROM api_keys WHERE key_type = 'ai' AND is_active = 1").fetchone()[0],
            'total_standard_requests': conn.execute("SELECT COALESCE(SUM(request_count),0) FROM api_keys WHERE key_type = 'standard'").fetchone()[0],
            'total_ai_requests': conn.execute("SELECT COALESCE(SUM(request_count),0) FROM api_keys WHERE key_type = 'ai'").fetchone()[0],
        },
        'deep_freeze': {
            'pending_modifications': conn.execute("SELECT COUNT(*) FROM user_modifications WHERE expires_at > datetime('now')").fetchone()[0],
        },
        'modules': {}
    }
    tables = ['books','menu_items','tasks','students','notes','files','blog_posts','inventory',
              'products','movies','recipes','events','contacts','songs','quotes','countries',
              'jokes','vehicles','courses','pets']
    for t in tables:
        try:
            stats['modules'][t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except:
            stats['modules'][t] = 0
    conn.close()
    return jsonify(stats)


# ============ MODULE PAGES ============
MODULE_INFO = {
    'books': {'title': 'Library System', 'icon': '📚', 'endpoint': '/api/books', 'table': 'books'},
    'menu': {'title': 'Restaurant Menu', 'icon': '🍽️', 'endpoint': '/api/menu', 'table': 'menu_items'},
    'tasks': {'title': 'Task Manager', 'icon': '✅', 'endpoint': '/api/tasks', 'table': 'tasks'},
    'students': {'title': 'Student Management', 'icon': '🎓', 'endpoint': '/api/students', 'table': 'students'},
    'notes': {'title': 'Notes System', 'icon': '📝', 'endpoint': '/api/notes', 'table': 'notes'},
    'files': {'title': 'File Manager', 'icon': '📁', 'endpoint': '/api/files', 'table': 'files'},
    'blog': {'title': 'Blog Platform', 'icon': '✍️', 'endpoint': '/api/blog', 'table': 'blog_posts'},
    'inventory': {'title': 'Inventory System', 'icon': '📦', 'endpoint': '/api/inventory', 'table': 'inventory'},
    'products': {'title': 'Product Store', 'icon': '🛍️', 'endpoint': '/api/products', 'table': 'products'},
    'movies': {'title': 'Movie Database', 'icon': '🎬', 'endpoint': '/api/movies', 'table': 'movies'},
    'recipes': {'title': 'Recipe Book', 'icon': '🧑‍🍳', 'endpoint': '/api/recipes', 'table': 'recipes'},
    'events': {'title': 'Event Calendar', 'icon': '📅', 'endpoint': '/api/events', 'table': 'events'},
    'contacts': {'title': 'Address Book', 'icon': '📇', 'endpoint': '/api/contacts', 'table': 'contacts'},
    'songs': {'title': 'Music Library', 'icon': '🎵', 'endpoint': '/api/songs', 'table': 'songs'},
    'quotes': {'title': 'Quotes Collection', 'icon': '💬', 'endpoint': '/api/quotes', 'table': 'quotes'},
    'countries': {'title': 'World Countries', 'icon': '🌍', 'endpoint': '/api/countries', 'table': 'countries'},
    'jokes': {'title': 'Joke API', 'icon': '😂', 'endpoint': '/api/jokes', 'table': 'jokes'},
    'vehicles': {'title': 'Vehicle Market', 'icon': '🚗', 'endpoint': '/api/vehicles', 'table': 'vehicles'},
    'courses': {'title': 'Online Courses', 'icon': '🎓', 'endpoint': '/api/courses', 'table': 'courses'},
    'pets': {'title': 'Pet Adoption', 'icon': '🐾', 'endpoint': '/api/pets', 'table': 'pets'},
    'weather': {'title': 'Weather API', 'icon': '🌤️', 'endpoint': '/api/weather', 'table': None},
    'ai': {'title': 'AI Assistant', 'icon': '🤖', 'endpoint': '/api/ai', 'table': None},
}

@app.route('/module/<name>')
def module_page(name):
    if name not in MODULE_INFO:
        return render_template('index.html'), 404
    info = MODULE_INFO[name]
    return render_template('module.html', module_name=name, module=info)


# ============ UTILITY API ENDPOINTS ============
@app.route('/api/health', methods=['GET'])
def health():
    conn = get_db()
    module_counts = {}
    for name, info in MODULE_INFO.items():
        if info['table']:
            try:
                module_counts[name] = conn.execute(f"SELECT COUNT(*) FROM {info['table']}").fetchone()[0]
            except:
                module_counts[name] = 0
    conn.close()
    return jsonify({
        'status': 'healthy',
        'version': '3.0.0',
        'modules': 20,
        'total_endpoints': '100+',
        'module_records': module_counts,
        'features': ['deep_freeze', 'dual_api_keys', 'per_user_isolation', 'file_security', 'ai_assistant'],
        'api_key_system': {
            'standard': {'prefix': 'nhk_', 'limit': STANDARD_KEY_LIMIT, 'regenerable': True},
            'ai': {'prefix': 'nai_', 'limit': AI_KEY_LIMIT, 'regenerable': False}
        }
    })

@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'HTTP Playground',
        'version': '3.0.0',
        'description': 'Production-grade educational API platform with 20 modules and 100+ endpoints',
        'modules': list(MODULE_INFO.keys()),
        'total_modules': len(MODULE_INFO),
        'auth': {
            'GET': 'Public — no authentication',
            'POST': 'Public — no authentication (Deep Freeze: auto-deleted in 2h)',
            'PUT': 'Standard API key required (nhk_ prefix, 15 requests)',
            'DELETE': 'Standard API key required (nhk_ prefix, 15 requests)',
            'AI': 'AI API key required (nai_ prefix, 3 requests total, no regeneration)'
        },
        'deep_freeze': {
            'POST': 'Auto-deleted in 2 hours',
            'PUT': 'Auto-reverted in 1 hour',
            'DELETE': 'Auto-restored in 1 hour'
        }
    })

@app.route('/api/echo', methods=['GET', 'POST', 'PUT', 'DELETE'])
def echo():
    return jsonify({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'query_params': dict(request.args),
        'body': request.get_json(silent=True),
        'ip': request.remote_addr,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/headers', methods=['GET'])
def show_headers():
    return jsonify({'headers': dict(request.headers), 'ip': request.remote_addr})

@app.route('/api/status-codes', methods=['GET'])
def status_codes():
    codes = {
        '200': 'OK — Request succeeded',
        '201': 'Created — New resource created',
        '204': 'No Content — Success, no response body',
        '400': 'Bad Request — Invalid input',
        '401': 'Unauthorized — Authentication required',
        '403': 'Forbidden — Insufficient permissions',
        '404': 'Not Found — Resource does not exist',
        '405': 'Method Not Allowed',
        '409': 'Conflict — Resource already exists',
        '429': 'Too Many Requests — Rate limit exceeded',
        '500': 'Internal Server Error'
    }
    return jsonify({'status_codes': codes})

@app.route('/api/status-codes/<int:code>', methods=['GET'])
def return_status_code(code):
    """Return a specific HTTP status code for testing"""
    if code < 100 or code > 599:
        return jsonify({'error': 'Invalid status code'}), 400
    return jsonify({'status_code': code, 'message': f'You requested HTTP {code}'}), code


# ============ PAGE ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/docs')
def docs_page():
    return render_template('docs.html')


# ============ ERROR HANDLERS ============
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404
    return render_template('index.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed', 'method': request.method, 'path': request.path}), 405

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Request too large (max 2MB)'}), 413

@app.errorhandler(429)
def rate_limited(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============ DEEP FREEZE DAEMON ============
def start_freeze_daemon():
    from freeze import freeze_cleanup
    t = threading.Thread(target=freeze_cleanup, daemon=True)
    t.start()
    print("🧊 Deep Freeze daemon started")


# ============ INIT & RUN ============
def create_superadmin():
    """Create superadmin from env vars if not exists"""
    username = os.getenv('SUPER_ADMIN_USERNAME')
    password = os.getenv('SUPER_ADMIN_PASSWORD')
    email = os.getenv('SUPER_ADMIN_EMAIL')
    if not username or not password:
        return
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not existing:
        pw_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, 'superadmin', 'approved')",
            (username, email or f'{username}@admin.local', pw_hash)
        )
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
        conn.execute("INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'standard', ?)",
                     (user_id, generate_api_key('standard'), 9999))
        conn.execute("INSERT INTO api_keys (user_id, key, key_type, max_requests) VALUES (?, ?, 'ai', ?)",
                     (user_id, generate_api_key('ai'), 9999))
        conn.commit()
    conn.close()


init_db()
create_superadmin()
start_freeze_daemon()

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False)
