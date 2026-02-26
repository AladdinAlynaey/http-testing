"""
Application Modules - 10 CRUD modules with deep freeze and security
- GET/POST: Public (no auth)
- PUT/DELETE: Require API key (tracks usage, 20-req limit)
- Deep freeze: tracks user modifications for auto-revert
"""
import os
import uuid
import json
import requests
import bleach
from flask import Blueprint, request, jsonify, send_from_directory, g
from werkzeug.utils import secure_filename
from database import get_db
from auth import require_auth, require_api_key, require_role, get_current_user, log_audit
from freeze import track_modification, get_record_snapshot
from dotenv import load_dotenv

load_dotenv()

modules_bp = Blueprint('modules', __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Security: allowed file extensions and max size
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json', 'xml', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Magic bytes for file type validation
MAGIC_BYTES = {
    'png': b'\x89PNG',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff',
    'gif': b'GIF8',
    'pdf': b'%PDF',
}

# Input length limits
MAX_TITLE_LEN = 500
MAX_CONTENT_LEN = 5000
MAX_FIELD_LEN = 500


def sanitize_str(val, max_len=MAX_FIELD_LEN):
    """Sanitize and limit string input"""
    if val is None:
        return None
    return bleach.clean(str(val).strip()[:max_len], tags=[], strip=True)


def sanitize_content(val, max_len=MAX_CONTENT_LEN):
    """Sanitize longer content fields"""
    if val is None:
        return None
    return bleach.clean(str(val).strip()[:max_len], tags=[], strip=True)


def get_user_context():
    """Get user_id and api_key_id from current request context (if authenticated)"""
    user = getattr(g, 'current_user', None)
    if user:
        return user.get('user_id'), user.get('api_key_id')
    return None, None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_content(file_obj, extension):
    """Validate file content matches its extension using magic bytes"""
    if extension in MAGIC_BYTES:
        header = file_obj.read(8)
        file_obj.seek(0)
        if not header.startswith(MAGIC_BYTES[extension]):
            return False
    return True


# ==============================================================
# 1. LIBRARY (Books) — /api/books
# ==============================================================

@modules_bp.route('/api/books', methods=['GET'])
def get_books():
    db = get_db()
    search = request.args.get('search', '')
    genre = request.args.get('genre', '')
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR author LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if genre:
        query += " AND genre = ?"
        params.append(genre)
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json(silent=True) or {}
    title = sanitize_str(data.get('title'))
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO books (title,author,isbn,genre,year,available,is_frozen,created_by_user) VALUES (?,?,?,?,?,?,0,?)",
        (title, sanitize_str(data.get('author', 'Unknown')),
         sanitize_str(data.get('isbn')), sanitize_str(data.get('genre')),
         data.get('year'), data.get('available', 1), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    # Track for deep freeze auto-delete (2h)
    track_modification('books', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'title': title}, 'message': 'Book created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/books/<int:book_id>', methods=['PUT'])
@require_api_key()
def update_book(book_id):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Book not found'}), 404
    # Snapshot for deep freeze revert
    snapshot = get_record_snapshot('books', book_id)
    data = request.get_json(silent=True) or {}
    updates = []
    values = []
    for col in ['title', 'author', 'isbn', 'genre']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]))
    for col in ['year', 'available']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(data[col])
    if not updates:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(book_id)
    db.execute(f"UPDATE books SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('books', book_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Book updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/books/<int:book_id>', methods=['DELETE'])
@require_api_key()
def delete_book(book_id):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Book not found'}), 404
    snapshot = get_record_snapshot('books', book_id)
    is_frozen = row['is_frozen']
    if is_frozen:
        # Don't actually delete frozen data, just hide it
        db.execute("DELETE FROM books WHERE id=?", (book_id,))
        db.commit()
        db.close()
        user_id, key_id = get_user_context()
        track_modification('books', book_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Book deleted (auto-restores in 1 hour)'})
    else:
        db.execute("DELETE FROM books WHERE id=?", (book_id,))
        db.commit()
        db.close()
        return jsonify({'message': 'Book deleted'})


# ==============================================================
# 2. RESTAURANT MENU — /api/menu
# ==============================================================

@modules_bp.route('/api/menu', methods=['GET'])
def get_menu():
    db = get_db()
    category = request.args.get('category', '')
    query = "SELECT * FROM menu_items WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Menu item not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/menu', methods=['POST'])
def create_menu_item():
    data = request.get_json(silent=True) or {}
    name = sanitize_str(data.get('name'))
    price = data.get('price')
    category = sanitize_str(data.get('category'))
    if not name or price is None or not category:
        return jsonify({'error': 'Name, price, and category are required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO menu_items (name,description,price,category,is_available,is_frozen,created_by_user) VALUES (?,?,?,?,?,0,?)",
        (name, sanitize_content(data.get('description')), float(price), category,
         data.get('is_available', 1), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('menu_items', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'name': name}, 'message': 'Menu item created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/menu/<int:item_id>', methods=['PUT'])
@require_api_key()
def update_menu_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Menu item not found'}), 404
    snapshot = get_record_snapshot('menu_items', item_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['name', 'description', 'category']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]) if col != 'description' else sanitize_content(data[col]))
    for col in ['price', 'is_available']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(data[col])
    if not updates:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(item_id)
    db.execute(f"UPDATE menu_items SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('menu_items', item_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Menu item updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/menu/<int:item_id>', methods=['DELETE'])
@require_api_key()
def delete_menu_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Menu item not found'}), 404
    snapshot = get_record_snapshot('menu_items', item_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('menu_items', item_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Menu item deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Menu item deleted'})


# ==============================================================
# 3. TASK MANAGER — /api/tasks
# ==============================================================

@modules_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    db = get_db()
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    title = sanitize_str(data.get('title'))
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO tasks (title,description,status,priority,due_date,assigned_to,is_frozen,created_by_user) VALUES (?,?,?,?,?,?,0,?)",
        (title, sanitize_content(data.get('description')),
         sanitize_str(data.get('status', 'pending')), sanitize_str(data.get('priority', 'medium')),
         sanitize_str(data.get('due_date')), sanitize_str(data.get('assigned_to')), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('tasks', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'title': title}, 'message': 'Task created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@require_api_key()
def update_task(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Task not found'}), 404
    snapshot = get_record_snapshot('tasks', task_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]) if col != 'description' else sanitize_content(data[col]))
    if not updates:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(task_id)
    db.execute(f"UPDATE tasks SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('tasks', task_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Task updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@require_api_key()
def delete_task(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Task not found'}), 404
    snapshot = get_record_snapshot('tasks', task_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('tasks', task_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Task deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Task deleted'})


# ==============================================================
# 4. STUDENT MANAGEMENT — /api/students
# ==============================================================

@modules_bp.route('/api/students', methods=['GET'])
def get_students():
    db = get_db()
    major = request.args.get('major', '')
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if major:
        query += " AND major LIKE ?"
        params.append(f'%{major}%')
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/students', methods=['POST'])
def create_student():
    data = request.get_json(silent=True) or {}
    name = sanitize_str(data.get('name'))
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO students (name,email,student_id,major,gpa,enrollment_year,is_frozen,created_by_user) VALUES (?,?,?,?,?,?,0,?)",
        (name, sanitize_str(data.get('email')),
         sanitize_str(data.get('student_id', f'STU{uuid.uuid4().hex[:4].upper()}')),
         sanitize_str(data.get('major')), data.get('gpa'), data.get('enrollment_year'), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('students', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'name': name}, 'message': 'Student created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/students/<int:student_id>', methods=['PUT'])
@require_api_key()
def update_student(student_id):
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    snapshot = get_record_snapshot('students', student_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['name', 'email', 'student_id', 'major']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]))
    for col in ['gpa', 'enrollment_year']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(data[col])
    if not updates:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(student_id)
    db.execute(f"UPDATE students SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('students', student_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Student updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
@require_api_key()
def delete_student(student_id):
    db = get_db()
    row = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    snapshot = get_record_snapshot('students', student_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM students WHERE id=?", (student_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('students', student_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Student deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Student deleted'})


# ==============================================================
# 5. NOTES — /api/notes
# ==============================================================

@modules_bp.route('/api/notes', methods=['GET'])
def get_notes():
    db = get_db()
    category = request.args.get('category', '')
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY is_pinned DESC, id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/notes', methods=['POST'])
def create_note():
    data = request.get_json(silent=True) or {}
    title = sanitize_str(data.get('title'))
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO notes (title,content,category,is_pinned,is_frozen,created_by_user) VALUES (?,?,?,?,0,?)",
        (title, sanitize_content(data.get('content')),
         sanitize_str(data.get('category')), data.get('is_pinned', 0), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('notes', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'title': title}, 'message': 'Note created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/notes/<int:note_id>', methods=['PUT'])
@require_api_key()
def update_note(note_id):
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Note not found'}), 404
    snapshot = get_record_snapshot('notes', note_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['title', 'category']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]))
    if 'content' in data:
        updates.append("content=?")
        values.append(sanitize_content(data['content']))
    if 'is_pinned' in data:
        updates.append("is_pinned=?")
        values.append(data['is_pinned'])
    updates.append("updated_at=CURRENT_TIMESTAMP")
    if len(updates) <= 1:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(note_id)
    db.execute(f"UPDATE notes SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('notes', note_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Note updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
@require_api_key()
def delete_note(note_id):
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Note not found'}), 404
    snapshot = get_record_snapshot('notes', note_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('notes', note_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Note deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Note deleted'})


# ==============================================================
# 6. FILE MANAGER — /api/files (SECURITY HARDENED)
# ==============================================================

@modules_bp.route('/api/files', methods=['GET'])
def list_files():
    db = get_db()
    rows = db.execute("SELECT * FROM files ORDER BY id ASC").fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400

    # Security: check extension
    if not allowed_file(f.filename):
        return jsonify({
            'error': 'File type not allowed',
            'allowed': list(ALLOWED_EXTENSIONS),
            'message': 'Only safe file types are accepted for security reasons'
        }), 400

    # Security: check file size
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 413

    # Security: validate magic bytes
    ext = f.filename.rsplit('.', 1)[1].lower()
    if not validate_file_content(f, ext):
        return jsonify({'error': 'File content does not match its extension. Possible disguised file.'}), 400

    # Sanitize filename
    original = secure_filename(f.filename)[:100]
    unique = f"{uuid.uuid4().hex}_{original}"
    filepath = os.path.join(UPLOAD_DIR, unique)
    f.save(filepath)

    db = get_db()
    c = db.execute(
        "INSERT INTO files (filename,original_name,file_type,file_size,uploaded_by,is_frozen,created_by_user) VALUES (?,?,?,?,?,0,?)",
        (unique, original, ext, size, 'anonymous', None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('files', record_id, 'create')
    return jsonify({
        'data': {'id': record_id, 'filename': original, 'size': size},
        'message': 'File uploaded (auto-deletes in 2 hours)'
    }), 201


@modules_bp.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    db = get_db()
    row = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(UPLOAD_DIR, row['filename'], as_attachment=True, download_name=row['original_name'])


@modules_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@require_api_key()
def delete_file(file_id):
    db = get_db()
    row = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'File not found'}), 404
    filepath = os.path.join(UPLOAD_DIR, row['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    db.execute("DELETE FROM files WHERE id=?", (file_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'File deleted'})


# ==============================================================
# 7. BLOG — /api/blog
# ==============================================================

@modules_bp.route('/api/blog', methods=['GET'])
def get_posts():
    db = get_db()
    tag = request.args.get('tag', '')
    query = "SELECT * FROM blog_posts WHERE 1=1"
    params = []
    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%{tag}%')
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/blog/<int:post_id>', methods=['GET'])
def get_post(post_id):
    db = get_db()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/blog', methods=['POST'])
def create_post():
    data = request.get_json(silent=True) or {}
    title = sanitize_str(data.get('title'))
    content = sanitize_content(data.get('content'))
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO blog_posts (title,content,author,tags,is_published,is_frozen,created_by_user) VALUES (?,?,?,?,?,0,?)",
        (title, content, sanitize_str(data.get('author', 'Anonymous')),
         sanitize_str(data.get('tags')), data.get('is_published', 1), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('blog_posts', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'title': title}, 'message': 'Blog post created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/blog/<int:post_id>', methods=['PUT'])
@require_api_key()
def update_post(post_id):
    db = get_db()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Post not found'}), 404
    snapshot = get_record_snapshot('blog_posts', post_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['title', 'author', 'tags']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]))
    if 'content' in data:
        updates.append("content=?")
        values.append(sanitize_content(data['content']))
    if 'is_published' in data:
        updates.append("is_published=?")
        values.append(data['is_published'])
    updates.append("updated_at=CURRENT_TIMESTAMP")
    if len(updates) <= 1:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(post_id)
    db.execute(f"UPDATE blog_posts SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('blog_posts', post_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Post updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/blog/<int:post_id>', methods=['DELETE'])
@require_api_key()
def delete_post(post_id):
    db = get_db()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Post not found'}), 404
    snapshot = get_record_snapshot('blog_posts', post_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('blog_posts', post_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Post deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Post deleted'})


# ==============================================================
# 8. INVENTORY — /api/inventory
# ==============================================================

@modules_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    db = get_db()
    low_stock = request.args.get('low_stock', '')
    category = request.args.get('category', '')
    warehouse = request.args.get('warehouse', '')
    query = "SELECT * FROM inventory WHERE 1=1"
    params = []
    if low_stock:
        query += " AND quantity < 10"
    if category:
        query += " AND category = ?"
        params.append(category)
    if warehouse:
        query += " AND warehouse = ?"
        params.append(warehouse)
    query += " ORDER BY id ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})


@modules_bp.route('/api/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Inventory item not found'}), 404
    return jsonify({'data': dict(row)})


@modules_bp.route('/api/inventory', methods=['POST'])
def create_inventory_item():
    data = request.get_json(silent=True) or {}
    name = sanitize_str(data.get('name'))
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO inventory (name,sku,quantity,price,category,warehouse,is_frozen,created_by_user) VALUES (?,?,?,?,?,?,0,?)",
        (name, sanitize_str(data.get('sku', f'SKU-{uuid.uuid4().hex[:6].upper()}')),
         data.get('quantity', 0), data.get('price', 0),
         sanitize_str(data.get('category')), sanitize_str(data.get('warehouse')), None)
    )
    record_id = c.lastrowid
    db.commit()
    db.close()
    track_modification('inventory', record_id, 'create')
    return jsonify({'data': {'id': record_id, 'name': name}, 'message': 'Inventory item created (auto-deletes in 2 hours)'}), 201


@modules_bp.route('/api/inventory/<int:item_id>', methods=['PUT'])
@require_api_key()
def update_inventory_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Inventory item not found'}), 404
    snapshot = get_record_snapshot('inventory', item_id)
    data = request.get_json(silent=True) or {}
    updates, values = [], []
    for col in ['name', 'sku', 'category', 'warehouse']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(sanitize_str(data[col]))
    for col in ['quantity', 'price']:
        if col in data:
            updates.append(f"{col}=?")
            values.append(data[col])
    if not updates:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400
    values.append(item_id)
    db.execute(f"UPDATE inventory SET {','.join(updates)} WHERE id=?", values)
    db.commit()
    db.close()
    user_id, key_id = get_user_context()
    track_modification('inventory', item_id, 'update', snapshot, user_id, key_id)
    return jsonify({'message': 'Inventory item updated (auto-reverts in 1 hour)'})


@modules_bp.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@require_api_key()
def delete_inventory_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Inventory item not found'}), 404
    snapshot = get_record_snapshot('inventory', item_id)
    is_frozen = row['is_frozen']
    db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    db.commit()
    db.close()
    if is_frozen:
        user_id, key_id = get_user_context()
        track_modification('inventory', item_id, 'delete', snapshot, user_id, key_id)
        return jsonify({'message': 'Inventory item deleted (auto-restores in 1 hour)'})
    return jsonify({'message': 'Inventory item deleted'})


# ==============================================================
# 9. WEATHER (Mock API — no CRUD, read-only)
# ==============================================================

WEATHER_DATA = {
    'london': {'city': 'London', 'country': 'UK', 'temp': 12, 'humidity': 78, 'condition': 'Cloudy', 'wind_speed': 15, 'uv_index': 2},
    'new york': {'city': 'New York', 'country': 'USA', 'temp': 18, 'humidity': 65, 'condition': 'Sunny', 'wind_speed': 10, 'uv_index': 5},
    'tokyo': {'city': 'Tokyo', 'country': 'Japan', 'temp': 22, 'humidity': 70, 'condition': 'Partly Cloudy', 'wind_speed': 8, 'uv_index': 4},
    'dubai': {'city': 'Dubai', 'country': 'UAE', 'temp': 38, 'humidity': 45, 'condition': 'Sunny', 'wind_speed': 12, 'uv_index': 9},
    'paris': {'city': 'Paris', 'country': 'France', 'temp': 15, 'humidity': 72, 'condition': 'Rainy', 'wind_speed': 18, 'uv_index': 3},
    'sydney': {'city': 'Sydney', 'country': 'Australia', 'temp': 25, 'humidity': 60, 'condition': 'Sunny', 'wind_speed': 14, 'uv_index': 7},
    'moscow': {'city': 'Moscow', 'country': 'Russia', 'temp': -5, 'humidity': 85, 'condition': 'Snowy', 'wind_speed': 20, 'uv_index': 1},
    'cairo': {'city': 'Cairo', 'country': 'Egypt', 'temp': 32, 'humidity': 30, 'condition': 'Sunny', 'wind_speed': 8, 'uv_index': 8},
    'berlin': {'city': 'Berlin', 'country': 'Germany', 'temp': 10, 'humidity': 75, 'condition': 'Overcast', 'wind_speed': 16, 'uv_index': 2},
    'singapore': {'city': 'Singapore', 'country': 'Singapore', 'temp': 30, 'humidity': 88, 'condition': 'Humid', 'wind_speed': 6, 'uv_index': 6},
}


@modules_bp.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', '').lower().strip()
    if city:
        data = WEATHER_DATA.get(city)
        if not data:
            return jsonify({'error': f'City not found. Available: {", ".join(WEATHER_DATA.keys())}'}), 404
        return jsonify({'data': data})
    return jsonify({
        'data': list(WEATHER_DATA.values()),
        'available_cities': list(WEATHER_DATA.keys()),
        'count': len(WEATHER_DATA)
    })


@modules_bp.route('/api/weather/compare', methods=['GET'])
def compare_weather():
    c1 = request.args.get('city1', '').lower().strip()
    c2 = request.args.get('city2', '').lower().strip()
    if not c1 or not c2:
        return jsonify({'error': 'Provide city1 and city2 query parameters'}), 400
    d1 = WEATHER_DATA.get(c1)
    d2 = WEATHER_DATA.get(c2)
    if not d1 or not d2:
        return jsonify({'error': f'City not found. Available: {", ".join(WEATHER_DATA.keys())}'}), 404
    return jsonify({
        'comparison': {
            'city1': d1, 'city2': d2,
            'temp_diff': abs(d1['temp'] - d2['temp']),
            'warmer': d1['city'] if d1['temp'] > d2['temp'] else d2['city']
        }
    })


# ==============================================================
# 10. AI ASSISTANT (OpenRouter) — /api/ai/*
# ==============================================================

OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY', '')
AI_MODEL = os.getenv('AI_MODEL', 'openai/gpt-3.5-turbo')
AI_BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'


def call_ai(messages, max_tokens=500):
    if not OPENROUTER_KEY:
        return None, 'AI service not configured (no API key)'
    try:
        resp = requests.post(AI_BASE_URL, json={
            'model': AI_MODEL,
            'messages': messages,
            'max_tokens': max_tokens
        }, headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type': 'application/json'
        }, timeout=30)
        data = resp.json()
        if 'choices' in data and data['choices']:
            return data['choices'][0]['message']['content'], None
        return None, data.get('error', {}).get('message', 'AI request failed')
    except Exception as e:
        return None, str(e)


@modules_bp.route('/api/ai/generate', methods=['POST'])
def ai_generate():
    data = request.get_json(silent=True) or {}
    prompt = sanitize_content(data.get('prompt'))
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    result, error = call_ai([
        {'role': 'system', 'content': 'You are a helpful AI assistant. Generate clear, concise content.'},
        {'role': 'user', 'content': prompt}
    ], data.get('max_tokens', 500))
    if error:
        return jsonify({'error': error}), 503
    return jsonify({'data': {'generated_text': result, 'model': AI_MODEL}})


@modules_bp.route('/api/ai/summarize', methods=['POST'])
def ai_summarize():
    data = request.get_json(silent=True) or {}
    text = sanitize_content(data.get('text'))
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    result, error = call_ai([
        {'role': 'system', 'content': 'Summarize the following text concisely.'},
        {'role': 'user', 'content': text}
    ])
    if error:
        return jsonify({'error': error}), 503
    return jsonify({'data': {'summary': result, 'original_length': len(text), 'model': AI_MODEL}})


@modules_bp.route('/api/ai/classify', methods=['POST'])
def ai_classify():
    data = request.get_json(silent=True) or {}
    text = sanitize_content(data.get('text'))
    cats = data.get('categories', [])
    if not text or not cats:
        return jsonify({'error': 'Text and categories are required'}), 400
    result, error = call_ai([
        {'role': 'system', 'content': f'Classify the text into one of: {", ".join(cats)}. Respond with only the category name.'},
        {'role': 'user', 'content': text}
    ])
    if error:
        return jsonify({'error': error}), 503
    return jsonify({'data': {'classification': result, 'categories': cats, 'model': AI_MODEL}})


@modules_bp.route('/api/ai/validate', methods=['POST'])
def ai_validate():
    data = request.get_json(silent=True) or {}
    text = sanitize_content(data.get('text'))
    vtype = sanitize_str(data.get('type', 'grammar'))
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    result, error = call_ai([
        {'role': 'system', 'content': f'Check the following text for {vtype} issues. Point out errors and suggest corrections.'},
        {'role': 'user', 'content': text}
    ])
    if error:
        return jsonify({'error': error}), 503
    return jsonify({'data': {'validation': result, 'type': vtype, 'model': AI_MODEL}})


@modules_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json(silent=True) or {}
    message = sanitize_content(data.get('message'))
    context = sanitize_str(data.get('context', 'general'))
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    result, error = call_ai([
        {'role': 'system', 'content': f'You are an AI tutor helping with {context}. Be helpful, clear, and educational.'},
        {'role': 'user', 'content': message}
    ])
    if error:
        return jsonify({'error': error}), 503
    return jsonify({'data': {'response': result, 'context': context, 'model': AI_MODEL}})


# ==============================================================
# UTILITY ENDPOINTS
# ==============================================================

@modules_bp.route('/api/echo', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def echo():
    return jsonify({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'query_params': dict(request.args),
        'body': request.get_json(silent=True),
        'content_type': request.content_type,
        'ip': request.remote_addr,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    })


@modules_bp.route('/api/headers', methods=['GET'])
def show_headers():
    return jsonify({
        'your_headers': dict(request.headers),
        'ip': request.remote_addr,
        'method': request.method
    })


@modules_bp.route('/api/status-codes/<int:code>', methods=['GET'])
def status_code(code):
    messages = {
        200: 'OK', 201: 'Created', 204: 'No Content',
        301: 'Moved Permanently', 302: 'Found', 304: 'Not Modified',
        400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden',
        404: 'Not Found', 405: 'Method Not Allowed', 409: 'Conflict',
        429: 'Too Many Requests', 500: 'Internal Server Error',
        502: 'Bad Gateway', 503: 'Service Unavailable'
    }
    msg = messages.get(code, 'Unknown Status Code')
    return jsonify({'status_code': code, 'message': msg, 'description': f'This is a {code} {msg} response'}), code if code < 600 else 200


@modules_bp.route('/api/health', methods=['GET'])
def health():
    from freeze import get_freeze_info
    freeze_info = get_freeze_info()
    db = get_db()
    counts = {}
    for table in ['books', 'menu_items', 'tasks', 'students', 'notes', 'files', 'blog_posts', 'inventory']:
        counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    db.close()
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'deep_freeze': freeze_info,
        'record_counts': counts,
        'features': ['deep_freeze', 'api_key_tracking', 'file_security', 'i18n', 'rtl']
    })


@modules_bp.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'HTTP Playground API',
        'version': '2.0.0',
        'description': 'The ultimate HTTP testing platform — GET/POST are public, PUT/DELETE need API key. Deep freeze auto-reverts changes!',
        'deep_freeze': {
            'enabled': True,
            'post_auto_delete': '2 hours',
            'put_auto_revert': '1 hour',
            'delete_auto_restore': '1 hour'
        },
        'api_key': {
            'max_requests': 20,
            'regenerate': '/api/auth/regenerate-key'
        },
        'modules': [
            {'name': 'Library', 'path': '/api/books', 'page': '/module/books', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Restaurant Menu', 'path': '/api/menu', 'page': '/module/menu', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Task Manager', 'path': '/api/tasks', 'page': '/module/tasks', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Student Management', 'path': '/api/students', 'page': '/module/students', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Notes', 'path': '/api/notes', 'page': '/module/notes', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'File Manager', 'path': '/api/files', 'page': '/module/files', 'auth': {'get': 'none', 'post': 'none', 'put': 'n/a', 'delete': 'api_key'}},
            {'name': 'Blog', 'path': '/api/blog', 'page': '/module/blog', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Inventory', 'path': '/api/inventory', 'page': '/module/inventory', 'auth': {'get': 'none', 'post': 'none', 'put': 'api_key', 'delete': 'api_key'}},
            {'name': 'Weather', 'path': '/api/weather', 'page': '/module/weather', 'auth': {'get': 'none'}},
            {'name': 'AI Assistant', 'path': '/api/ai/*', 'page': '/module/ai', 'auth': {'post': 'none'}},
        ],
        'documentation': '/docs'
    })


# ==============================================================
# DEEP FREEZE ADMIN — Superadmin can add frozen baseline data
# ==============================================================

@modules_bp.route('/api/admin/freeze/status', methods=['GET'])
@require_role('admin', 'superadmin')
def freeze_status():
    from freeze import get_freeze_info
    return jsonify({'data': get_freeze_info()})


@modules_bp.route('/api/admin/freeze/add-baseline', methods=['POST'])
@require_role('superadmin')
def add_baseline():
    """Superadmin: add data permanently to the frozen baseline"""
    data = request.get_json(silent=True) or {}
    table = data.get('table')
    record_id = data.get('record_id')
    if not table or not record_id:
        return jsonify({'error': 'table and record_id are required'}), 400
    if table not in ['books', 'menu_items', 'tasks', 'students', 'notes', 'blog_posts', 'inventory']:
        return jsonify({'error': 'Invalid table name'}), 400
    db = get_db()
    db.execute(f"UPDATE {table} SET is_frozen = 1, created_by_user = NULL WHERE id = ?", (record_id,))
    # Remove any pending modification for this record
    db.execute("DELETE FROM user_modifications WHERE table_name = ? AND record_id = ?", (table, record_id))
    db.commit()
    db.close()
    return jsonify({'message': f'Record {record_id} in {table} is now frozen baseline data'})
