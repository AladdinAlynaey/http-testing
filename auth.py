"""
Authentication & Authorization module
- JWT sessions, API key management, RBAC decorators
- Brute-force protection, request fingerprinting
- API key usage tracking (20-request limit)
"""
import jwt
import hashlib
import secrets
import time
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'fallback-secret-change-me')
JWT_ACCESS_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
JWT_REFRESH_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', 900))

SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME')
SUPER_ADMIN_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')
SUPER_ADMIN_EMAIL = os.getenv('SUPER_ADMIN_EMAIL')


def get_request_fingerprint():
    """Generate fingerprint from request characteristics"""
    parts = [
        request.remote_addr or '',
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
    ]
    return hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]


def log_audit(user_id, action, resource=None, details=None):
    try:
        db = get_db()
        db.execute(
            "INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent, details) VALUES (?,?,?,?,?,?)",
            (user_id, action, resource, request.remote_addr,
             request.headers.get('User-Agent', '')[:200], details)
        )
        db.commit()
        db.close()
    except Exception:
        pass


def is_locked_out(identifier):
    """Check if an IP/user is locked out from too many failed attempts"""
    db = get_db()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=LOCKOUT_DURATION)
    row = db.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE identifier=? AND success=0 AND attempted_at>?",
        (identifier, cutoff.isoformat())
    ).fetchone()
    db.close()
    return row[0] >= MAX_LOGIN_ATTEMPTS


def record_login_attempt(identifier, success, ip):
    db = get_db()
    db.execute(
        "INSERT INTO login_attempts (identifier, success, ip_address) VALUES (?,?,?)",
        (identifier, 1 if success else 0, ip)
    )
    if success:
        db.execute(
            "DELETE FROM login_attempts WHERE identifier=? AND success=0",
            (identifier,)
        )
    db.commit()
    db.close()


def generate_api_key():
    return 'nhk_' + secrets.token_urlsafe(32)


def create_access_token(user_id, role, username):
    payload = {
        'user_id': user_id,
        'role': role,
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=JWT_ACCESS_EXPIRES),
        'iat': datetime.now(timezone.utc),
        'type': 'access',
        'fp': get_request_fingerprint()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def create_refresh_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=JWT_REFRESH_EXPIRES),
        'iat': datetime.now(timezone.utc),
        'type': 'refresh'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """Extract user from JWT or API key"""
    # Check JWT in Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload and payload.get('type') == 'access':
            return payload

    # Check API key
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        db = get_db()
        row = db.execute(
            """SELECT ak.*, u.username, u.role, u.status FROM api_keys ak
               JOIN users u ON ak.user_id = u.id
               WHERE ak.key=? AND ak.is_active=1 AND u.status='approved'""",
            (api_key,)
        ).fetchone()
        if row:
            # Check request limit
            if row['request_count'] >= row['max_requests']:
                db.execute("UPDATE api_keys SET is_active=0 WHERE key=?", (api_key,))
                db.commit()
                db.close()
                return None  # Key exhausted

            # Increment usage counter
            db.execute(
                "UPDATE api_keys SET last_used=CURRENT_TIMESTAMP, request_count=request_count+1 WHERE key=?",
                (api_key,)
            )
            db.commit()
            remaining = row['max_requests'] - row['request_count'] - 1
            db.close()
            return {
                'user_id': row['user_id'],
                'username': row['username'],
                'role': row['role'],
                'scope': row['scope'],
                'auth_type': 'api_key',
                'api_key_id': row['id'],
                'requests_remaining': max(0, remaining),
                'max_requests': row['max_requests']
            }
        db.close()

    return None


def require_auth(f):
    """Decorator: require any valid authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            # Check if the key was exhausted
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if api_key:
                db = get_db()
                row = db.execute("SELECT request_count, max_requests, is_active FROM api_keys WHERE key=?", (api_key,)).fetchone()
                db.close()
                if row and row['request_count'] >= row['max_requests']:
                    return jsonify({
                        'error': 'API key expired — all requests used',
                        'message': f'You used {row["max_requests"]}/{row["max_requests"]} requests. Generate a new key at /api/auth/regenerate-key',
                        'requests_used': row['request_count'],
                        'max_requests': row['max_requests'],
                        'code': 429
                    }), 429
            return jsonify({'error': 'Authentication required', 'code': 401}), 401
        g.current_user = user
        response = f(*args, **kwargs)
        # Add remaining requests header for API key users
        if isinstance(response, tuple):
            resp_obj, status = response
        else:
            resp_obj, status = response, 200
        if hasattr(resp_obj, 'headers') and user.get('auth_type') == 'api_key':
            resp_obj.headers['X-API-Requests-Remaining'] = str(user.get('requests_remaining', 0))
            resp_obj.headers['X-API-Requests-Max'] = str(user.get('max_requests', 20))
        return response
    return decorated


def require_role(*roles):
    """Decorator: require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required', 'code': 401}), 401
            if user.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions', 'code': 403}), 403
            g.current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_api_key(scope='basic'):
    """Decorator: require API key with specific scope. Tracks usage and enforces 20-request limit."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                # Check if the key was exhausted
                api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
                if api_key:
                    db = get_db()
                    row = db.execute("SELECT request_count, max_requests, is_active FROM api_keys WHERE key=?", (api_key,)).fetchone()
                    db.close()
                    if row and row['request_count'] >= row['max_requests']:
                        return jsonify({
                            'error': 'API key expired — all requests used',
                            'message': f'You used {row["max_requests"]}/{row["max_requests"]} requests. Generate a new key at /api/auth/regenerate-key',
                            'requests_used': row['request_count'],
                            'max_requests': row['max_requests'],
                            'code': 429
                        }), 429
                return jsonify({
                    'error': 'API key required for this operation',
                    'message': 'Send your API key in the X-API-Key header. Register and login to get one.',
                    'code': 401
                }), 401
            g.current_user = user
            response = f(*args, **kwargs)
            # Add remaining requests header
            if isinstance(response, tuple):
                resp_obj, status = response
            else:
                resp_obj, status = response, 200
            if hasattr(resp_obj, 'headers') and user.get('auth_type') == 'api_key':
                resp_obj.headers['X-API-Requests-Remaining'] = str(user.get('requests_remaining', 0))
                resp_obj.headers['X-API-Requests-Max'] = str(user.get('max_requests', 20))
            return response
        return decorated
    return decorator
