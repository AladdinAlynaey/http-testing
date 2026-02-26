"""
HTTP Playground & API Training Platform v2.0
Main Flask Application with Security Middleware, Deep Freeze Daemon
"""
import os
import time
import secrets
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

from database import init_db, get_db
from auth import (
    create_access_token, create_refresh_token, decode_token,
    generate_api_key, get_current_user, require_auth, require_role,
    is_locked_out, record_login_attempt, log_audit, get_request_fingerprint,
    SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, SUPER_ADMIN_EMAIL
)
from modules import modules_bp
from freeze import start_freeze_daemon

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 2097152))  # 2MB

# ============================================================
# CORS - Strict Configuration
# ============================================================
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://n8nhttp.alaadin-alynaey.site",
            "http://localhost:5050",
            "http://127.0.0.1:5050"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        "expose_headers": ["X-RateLimit-Remaining", "X-Request-Id", "X-API-Requests-Remaining", "X-API-Requests-Max"],
        "max_age": 600
    }
})

# ============================================================
# RATE LIMITING
# ============================================================
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


# ============================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://openrouter.ai"
    )
    rid = request.headers.get('X-Request-Id', secrets.token_hex(8))
    response.headers['X-Request-Id'] = rid
    return response


# ============================================================
# REQUEST LOGGING
# ============================================================
@app.before_request
def log_request():
    g.request_start = time.time()

@app.after_request
def log_response(response):
    if hasattr(g, 'request_start'):
        duration = round((time.time() - g.request_start) * 1000, 2)
        response.headers['X-Response-Time'] = f'{duration}ms'
    return response


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================
app.register_blueprint(modules_bp)


# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json(silent=True) or {}
    import bleach
    username = bleach.clean(str(data.get('username', '')).strip(), tags=[], strip=True)
    email = bleach.clean(str(data.get('email', '')).strip(), tags=[], strip=True)
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    if len(username) < 3 or len(username) > 30:
        return jsonify({'error': 'Username must be 3-30 characters'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email format'}), 400

    # Block super admin credential registration
    if username.lower() == SUPER_ADMIN_USERNAME.lower():
        return jsonify({'error': 'Username not available'}), 409

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'Username or email already registered'}), 409

    pwd_hash = generate_password_hash(password)
    db.execute(
        "INSERT INTO users (username, email, password_hash, role, status) VALUES (?,?,?,?,?)",
        (username, email, pwd_hash, 'user', 'pending')
    )
    db.commit()
    db.close()
    log_audit(None, 'register', 'auth', f'New registration: {username}')
    return jsonify({
        'message': 'Registration successful! Your account is pending admin approval.',
        'status': 'pending'
    }), 201


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    ip = request.remote_addr
    if is_locked_out(username) or is_locked_out(ip):
        return jsonify({'error': 'Account temporarily locked. Try again later.'}), 429

    # Check super admin
    if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
        record_login_attempt(username, True, ip)
        token = create_access_token(0, 'superadmin', SUPER_ADMIN_USERNAME)
        refresh = create_refresh_token(0)
        log_audit(0, 'login', 'auth', 'Super admin login')
        return jsonify({
            'message': 'Login successful',
            'access_token': token,
            'refresh_token': refresh,
            'user': {
                'id': 0,
                'username': SUPER_ADMIN_USERNAME,
                'email': SUPER_ADMIN_EMAIL,
                'role': 'superadmin',
                'status': 'approved'
            }
        })

    # Check regular user
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    db.close()

    if not user or not check_password_hash(user['password_hash'], password):
        record_login_attempt(username, False, ip)
        return jsonify({'error': 'Invalid credentials'}), 401

    if user['status'] != 'approved':
        return jsonify({'error': f'Account is {user["status"]}. Please wait for admin approval.'}), 403

    record_login_attempt(username, True, ip)
    token = create_access_token(user['id'], user['role'], user['username'])
    refresh = create_refresh_token(user['id'])
    log_audit(user['id'], 'login', 'auth')

    # Get API key
    db = get_db()
    key_row = db.execute(
        "SELECT key, request_count, max_requests FROM api_keys WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
        (user['id'],)
    ).fetchone()
    db.close()

    return jsonify({
        'message': 'Login successful',
        'access_token': token,
        'refresh_token': refresh,
        'api_key': key_row['key'] if key_row else None,
        'api_key_info': {
            'requests_used': key_row['request_count'],
            'requests_remaining': key_row['max_requests'] - key_row['request_count'],
            'max_requests': key_row['max_requests']
        } if key_row else None,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'status': user['status']
        }
    })


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json(silent=True) or {}
    token = data.get('refresh_token', '')
    payload = decode_token(token)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid refresh token'}), 401

    user_id = payload['user_id']
    if user_id == 0:
        new_token = create_access_token(0, 'superadmin', SUPER_ADMIN_USERNAME)
    else:
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        db.close()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        new_token = create_access_token(user['id'], user['role'], user['username'])

    return jsonify({'access_token': new_token})


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    user = g.current_user
    if user.get('user_id') == 0:
        return jsonify({'data': {
            'id': 0, 'username': SUPER_ADMIN_USERNAME,
            'email': SUPER_ADMIN_EMAIL, 'role': 'superadmin', 'status': 'approved'
        }})
    db = get_db()
    row = db.execute("SELECT id,username,email,role,status,created_at FROM users WHERE id=?",
                     (user['user_id'],)).fetchone()
    key_row = db.execute(
        "SELECT key,scope,request_count,max_requests,created_at,last_used FROM api_keys WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
        (user['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    data = dict(row)
    if key_row:
        kd = dict(key_row)
        kd['requests_remaining'] = kd['max_requests'] - kd['request_count']
        data['api_key'] = kd
    else:
        data['api_key'] = None
    return jsonify({'data': data})


# ============================================================
# API KEY MANAGEMENT
# ============================================================
@app.route('/api/auth/key-status', methods=['GET'])
@require_auth
def key_status():
    """Check your API key status and remaining requests"""
    user = g.current_user
    db = get_db()
    keys = db.execute(
        "SELECT id, key, request_count, max_requests, is_active, created_at, last_used FROM api_keys WHERE user_id=? ORDER BY id DESC",
        (user['user_id'],)
    ).fetchall()
    db.close()
    result = []
    for k in keys:
        kd = dict(k)
        kd['requests_remaining'] = max(0, kd['max_requests'] - kd['request_count'])
        result.append(kd)
    return jsonify({'data': result, 'count': len(result)})


@app.route('/api/auth/regenerate-key', methods=['POST'])
@require_auth
def regenerate_key():
    """Deactivate old key and generate a new one with 20 fresh requests"""
    user = g.current_user
    db = get_db()
    # Deactivate all old keys
    db.execute("UPDATE api_keys SET is_active=0 WHERE user_id=?", (user['user_id'],))
    # Generate new key
    new_key = generate_api_key()
    db.execute(
        "INSERT INTO api_keys (user_id, key, scope, request_count, max_requests) VALUES (?,?,?,0,20)",
        (user['user_id'], new_key, 'intermediate')
    )
    db.commit()
    db.close()
    log_audit(user['user_id'], 'regenerate_key', 'auth')
    return jsonify({
        'message': 'New API key generated! You have 20 fresh requests.',
        'api_key': new_key,
        'requests_remaining': 20,
        'max_requests': 20
    })


# ============================================================
# ADMIN ROUTES
# ============================================================
@app.route('/api/admin/users', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_list_users():
    db = get_db()
    status_filter = request.args.get('status')
    query = "SELECT id,username,email,role,status,created_at FROM users"
    params = []
    if status_filter:
        query += " WHERE status=?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
@require_role('admin', 'superadmin')
def admin_approve_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404
    if user['status'] == 'approved':
        db.close()
        return jsonify({'message': 'User already approved'}), 200

    db.execute("UPDATE users SET status='approved', updated_at=CURRENT_TIMESTAMP WHERE id=?", (user_id,))

    # Generate API key for approved user (20 requests)
    api_key = generate_api_key()
    db.execute(
        "INSERT INTO api_keys (user_id, key, scope, request_count, max_requests) VALUES (?,?,?,0,20)",
        (user_id, api_key, 'intermediate')
    )
    db.commit()
    db.close()
    log_audit(g.current_user.get('user_id'), 'approve_user', f'user:{user_id}')
    return jsonify({
        'message': f'User {user["username"]} approved with API key (20 requests)',
        'api_key': api_key
    })


@app.route('/api/admin/users/<int:user_id>/reject', methods=['POST'])
@require_role('admin', 'superadmin')
def admin_reject_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404
    db.execute("UPDATE users SET status='rejected', updated_at=CURRENT_TIMESTAMP WHERE id=?", (user_id,))
    db.commit()
    db.close()
    log_audit(g.current_user.get('user_id'), 'reject_user', f'user:{user_id}')
    return jsonify({'message': f'User {user["username"]} rejected'})


@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@require_role('superadmin')
def admin_change_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get('role', '')
    if new_role not in ('user', 'admin'):
        return jsonify({'error': 'Role must be user or admin'}), 400
    db = get_db()
    db.execute("UPDATE users SET role=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_role, user_id))
    db.commit()
    db.close()
    log_audit(g.current_user.get('user_id'), 'change_role', f'user:{user_id}', new_role)
    return jsonify({'message': f'Role updated to {new_role}'})


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_role('superadmin')
def admin_delete_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404
    db.execute("DELETE FROM api_keys WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    db.close()
    log_audit(g.current_user.get('user_id'), 'delete_user', f'user:{user_id}')
    return jsonify({'message': 'User deleted'})


@app.route('/api/admin/keys', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_list_keys():
    db = get_db()
    rows = db.execute(
        """SELECT ak.*, u.username FROM api_keys ak JOIN users u ON ak.user_id = u.id
           ORDER BY ak.created_at DESC"""
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        d = dict(r)
        d['requests_remaining'] = max(0, d['max_requests'] - d['request_count'])
        result.append(d)
    return jsonify({'data': result})


@app.route('/api/admin/keys/<int:key_id>/revoke', methods=['POST'])
@require_role('admin', 'superadmin')
def admin_revoke_key(key_id):
    db = get_db()
    db.execute("UPDATE api_keys SET is_active=0 WHERE id=?", (key_id,))
    db.commit()
    db.close()
    log_audit(g.current_user.get('user_id'), 'revoke_key', f'key:{key_id}')
    return jsonify({'message': 'API key revoked'})


@app.route('/api/admin/audit', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_audit_logs():
    db = get_db()
    limit = min(int(request.args.get('limit', 50)), 200)
    rows = db.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows]})


@app.route('/api/admin/stats', methods=['GET'])
@require_role('admin', 'superadmin')
def admin_stats():
    db = get_db()
    stats = {
        'total_users': db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'pending_users': db.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0],
        'approved_users': db.execute("SELECT COUNT(*) FROM users WHERE status='approved'").fetchone()[0],
        'active_keys': db.execute("SELECT COUNT(*) FROM api_keys WHERE is_active=1").fetchone()[0],
        'total_books': db.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        'total_tasks': db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
        'total_posts': db.execute("SELECT COUNT(*) FROM blog_posts").fetchone()[0],
        'total_students': db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        'total_inventory': db.execute("SELECT COUNT(*) FROM inventory").fetchone()[0],
        'pending_modifications': db.execute("SELECT COUNT(*) FROM user_modifications").fetchone()[0],
        'recent_logs': db.execute("SELECT COUNT(*) FROM audit_logs WHERE created_at > datetime('now','-24 hours')").fetchone()[0],
    }
    db.close()
    return jsonify({'data': stats})


# ============================================================
# PAGE ROUTES (serve HTML)
# ============================================================
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

# Module pages — dedicated interactive page per module
MODULE_INFO = {
    'books': {'title': 'Library System', 'icon': '📚', 'endpoint': '/api/books', 'table': 'books'},
    'menu': {'title': 'Restaurant Menu', 'icon': '🍽️', 'endpoint': '/api/menu', 'table': 'menu_items'},
    'tasks': {'title': 'Task Manager', 'icon': '✅', 'endpoint': '/api/tasks', 'table': 'tasks'},
    'students': {'title': 'Student Management', 'icon': '🎓', 'endpoint': '/api/students', 'table': 'students'},
    'notes': {'title': 'Notes System', 'icon': '📝', 'endpoint': '/api/notes', 'table': 'notes'},
    'files': {'title': 'File Manager', 'icon': '📁', 'endpoint': '/api/files', 'table': 'files'},
    'blog': {'title': 'Blog Platform', 'icon': '✍️', 'endpoint': '/api/blog', 'table': 'blog_posts'},
    'inventory': {'title': 'Inventory System', 'icon': '📦', 'endpoint': '/api/inventory', 'table': 'inventory'},
    'weather': {'title': 'Weather API', 'icon': '🌤️', 'endpoint': '/api/weather', 'table': None},
    'ai': {'title': 'AI Assistant', 'icon': '🤖', 'endpoint': '/api/ai', 'table': None},
}

@app.route('/module/<name>')
def module_page(name):
    if name not in MODULE_INFO:
        return render_template('index.html'), 404
    info = MODULE_INFO[name]
    return render_template('module.html', module_name=name, module=info)


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found', 'code': 404}), 404
    return render_template('index.html'), 404

@app.errorhandler(429)
def rate_limited(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please slow down.',
        'code': 429
    }), 429

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum 2MB allowed.', 'code': 413}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error', 'code': 500}), 500


# ============================================================
# INITIALIZE
# ============================================================
init_db()
start_freeze_daemon()

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False)
