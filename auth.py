"""
HTTP Playground v3.0 — Authentication & Dual API Key System
Standard keys: 15 requests (PUT/DELETE on regular modules)
AI keys: 3 requests (AI endpoints only, max 1 per user)
"""
import os
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from database import get_db

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRY = timedelta(hours=24)
REFRESH_TOKEN_EXPIRY = timedelta(days=30)

STANDARD_KEY_LIMIT = 15
AI_KEY_LIMIT = 3


# ============ PASSWORD HASHING ============
def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password, stored):
    try:
        salt, hashed = stored.split(':')
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return check.hex() == hashed
    except Exception:
        return False


# ============ JWT TOKEN MANAGEMENT ============
def create_access_token(user_id, username, role):
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + ACCESS_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + REFRESH_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============ API KEY GENERATION ============
def generate_api_key(key_type='standard'):
    """Generate a prefixed API key: nhk_ for standard, nai_ for AI"""
    prefix = 'nhk_' if key_type == 'standard' else 'nai_'
    return prefix + secrets.token_hex(24)


# ============ CURRENT USER FROM JWT ============
def get_current_user():
    """Extract user from Authorization Bearer token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    payload = decode_token(token)
    if not payload or payload.get('type') != 'access':
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (payload['user_id'],)).fetchone()
    conn.close()
    if not user:
        return None
    return dict(user)


# ============ GET USER FROM API KEY ============
def get_user_from_api_key(key_type='standard'):
    """Validate API key and return user info with key data"""
    api_key = request.headers.get('X-API-Key', '')
    if not api_key:
        return None, None

    conn = get_db()
    key_row = conn.execute(
        "SELECT ak.*, u.username, u.role, u.status FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key = ? AND ak.key_type = ?",
        (api_key, key_type)
    ).fetchone()

    if not key_row:
        conn.close()
        return None, None

    key_data = dict(key_row)
    conn.close()
    return key_data, key_data


# ============ REQUIRE API KEY DECORATOR (Standard) ============
def require_api_key(f):
    """Decorator: requires a valid STANDARD API key for PUT/DELETE endpoints.
    Standard keys have 15 requests max."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'This endpoint requires a Standard API key. Include it in the X-API-Key header.',
                'how_to_get_key': '1. Register at /register  2. Login at /login  3. Your API key will be in the response',
                'key_type': 'standard',
                'prefix': 'nhk_'
            }), 401

        conn = get_db()
        key_row = conn.execute(
            "SELECT ak.*, u.username, u.role, u.status FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key = ? AND ak.key_type = 'standard'",
            (api_key,)
        ).fetchone()

        if not key_row:
            conn.close()
            return jsonify({
                'error': 'Invalid API key',
                'message': 'This key is not recognized as a valid Standard API key. Standard keys start with nhk_',
                'key_type_expected': 'standard'
            }), 401

        key_data = dict(key_row)

        if not key_data['is_active']:
            conn.close()
            return jsonify({
                'error': 'API key exhausted',
                'message': f'This key has used all {STANDARD_KEY_LIMIT} requests. Generate a new key at POST /api/auth/regenerate-key',
                'requests_used': key_data['request_count'],
                'max_requests': key_data['max_requests']
            }), 403

        if key_data['status'] != 'approved':
            conn.close()
            return jsonify({'error': 'Account not approved', 'message': 'Your account is pending admin approval.'}), 403

        if key_data['request_count'] >= key_data['max_requests']:
            conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_data['id'],))
            conn.commit()
            conn.close()
            return jsonify({
                'error': 'API key limit reached',
                'message': f'You have used all {STANDARD_KEY_LIMIT} requests. Create a new key: POST /api/auth/regenerate-key',
                'requests_used': key_data['request_count'],
                'max_requests': key_data['max_requests']
            }), 429

        # Increment usage
        conn.execute(
            "UPDATE api_keys SET request_count = request_count + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?",
            (key_data['id'],)
        )
        conn.commit()

        remaining = key_data['max_requests'] - key_data['request_count'] - 1

        g.current_user = {
            'id': key_data['user_id'],
            'username': key_data['username'],
            'role': key_data['role'],
            'key_id': key_data['id'],
            'key_type': 'standard'
        }
        g.api_key = api_key
        g.requests_remaining = remaining
        g.requests_max = key_data['max_requests']

        conn.close()

        response = f(*args, **kwargs)

        # Add tracking headers
        if hasattr(response, 'headers'):
            response.headers['X-API-Requests-Remaining'] = str(max(0, remaining))
            response.headers['X-API-Requests-Max'] = str(key_data['max_requests'])
            response.headers['X-API-Key-Type'] = 'standard'
        elif isinstance(response, tuple):
            resp_obj = response[0]
            if hasattr(resp_obj, 'headers'):
                resp_obj.headers['X-API-Requests-Remaining'] = str(max(0, remaining))
                resp_obj.headers['X-API-Requests-Max'] = str(key_data['max_requests'])
                resp_obj.headers['X-API-Key-Type'] = 'standard'

        return response
    return decorated


# ============ REQUIRE AI KEY DECORATOR ============
def require_ai_key(f):
    """Decorator: requires a valid AI API key for AI endpoints.
    AI keys have 3 requests max, one per user, no regeneration."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')

        if not api_key:
            return jsonify({
                'error': 'AI API key required',
                'message': 'AI endpoints require a separate AI API key. Include it in the X-API-Key header.',
                'how_to_get_key': '1. Register & Login  2. An AI key (nai_ prefix) is auto-generated  3. You get 3 AI requests total',
                'key_type': 'ai',
                'prefix': 'nai_',
                'limit': AI_KEY_LIMIT
            }), 401

        conn = get_db()
        key_row = conn.execute(
            "SELECT ak.*, u.username, u.role, u.status FROM api_keys ak JOIN users u ON ak.user_id = u.id WHERE ak.key = ? AND ak.key_type = 'ai'",
            (api_key,)
        ).fetchone()

        if not key_row:
            conn.close()
            return jsonify({
                'error': 'Invalid AI API key',
                'message': 'This key is not recognized as a valid AI API key. AI keys start with nai_',
                'key_type_expected': 'ai'
            }), 401

        key_data = dict(key_row)

        if not key_data['is_active']:
            conn.close()
            return jsonify({
                'error': 'AI API key exhausted',
                'message': f'Your AI key has used all {AI_KEY_LIMIT} requests. AI keys cannot be regenerated — each user gets only {AI_KEY_LIMIT} AI requests total.',
                'requests_used': key_data['request_count'],
                'max_requests': AI_KEY_LIMIT
            }), 429

        if key_data['status'] != 'approved':
            conn.close()
            return jsonify({'error': 'Account not approved'}), 403

        if key_data['request_count'] >= key_data['max_requests']:
            conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_data['id'],))
            conn.commit()
            conn.close()
            return jsonify({
                'error': 'AI request limit reached',
                'message': f'You have used all {AI_KEY_LIMIT} AI requests. AI keys cannot be regenerated.',
                'requests_used': key_data['request_count'],
                'max_requests': AI_KEY_LIMIT
            }), 429

        # Increment usage
        conn.execute(
            "UPDATE api_keys SET request_count = request_count + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?",
            (key_data['id'],)
        )
        conn.commit()

        remaining = key_data['max_requests'] - key_data['request_count'] - 1

        g.current_user = {
            'id': key_data['user_id'],
            'username': key_data['username'],
            'role': key_data['role'],
            'key_id': key_data['id'],
            'key_type': 'ai'
        }
        g.api_key = api_key
        g.requests_remaining = remaining
        g.requests_max = key_data['max_requests']

        conn.close()

        response = f(*args, **kwargs)

        if hasattr(response, 'headers'):
            response.headers['X-AI-Requests-Remaining'] = str(max(0, remaining))
            response.headers['X-AI-Requests-Max'] = str(AI_KEY_LIMIT)
            response.headers['X-API-Key-Type'] = 'ai'
        elif isinstance(response, tuple):
            resp_obj = response[0]
            if hasattr(resp_obj, 'headers'):
                resp_obj.headers['X-AI-Requests-Remaining'] = str(max(0, remaining))
                resp_obj.headers['X-AI-Requests-Max'] = str(AI_KEY_LIMIT)
                resp_obj.headers['X-API-Key-Type'] = 'ai'

        return response
    return decorated


# ============ LOGIN TRACKING ============
def track_login_attempt(identifier, success, ip):
    conn = get_db()
    conn.execute(
        "INSERT INTO login_attempts (identifier, success, ip_address) VALUES (?, ?, ?)",
        (identifier, 1 if success else 0, ip)
    )
    conn.commit()
    conn.close()

def get_failed_attempts(identifier, window_minutes=15):
    conn = get_db()
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    count = conn.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE identifier = ? AND success = 0 AND created_at > ?",
        (identifier, cutoff.isoformat())
    ).fetchone()[0]
    conn.close()
    return count

def is_locked_out(identifier, max_attempts=5):
    return get_failed_attempts(identifier) >= max_attempts


# ============ REQUEST FINGERPRINT ============
def get_request_fingerprint():
    return hashlib.md5(
        f"{request.remote_addr}:{request.headers.get('User-Agent', '')}".encode()
    ).hexdigest()[:16]


# ============ ROLE CHECKING ============
def require_role(*roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            if user['role'] not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            g.current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============ AUDIT LOGGING ============
def log_audit(user_id, action, resource=None, details=None):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource, details, ip_address) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, resource, details, request.remote_addr)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
