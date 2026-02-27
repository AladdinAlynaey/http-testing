"""
HTTP Playground v3.0 — All 20 API Module Endpoints
100+ request types, per-user deep freeze tracking, file security
"""
import os
import json
import bleach
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, send_from_directory
from werkzeug.utils import secure_filename
from auth import require_api_key, require_ai_key, get_current_user, STANDARD_KEY_LIMIT, AI_KEY_LIMIT
from database import get_db

modules_bp = Blueprint('modules', __name__)

# ============ CONSTANTS ============
MAX_FIELD_LEN = 500
MAX_CONTENT_LEN = 5000
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json', 'xml', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAGIC_BYTES = {
    'png': [b'\x89PNG'], 'jpg': [b'\xff\xd8\xff'], 'jpeg': [b'\xff\xd8\xff'],
    'gif': [b'GIF87a', b'GIF89a'], 'pdf': [b'%PDF'],
    'json': [b'{', b'['], 'xml': [b'<?xml', b'<'],
    'txt': [], 'csv': [],
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============ HELPERS ============
def sanitize_str(val, max_len=MAX_FIELD_LEN):
    if val is None:
        return None
    return bleach.clean(str(val).strip()[:max_len], tags=[], strip=True)

def sanitize_content(val):
    return sanitize_str(val, MAX_CONTENT_LEN)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file_obj, ext):
    signatures = MAGIC_BYTES.get(ext, [])
    if not signatures:
        return True
    file_obj.seek(0)
    header = file_obj.read(16)
    file_obj.seek(0)
    return any(header.startswith(sig) for sig in signatures)

def track_modification(conn, table, record_id, action, original_data=None, hours=2):
    """Track user modification for deep freeze auto-revert"""
    user_key = g.get('api_key', request.remote_addr)
    user_id = None
    if hasattr(g, 'current_user') and g.current_user:
        user_id = g.current_user.get('id')
    expires = datetime.utcnow() + timedelta(hours=hours)
    conn.execute(
        "INSERT INTO user_modifications (table_name, record_id, action, original_data, user_key, user_id, expires_at) VALUES (?,?,?,?,?,?,?)",
        (table, record_id, action, json.dumps(original_data) if original_data else None, user_key, user_id, expires.isoformat())
    )

def freeze_notice(action):
    notices = {
        'create': 'This record will be auto-deleted in 2 hours (Deep Freeze)',
        'update': 'Changes will auto-revert in 1 hour (Deep Freeze)',
        'delete': 'Record will be auto-restored in 1 hour (Deep Freeze)',
    }
    return notices.get(action, '')


# ============ GENERIC CRUD FACTORY ============
def make_crud_routes(name, table, fields, search_fields=None, filter_fields=None):
    """Factory function to create GET/POST/PUT/DELETE routes for a module"""

    # GET all + GET by id
    @modules_bp.route(f'/api/{name}', methods=['GET'], endpoint=f'get_{name}')
    def get_all():
        conn = get_db()
        query = f"SELECT * FROM {table}"
        params = []
        conditions = []

        # Search
        search = request.args.get('search', '').strip()
        if search and search_fields:
            search_conditions = [f"{sf} LIKE ?" for sf in search_fields]
            conditions.append(f"({' OR '.join(search_conditions)})")
            params.extend([f"%{search}%" for _ in search_fields])

        # Filters
        if filter_fields:
            for ff in filter_fields:
                val = request.args.get(ff)
                if val:
                    conditions.append(f"{ff} = ?")
                    params.append(val)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"

        # Pagination
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 100)
        if page:
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"

        rows = conn.execute(query, params).fetchall()
        data = [dict(r) for r in rows]
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()

        return jsonify({
            'data': data,
            'count': len(data),
            'total': total,
            'module': name,
            'message': 'Success'
        })

    @modules_bp.route(f'/api/{name}/<int:item_id>', methods=['GET'], endpoint=f'get_{name}_by_id')
    def get_by_id(item_id):
        conn = get_db()
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'error': f'{name.title()} not found', 'id': item_id}), 404
        return jsonify({'data': dict(row), 'module': name})

    # POST (public — no auth)
    @modules_bp.route(f'/api/{name}', methods=['POST'], endpoint=f'create_{name}')
    def create():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        # Validate required fields
        cols = []
        vals = []
        for field_name, field_info in fields.items():
            val = data.get(field_name)
            if field_info.get('required') and not val:
                return jsonify({'error': f'{field_name} is required'}), 400
            if val is not None:
                if field_info.get('type') in ('text', 'content'):
                    val = sanitize_content(val) if field_info.get('type') == 'content' else sanitize_str(val)
                cols.append(field_name)
                vals.append(val)

        # Add user tracking
        cols.extend(['created_by_user', 'created_by_key'])
        vals.extend([1, g.get('api_key', request.remote_addr)])

        placeholders = ','.join(['?' for _ in vals])
        col_names = ','.join(cols)

        conn = get_db()
        cursor = conn.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", vals)
        new_id = cursor.lastrowid
        track_modification(conn, table, new_id, 'create', hours=2)
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (new_id,)).fetchone()
        conn.close()

        return jsonify({
            'message': f'{name.title()} created successfully',
            'data': dict(row),
            'deep_freeze': {'notice': freeze_notice('create'), 'expires_in': '2 hours'}
        }), 201

    # PUT (requires standard API key)
    @modules_bp.route(f'/api/{name}/<int:item_id>', methods=['PUT'], endpoint=f'update_{name}')
    @require_api_key
    def update(item_id):
        conn = get_db()
        existing = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': f'{name.title()} not found'}), 404

        data = request.get_json()
        if not data:
            conn.close()
            return jsonify({'error': 'JSON body required'}), 400

        # Save original for freeze revert
        original = dict(existing)

        updates = []
        vals = []
        for field_name in fields:
            if field_name in data:
                val = data[field_name]
                if isinstance(val, str):
                    val = sanitize_str(val)
                updates.append(f"{field_name} = ?")
                vals.append(val)

        if not updates:
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400

        vals.append(item_id)
        conn.execute(f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?", vals)
        track_modification(conn, table, item_id, 'update', original_data=original, hours=1)
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
        conn.close()

        return jsonify({
            'message': f'{name.title()} updated successfully',
            'data': dict(row),
            'deep_freeze': {'notice': freeze_notice('update'), 'reverts_in': '1 hour'}
        })

    # DELETE (requires standard API key)
    @modules_bp.route(f'/api/{name}/<int:item_id>', methods=['DELETE'], endpoint=f'delete_{name}')
    @require_api_key
    def delete(item_id):
        conn = get_db()
        existing = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': f'{name.title()} not found'}), 404

        existing_data = dict(existing)
        if existing_data.get('is_frozen'):
            conn.close()
            return jsonify({'error': 'Cannot delete frozen baseline data', 'is_frozen': True}), 403

        conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        track_modification(conn, table, item_id, 'delete', original_data=existing_data, hours=1)
        conn.commit()
        conn.close()

        return jsonify({
            'message': f'{name.title()} deleted',
            'id': item_id,
            'deep_freeze': {'notice': freeze_notice('delete'), 'restores_in': '1 hour'}
        })


# ================================================================
# REGISTER ALL 20 MODULES
# ================================================================

# 1. Books
make_crud_routes('books', 'books',
    fields={'title': {'type': 'text', 'required': True}, 'author': {'type': 'text', 'required': True},
            'isbn': {'type': 'text'}, 'genre': {'type': 'text'}, 'year': {'type': 'number'}, 'available': {'type': 'number'}},
    search_fields=['title', 'author', 'isbn'],
    filter_fields=['genre', 'year', 'available']
)

# 2. Menu
make_crud_routes('menu', 'menu_items',
    fields={'name': {'type': 'text', 'required': True}, 'description': {'type': 'content'},
            'price': {'type': 'number', 'required': True}, 'category': {'type': 'text'}, 'is_available': {'type': 'number'}},
    search_fields=['name', 'description'],
    filter_fields=['category', 'is_available']
)

# 3. Tasks
make_crud_routes('tasks', 'tasks',
    fields={'title': {'type': 'text', 'required': True}, 'description': {'type': 'content'},
            'status': {'type': 'text'}, 'priority': {'type': 'text'}, 'due_date': {'type': 'text'}, 'assigned_to': {'type': 'text'}},
    search_fields=['title', 'description', 'assigned_to'],
    filter_fields=['status', 'priority', 'assigned_to']
)

# 4. Students
make_crud_routes('students', 'students',
    fields={'name': {'type': 'text', 'required': True}, 'email': {'type': 'text'},
            'student_id': {'type': 'text'}, 'major': {'type': 'text'}, 'gpa': {'type': 'number'}, 'enrollment_year': {'type': 'number'}},
    search_fields=['name', 'email', 'student_id'],
    filter_fields=['major', 'enrollment_year']
)

# 5. Notes
make_crud_routes('notes', 'notes',
    fields={'title': {'type': 'text', 'required': True}, 'content': {'type': 'content'},
            'category': {'type': 'text'}, 'is_pinned': {'type': 'number'}},
    search_fields=['title', 'content'],
    filter_fields=['category', 'is_pinned']
)

# 6. Blog
make_crud_routes('blog', 'blog_posts',
    fields={'title': {'type': 'text', 'required': True}, 'content': {'type': 'content', 'required': True},
            'author': {'type': 'text'}, 'tags': {'type': 'text'}, 'is_published': {'type': 'number'}},
    search_fields=['title', 'content', 'author', 'tags'],
    filter_fields=['author', 'is_published']
)

# 7. Inventory
make_crud_routes('inventory', 'inventory',
    fields={'name': {'type': 'text', 'required': True}, 'sku': {'type': 'text'},
            'quantity': {'type': 'number'}, 'price': {'type': 'number'}, 'category': {'type': 'text'}, 'warehouse': {'type': 'text'}},
    search_fields=['name', 'sku'],
    filter_fields=['category', 'warehouse']
)

# Extra inventory route: low stock
@modules_bp.route('/api/inventory/low-stock', methods=['GET'])
def inventory_low_stock():
    threshold = request.args.get('threshold', 20, type=int)
    conn = get_db()
    rows = conn.execute("SELECT * FROM inventory WHERE quantity <= ? ORDER BY quantity ASC", (threshold,)).fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows), 'threshold': threshold})

# 8. Products
make_crud_routes('products', 'products',
    fields={'name': {'type': 'text', 'required': True}, 'description': {'type': 'content'},
            'price': {'type': 'number', 'required': True}, 'category': {'type': 'text'}, 'brand': {'type': 'text'},
            'rating': {'type': 'number'}, 'stock': {'type': 'number'}, 'image_url': {'type': 'text'}},
    search_fields=['name', 'description', 'brand'],
    filter_fields=['category', 'brand']
)

# Extra products route: top rated
@modules_bp.route('/api/products/top-rated', methods=['GET'])
def products_top_rated():
    limit = request.args.get('limit', 5, type=int)
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY rating DESC LIMIT ?", (min(limit, 20),)).fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

# 9. Movies
make_crud_routes('movies', 'movies',
    fields={'title': {'type': 'text', 'required': True}, 'director': {'type': 'text'},
            'genre': {'type': 'text'}, 'year': {'type': 'number'}, 'rating': {'type': 'number'},
            'runtime': {'type': 'number'}, 'language': {'type': 'text'}},
    search_fields=['title', 'director'],
    filter_fields=['genre', 'year', 'language']
)

# Extra movies route: top rated
@modules_bp.route('/api/movies/top-rated', methods=['GET'])
def movies_top_rated():
    limit = request.args.get('limit', 5, type=int)
    conn = get_db()
    rows = conn.execute("SELECT * FROM movies ORDER BY rating DESC LIMIT ?", (min(limit, 20),)).fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

# 10. Recipes
make_crud_routes('recipes', 'recipes',
    fields={'title': {'type': 'text', 'required': True}, 'description': {'type': 'content'},
            'cuisine': {'type': 'text'}, 'difficulty': {'type': 'text'}, 'prep_time': {'type': 'number'},
            'cook_time': {'type': 'number'}, 'servings': {'type': 'number'}, 'ingredients': {'type': 'content'}},
    search_fields=['title', 'description', 'cuisine', 'ingredients'],
    filter_fields=['cuisine', 'difficulty']
)

# 11. Events
make_crud_routes('events', 'events',
    fields={'title': {'type': 'text', 'required': True}, 'description': {'type': 'content'},
            'location': {'type': 'text'}, 'event_date': {'type': 'text'}, 'event_time': {'type': 'text'},
            'category': {'type': 'text'}, 'capacity': {'type': 'number'}, 'organizer': {'type': 'text'}},
    search_fields=['title', 'description', 'location', 'organizer'],
    filter_fields=['category', 'event_date']
)

# Extra events route: upcoming
@modules_bp.route('/api/events/upcoming', methods=['GET'])
def events_upcoming():
    conn = get_db()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    rows = conn.execute("SELECT * FROM events WHERE event_date >= ? ORDER BY event_date ASC", (today,)).fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

# 12. Contacts
make_crud_routes('contacts', 'contacts',
    fields={'first_name': {'type': 'text', 'required': True}, 'last_name': {'type': 'text'},
            'email': {'type': 'text'}, 'phone': {'type': 'text'}, 'company': {'type': 'text'},
            'job_title': {'type': 'text'}, 'city': {'type': 'text'}, 'country': {'type': 'text'}},
    search_fields=['first_name', 'last_name', 'email', 'company'],
    filter_fields=['company', 'country', 'city']
)

# 13. Songs / Music
make_crud_routes('songs', 'songs',
    fields={'title': {'type': 'text', 'required': True}, 'artist': {'type': 'text', 'required': True},
            'album': {'type': 'text'}, 'genre': {'type': 'text'}, 'duration': {'type': 'number'},
            'year': {'type': 'number'}, 'is_explicit': {'type': 'number'}},
    search_fields=['title', 'artist', 'album'],
    filter_fields=['genre', 'year', 'is_explicit']
)

# 14. Quotes
make_crud_routes('quotes', 'quotes',
    fields={'text': {'type': 'content', 'required': True}, 'author': {'type': 'text', 'required': True},
            'category': {'type': 'text'}, 'language': {'type': 'text'}},
    search_fields=['text', 'author'],
    filter_fields=['category', 'language']
)

# Extra quotes route: random
@modules_bp.route('/api/quotes/random', methods=['GET'])
def quotes_random():
    conn = get_db()
    row = conn.execute("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'No quotes found'}), 404
    return jsonify({'data': dict(row)})

# 15. Countries
make_crud_routes('countries', 'countries',
    fields={'name': {'type': 'text', 'required': True}, 'capital': {'type': 'text'},
            'continent': {'type': 'text'}, 'population': {'type': 'number'}, 'area_km2': {'type': 'number'},
            'currency': {'type': 'text'}, 'language': {'type': 'text'}, 'calling_code': {'type': 'text'}},
    search_fields=['name', 'capital', 'currency'],
    filter_fields=['continent', 'language']
)

# Extra countries route: by continent
@modules_bp.route('/api/countries/by-continent', methods=['GET'])
def countries_by_continent():
    conn = get_db()
    rows = conn.execute("SELECT continent, COUNT(*) as count FROM countries GROUP BY continent ORDER BY count DESC").fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows]})

# 16. Jokes
make_crud_routes('jokes', 'jokes',
    fields={'setup': {'type': 'content', 'required': True}, 'punchline': {'type': 'content', 'required': True},
            'category': {'type': 'text'}, 'rating': {'type': 'number'}},
    search_fields=['setup', 'punchline'],
    filter_fields=['category']
)

# Extra jokes route: random
@modules_bp.route('/api/jokes/random', methods=['GET'])
def jokes_random():
    conn = get_db()
    row = conn.execute("SELECT * FROM jokes ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'No jokes found'}), 404
    return jsonify({'data': dict(row)})

# 17. Vehicles
make_crud_routes('vehicles', 'vehicles',
    fields={'make': {'type': 'text', 'required': True}, 'model': {'type': 'text', 'required': True},
            'year': {'type': 'number'}, 'type': {'type': 'text'}, 'color': {'type': 'text'},
            'price': {'type': 'number'}, 'fuel_type': {'type': 'text'}, 'mileage': {'type': 'number'}},
    search_fields=['make', 'model'],
    filter_fields=['type', 'fuel_type', 'year', 'color']
)

# 18. Courses
make_crud_routes('courses', 'courses',
    fields={'title': {'type': 'text', 'required': True}, 'instructor': {'type': 'text'},
            'category': {'type': 'text'}, 'level': {'type': 'text'}, 'duration_hours': {'type': 'number'},
            'price': {'type': 'number'}, 'rating': {'type': 'number'}, 'enrolled': {'type': 'number'}},
    search_fields=['title', 'instructor', 'category'],
    filter_fields=['category', 'level']
)

# Extra courses route: free courses
@modules_bp.route('/api/courses/free', methods=['GET'])
def courses_free():
    conn = get_db()
    rows = conn.execute("SELECT * FROM courses WHERE price = 0 OR price IS NULL ORDER BY rating DESC").fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

# Extra courses route: popular
@modules_bp.route('/api/courses/popular', methods=['GET'])
def courses_popular():
    limit = request.args.get('limit', 5, type=int)
    conn = get_db()
    rows = conn.execute("SELECT * FROM courses ORDER BY enrolled DESC LIMIT ?", (min(limit, 20),)).fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

# 19. Pets
make_crud_routes('pets', 'pets',
    fields={'name': {'type': 'text', 'required': True}, 'species': {'type': 'text', 'required': True},
            'breed': {'type': 'text'}, 'age': {'type': 'number'}, 'color': {'type': 'text'},
            'weight': {'type': 'number'}, 'adopted': {'type': 'number'}, 'shelter': {'type': 'text'}},
    search_fields=['name', 'breed', 'shelter'],
    filter_fields=['species', 'adopted', 'shelter']
)

# Extra pets route: available for adoption
@modules_bp.route('/api/pets/available', methods=['GET'])
def pets_available():
    conn = get_db()
    rows = conn.execute("SELECT * FROM pets WHERE adopted = 0 ORDER BY name ASC").fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


# ================================================================
# 20. FILES MODULE (special — multipart upload)
# ================================================================
@modules_bp.route('/api/files', methods=['GET'])
def list_files():
    conn = get_db()
    rows = conn.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows), 'module': 'files'})

@modules_bp.route('/api/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'File not found'}), 404
    return jsonify({'data': dict(row), 'module': 'files'})

@modules_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided', 'hint': 'Use -F "file=@yourfile.txt" in CURL'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Empty filename'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'File type not allowed', 'allowed': list(ALLOWED_EXTENSIONS)}), 400
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)'}), 400
    ext = f.filename.rsplit('.', 1)[1].lower()
    if not validate_file_content(f, ext):
        return jsonify({'error': 'File content does not match its extension'}), 400
    safe_name = secure_filename(f.filename)[:100]
    stored = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_name}"
    f.save(os.path.join(UPLOAD_DIR, stored))
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO files (original_name, stored_name, file_type, file_size, created_by_user, created_by_key) VALUES (?,?,?,?,1,?)",
        (safe_name, stored, ext, size, request.remote_addr)
    )
    new_id = cursor.lastrowid
    track_modification(conn, 'files', new_id, 'create', hours=2)
    conn.commit()
    conn.close()
    return jsonify({'message': 'File uploaded', 'data': {'id': new_id, 'name': safe_name, 'size': size, 'type': ext},
                    'deep_freeze': {'notice': freeze_notice('create')}}), 201

@modules_bp.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(UPLOAD_DIR, row['stored_name'], download_name=row['original_name'])

@modules_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@require_api_key
def delete_file(file_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'File not found'}), 404
    if row['is_frozen']:
        conn.close()
        return jsonify({'error': 'Cannot delete frozen file'}), 403
    file_data = dict(row)
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    track_modification(conn, 'files', file_id, 'delete', original_data=file_data, hours=1)
    conn.commit()
    conn.close()
    return jsonify({'message': 'File deleted', 'id': file_id, 'deep_freeze': {'notice': freeze_notice('delete')}})


# ================================================================
# WEATHER MODULE (read-only, mock data)
# ================================================================
WEATHER_DATA = {
    'dubai': {'city': 'Dubai', 'country': 'UAE', 'temp': 38, 'humidity': 45, 'condition': 'Sunny', 'wind_speed': 15, 'uv_index': 9, 'feels_like': 42},
    'london': {'city': 'London', 'country': 'UK', 'temp': 12, 'humidity': 78, 'condition': 'Cloudy', 'wind_speed': 20, 'uv_index': 3, 'feels_like': 9},
    'tokyo': {'city': 'Tokyo', 'country': 'Japan', 'temp': 22, 'humidity': 60, 'condition': 'Partly Cloudy', 'wind_speed': 10, 'uv_index': 5, 'feels_like': 24},
    'new york': {'city': 'New York', 'country': 'USA', 'temp': 15, 'humidity': 55, 'condition': 'Clear', 'wind_speed': 18, 'uv_index': 4, 'feels_like': 13},
    'paris': {'city': 'Paris', 'country': 'France', 'temp': 14, 'humidity': 70, 'condition': 'Rainy', 'wind_speed': 22, 'uv_index': 2, 'feels_like': 11},
    'sydney': {'city': 'Sydney', 'country': 'Australia', 'temp': 25, 'humidity': 65, 'condition': 'Sunny', 'wind_speed': 12, 'uv_index': 8, 'feels_like': 27},
    'cairo': {'city': 'Cairo', 'country': 'Egypt', 'temp': 35, 'humidity': 30, 'condition': 'Hot', 'wind_speed': 8, 'uv_index': 10, 'feels_like': 37},
    'berlin': {'city': 'Berlin', 'country': 'Germany', 'temp': 10, 'humidity': 75, 'condition': 'Overcast', 'wind_speed': 25, 'uv_index': 2, 'feels_like': 6},
    'mumbai': {'city': 'Mumbai', 'country': 'India', 'temp': 32, 'humidity': 80, 'condition': 'Humid', 'wind_speed': 14, 'uv_index': 7, 'feels_like': 38},
    'toronto': {'city': 'Toronto', 'country': 'Canada', 'temp': 5, 'humidity': 60, 'condition': 'Cold', 'wind_speed': 30, 'uv_index': 1, 'feels_like': -2},
    'riyadh': {'city': 'Riyadh', 'country': 'Saudi Arabia', 'temp': 40, 'humidity': 15, 'condition': 'Very Hot', 'wind_speed': 10, 'uv_index': 11, 'feels_like': 43},
    'seoul': {'city': 'Seoul', 'country': 'South Korea', 'temp': 18, 'humidity': 50, 'condition': 'Clear', 'wind_speed': 8, 'uv_index': 4, 'feels_like': 17},
}

@modules_bp.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', '').lower().strip()
    if city:
        data = WEATHER_DATA.get(city)
        if not data:
            return jsonify({'error': 'City not found', 'available_cities': list(WEATHER_DATA.keys())}), 404
        return jsonify({'data': data, 'module': 'weather'})
    return jsonify({'data': list(WEATHER_DATA.values()), 'count': len(WEATHER_DATA), 'module': 'weather'})

@modules_bp.route('/api/weather/compare', methods=['GET'])
def compare_weather():
    c1 = request.args.get('city1', '').lower().strip()
    c2 = request.args.get('city2', '').lower().strip()
    if not c1 or not c2:
        return jsonify({'error': 'Provide city1 and city2 query parameters'}), 400
    d1 = WEATHER_DATA.get(c1)
    d2 = WEATHER_DATA.get(c2)
    if not d1 or not d2:
        missing = [c for c, d in [(c1, d1), (c2, d2)] if not d]
        return jsonify({'error': f'City not found: {", ".join(missing)}', 'available': list(WEATHER_DATA.keys())}), 404
    diff = d1['temp'] - d2['temp']
    return jsonify({
        'city1': d1, 'city2': d2,
        'comparison': {
            'temp_difference': abs(diff),
            'warmer': d1['city'] if diff > 0 else d2['city'],
            'humidity_difference': abs(d1['humidity'] - d2['humidity'])
        }
    })

@modules_bp.route('/api/weather/forecast/<city_name>', methods=['GET'])
def weather_forecast(city_name):
    """Mock 5-day forecast"""
    city = city_name.lower().strip()
    base = WEATHER_DATA.get(city)
    if not base:
        return jsonify({'error': 'City not found'}), 404
    import random
    random.seed(hash(city))
    forecast = []
    for i in range(5):
        forecast.append({
            'day': (datetime.utcnow() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
            'temp_high': base['temp'] + random.randint(-3, 5),
            'temp_low': base['temp'] - random.randint(3, 8),
            'condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy', 'Clear']),
            'humidity': base['humidity'] + random.randint(-10, 10),
        })
    return jsonify({'city': base['city'], 'forecast': forecast})


# ================================================================
# AI MODULE (requires AI API key — nai_ prefix, 3 requests max)
# ================================================================
@modules_bp.route('/api/ai/generate', methods=['POST'])
@require_ai_key
def ai_generate():
    data = request.get_json()
    if not data or not data.get('prompt'):
        return jsonify({'error': 'prompt is required'}), 400

    # Call OpenRouter API
    import requests as http_req
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI service not configured'}), 503

    try:
        resp = http_req.post('https://openrouter.ai/api/v1/chat/completions', headers={
            'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'
        }, json={
            'model': data.get('model', 'meta-llama/llama-3.3-8b-instruct:free'),
            'messages': [{'role': 'user', 'content': sanitize_content(data['prompt'])}],
            'max_tokens': min(data.get('max_tokens', 500), 1000)
        }, timeout=30)
        result = resp.json()
        text = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        return jsonify({'data': {'text': text, 'model': data.get('model', 'llama-3.3-8b'), 'tokens_used': result.get('usage', {})}, 'module': 'ai'})
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

@modules_bp.route('/api/ai/summarize', methods=['POST'])
@require_ai_key
def ai_summarize():
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({'error': 'text is required'}), 400
    import requests as http_req
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI service not configured'}), 503
    try:
        resp = http_req.post('https://openrouter.ai/api/v1/chat/completions', headers={
            'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'
        }, json={
            'model': 'meta-llama/llama-3.3-8b-instruct:free',
            'messages': [{'role': 'user', 'content': f"Summarize the following text concisely:\n\n{sanitize_content(data['text'])}"}],
            'max_tokens': 500
        }, timeout=30)
        result = resp.json()
        text = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        return jsonify({'data': {'summary': text}, 'module': 'ai'})
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

@modules_bp.route('/api/ai/chat', methods=['POST'])
@require_ai_key
def ai_chat():
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({'error': 'message is required'}), 400
    import requests as http_req
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI service not configured'}), 503
    try:
        messages = [{'role': 'system', 'content': 'You are a helpful assistant for the HTTP Playground platform. Help users learn about HTTP, REST APIs, CURL commands. Be concise.'}]
        if data.get('context'):
            messages.append({'role': 'system', 'content': f"Context: {sanitize_str(data['context'])}"})
        messages.append({'role': 'user', 'content': sanitize_content(data['message'])})
        resp = http_req.post('https://openrouter.ai/api/v1/chat/completions', headers={
            'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'
        }, json={'model': 'meta-llama/llama-3.3-8b-instruct:free', 'messages': messages, 'max_tokens': 500}, timeout=30)
        result = resp.json()
        text = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        return jsonify({'data': {'reply': text}, 'module': 'ai'})
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

@modules_bp.route('/api/ai/classify', methods=['POST'])
@require_ai_key
def ai_classify():
    data = request.get_json()
    if not data or not data.get('text') or not data.get('categories'):
        return jsonify({'error': 'text and categories are required'}), 400
    import requests as http_req
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI service not configured'}), 503
    try:
        cats = ', '.join(data['categories'][:10])
        resp = http_req.post('https://openrouter.ai/api/v1/chat/completions', headers={
            'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'
        }, json={
            'model': 'meta-llama/llama-3.3-8b-instruct:free',
            'messages': [{'role': 'user', 'content': f"Classify the following text into one of these categories: {cats}\n\nText: {sanitize_content(data['text'])}\n\nRespond with ONLY the category name."}],
            'max_tokens': 50
        }, timeout=30)
        result = resp.json()
        text = result.get('choices', [{}])[0].get('message', {}).get('content', 'Unknown').strip()
        return jsonify({'data': {'classification': text, 'categories': data['categories']}, 'module': 'ai'})
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500
