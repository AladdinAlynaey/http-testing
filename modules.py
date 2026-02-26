"""
Application Modules - 10 CRUD modules with beginner/intermediate/advanced scenarios
"""
import os
import uuid
import requests
import bleach
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from database import get_db
from auth import require_auth, require_api_key, require_role, get_current_user, log_audit
from dotenv import load_dotenv

load_dotenv()

modules_bp = Blueprint('modules', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 5242880))
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,csv,json').split(','))
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-3.5-turbo')


def sanitize(text):
    if text is None:
        return None
    return bleach.clean(str(text).strip(), tags=[], strip=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# 1. LIBRARY SYSTEM (Public - Beginner)
# ============================================================
@modules_bp.route('/api/books', methods=['GET'])
def get_books():
    """Get all books - PUBLIC endpoint"""
    db = get_db()
    genre = request.args.get('genre')
    search = request.args.get('search')
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if genre:
        query += " AND genre=?"
        params.append(sanitize(genre))
    if search:
        query += " AND (title LIKE ? OR author LIKE ?)"
        params.extend([f'%{sanitize(search)}%', f'%{sanitize(search)}%'])
    query += " ORDER BY id DESC"
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
    title = sanitize(data.get('title'))
    author = sanitize(data.get('author'))
    if not title or not author:
        return jsonify({'error': 'Title and author are required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO books (title,author,isbn,genre,year,available) VALUES (?,?,?,?,?,?)",
        (title, author, sanitize(data.get('isbn')), sanitize(data.get('genre')),
         data.get('year'), data.get('available', 1))
    )
    db.commit()
    book_id = c.lastrowid
    row = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Book created successfully'}), 201

@modules_bp.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Book not found'}), 404
    db.execute(
        "UPDATE books SET title=?, author=?, isbn=?, genre=?, year=?, available=? WHERE id=?",
        (sanitize(data.get('title', existing['title'])),
         sanitize(data.get('author', existing['author'])),
         sanitize(data.get('isbn', existing['isbn'])),
         sanitize(data.get('genre', existing['genre'])),
         data.get('year', existing['year']),
         data.get('available', existing['available']),
         book_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Book updated successfully'})

@modules_bp.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    db = get_db()
    existing = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Book not found'}), 404
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Book deleted successfully'})


# ============================================================
# 2. RESTAURANT MENU (Public - Beginner)
# ============================================================
@modules_bp.route('/api/menu', methods=['GET'])
def get_menu():
    db = get_db()
    category = request.args.get('category')
    query = "SELECT * FROM menu_items"
    params = []
    if category:
        query += " WHERE category=?"
        params.append(sanitize(category))
    query += " ORDER BY category, name"
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
    name = sanitize(data.get('name'))
    price = data.get('price')
    category = sanitize(data.get('category'))
    if not name or price is None or not category:
        return jsonify({'error': 'Name, price, and category are required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO menu_items (name,description,price,category,is_available) VALUES (?,?,?,?,?)",
        (name, sanitize(data.get('description')), float(price), category,
         data.get('is_available', 1))
    )
    db.commit()
    row = db.execute("SELECT * FROM menu_items WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Menu item created'}), 201

@modules_bp.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Menu item not found'}), 404
    db.execute(
        "UPDATE menu_items SET name=?,description=?,price=?,category=?,is_available=? WHERE id=?",
        (sanitize(data.get('name', existing['name'])),
         sanitize(data.get('description', existing['description'])),
         float(data.get('price', existing['price'])),
         sanitize(data.get('category', existing['category'])),
         data.get('is_available', existing['is_available']),
         item_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Menu item updated'})

@modules_bp.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    db = get_db()
    existing = db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Menu item not found'}), 404
    db.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Menu item deleted'})


# ============================================================
# 3. TASK MANAGER (Public - Beginner)
# ============================================================
@modules_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    db = get_db()
    status = request.args.get('status')
    priority = request.args.get('priority')
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(sanitize(status))
    if priority:
        query += " AND priority=?"
        params.append(sanitize(priority))
    query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id DESC"
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
    title = sanitize(data.get('title'))
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO tasks (title,description,status,priority,due_date,assigned_to) VALUES (?,?,?,?,?,?)",
        (title, sanitize(data.get('description')), sanitize(data.get('status', 'pending')),
         sanitize(data.get('priority', 'medium')), data.get('due_date'),
         sanitize(data.get('assigned_to')))
    )
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Task created'}), 201

@modules_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Task not found'}), 404
    db.execute(
        "UPDATE tasks SET title=?,description=?,status=?,priority=?,due_date=?,assigned_to=? WHERE id=?",
        (sanitize(data.get('title', existing['title'])),
         sanitize(data.get('description', existing['description'])),
         sanitize(data.get('status', existing['status'])),
         sanitize(data.get('priority', existing['priority'])),
         data.get('due_date', existing['due_date']),
         sanitize(data.get('assigned_to', existing['assigned_to'])),
         task_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Task updated'})

@modules_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Task not found'}), 404
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Task deleted'})


# ============================================================
# 4. STUDENT MANAGEMENT (Intermediate - API Key)
# ============================================================
@modules_bp.route('/api/students', methods=['GET'])
def get_students():
    db = get_db()
    major = request.args.get('major')
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if major:
        query += " AND major=?"
        params.append(sanitize(major))
    query += " ORDER BY name"
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
@require_api_key('intermediate')
def create_student():
    data = request.get_json(silent=True) or {}
    name = sanitize(data.get('name'))
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO students (name,email,student_id,major,gpa,enrollment_year) VALUES (?,?,?,?,?,?)",
        (name, sanitize(data.get('email')), sanitize(data.get('student_id')),
         sanitize(data.get('major')), data.get('gpa'), data.get('enrollment_year'))
    )
    db.commit()
    row = db.execute("SELECT * FROM students WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    log_audit(g.current_user.get('user_id'), 'create_student', f'student:{c.lastrowid}')
    return jsonify({'data': dict(row), 'message': 'Student created'}), 201

@modules_bp.route('/api/students/<int:student_id>', methods=['PUT'])
@require_api_key('intermediate')
def update_student(student_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    db.execute(
        "UPDATE students SET name=?,email=?,student_id=?,major=?,gpa=?,enrollment_year=? WHERE id=?",
        (sanitize(data.get('name', existing['name'])),
         sanitize(data.get('email', existing['email'])),
         sanitize(data.get('student_id', existing['student_id'])),
         sanitize(data.get('major', existing['major'])),
         data.get('gpa', existing['gpa']),
         data.get('enrollment_year', existing['enrollment_year']),
         student_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Student updated'})

@modules_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
@require_api_key('intermediate')
def delete_student(student_id):
    db = get_db()
    existing = db.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    db.execute("DELETE FROM students WHERE id=?", (student_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Student deleted'})


# ============================================================
# 5. NOTES SYSTEM (Public - Beginner)
# ============================================================
@modules_bp.route('/api/notes', methods=['GET'])
def get_notes():
    db = get_db()
    category = request.args.get('category')
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if category:
        query += " AND category=?"
        params.append(sanitize(category))
    query += " ORDER BY is_pinned DESC, id DESC"
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
    title = sanitize(data.get('title'))
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO notes (title,content,category,is_pinned) VALUES (?,?,?,?)",
        (title, sanitize(data.get('content')), sanitize(data.get('category')),
         data.get('is_pinned', 0))
    )
    db.commit()
    row = db.execute("SELECT * FROM notes WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Note created'}), 201

@modules_bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Note not found'}), 404
    db.execute(
        "UPDATE notes SET title=?,content=?,category=?,is_pinned=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (sanitize(data.get('title', existing['title'])),
         sanitize(data.get('content', existing['content'])),
         sanitize(data.get('category', existing['category'])),
         data.get('is_pinned', existing['is_pinned']),
         note_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Note updated'})

@modules_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    db = get_db()
    existing = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Note not found'}), 404
    db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Note deleted'})


# ============================================================
# 6. FILE UPLOAD/DOWNLOAD PLAYGROUND (Intermediate - API Key)
# ============================================================
@modules_bp.route('/api/files', methods=['GET'])
def list_files():
    db = get_db()
    rows = db.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

@modules_bp.route('/api/files/upload', methods=['POST'])
@require_api_key('intermediate')
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_SIZE:
        return jsonify({'error': f'File too large. Max size: {MAX_UPLOAD_SIZE // 1048576}MB'}), 400

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(UPLOAD_FOLDER, unique_name))

    ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'unknown'
    db = get_db()
    c = db.execute(
        "INSERT INTO files (filename,original_name,file_type,file_size,uploaded_by) VALUES (?,?,?,?,?)",
        (unique_name, original_name, ext, size, g.current_user.get('username', 'anonymous'))
    )
    db.commit()
    row = db.execute("SELECT * FROM files WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    log_audit(g.current_user.get('user_id'), 'upload_file', f'file:{unique_name}')
    return jsonify({'data': dict(row), 'message': 'File uploaded successfully'}), 201

@modules_bp.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    db = get_db()
    row = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'File not found'}), 404
    filepath = os.path.join(UPLOAD_FOLDER, row['filename'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_from_directory(UPLOAD_FOLDER, row['filename'],
                               download_name=row['original_name'], as_attachment=True)

@modules_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@require_api_key('intermediate')
def delete_file(file_id):
    db = get_db()
    row = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'File not found'}), 404
    filepath = os.path.join(UPLOAD_FOLDER, row['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    db.execute("DELETE FROM files WHERE id=?", (file_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'File deleted'})


# ============================================================
# 7. BLOG SYSTEM (Public Read, Intermediate Write)
# ============================================================
@modules_bp.route('/api/blog', methods=['GET'])
def get_blog_posts():
    db = get_db()
    tag = request.args.get('tag')
    query = "SELECT * FROM blog_posts WHERE is_published=1"
    params = []
    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%{sanitize(tag)}%')
    query += " ORDER BY id DESC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

@modules_bp.route('/api/blog/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    db = get_db()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify({'data': dict(row)})

@modules_bp.route('/api/blog', methods=['POST'])
@require_api_key('intermediate')
def create_blog_post():
    data = request.get_json(silent=True) or {}
    title = sanitize(data.get('title'))
    content = sanitize(data.get('content'))
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO blog_posts (title,content,author,tags,is_published) VALUES (?,?,?,?,?)",
        (title, content, g.current_user.get('username', 'anonymous'),
         sanitize(data.get('tags')), data.get('is_published', 1))
    )
    db.commit()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Blog post created'}), 201

@modules_bp.route('/api/blog/<int:post_id>', methods=['PUT'])
@require_api_key('intermediate')
def update_blog_post(post_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Post not found'}), 404
    db.execute(
        "UPDATE blog_posts SET title=?,content=?,tags=?,is_published=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (sanitize(data.get('title', existing['title'])),
         sanitize(data.get('content', existing['content'])),
         sanitize(data.get('tags', existing['tags'])),
         data.get('is_published', existing['is_published']),
         post_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Post updated'})

@modules_bp.route('/api/blog/<int:post_id>', methods=['DELETE'])
@require_api_key('intermediate')
def delete_blog_post(post_id):
    db = get_db()
    existing = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Post not found'}), 404
    db.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Post deleted'})


# ============================================================
# 8. INVENTORY SYSTEM (Intermediate - API Key)
# ============================================================
@modules_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    db = get_db()
    category = request.args.get('category')
    warehouse = request.args.get('warehouse')
    low_stock = request.args.get('low_stock')
    query = "SELECT * FROM inventory WHERE 1=1"
    params = []
    if category:
        query += " AND category=?"
        params.append(sanitize(category))
    if warehouse:
        query += " AND warehouse=?"
        params.append(sanitize(warehouse))
    if low_stock:
        query += " AND quantity < 10"
    query += " ORDER BY name"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify({'data': [dict(r) for r in rows], 'count': len(rows)})

@modules_bp.route('/api/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'data': dict(row)})

@modules_bp.route('/api/inventory', methods=['POST'])
@require_api_key('intermediate')
def create_inventory_item():
    data = request.get_json(silent=True) or {}
    name = sanitize(data.get('name'))
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db = get_db()
    c = db.execute(
        "INSERT INTO inventory (name,sku,quantity,price,category,warehouse) VALUES (?,?,?,?,?,?)",
        (name, sanitize(data.get('sku')), data.get('quantity', 0),
         data.get('price'), sanitize(data.get('category')),
         sanitize(data.get('warehouse')))
    )
    db.commit()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (c.lastrowid,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Item created'}), 201

@modules_bp.route('/api/inventory/<int:item_id>', methods=['PUT'])
@require_api_key('intermediate')
def update_inventory_item(item_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    existing = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Item not found'}), 404
    db.execute(
        "UPDATE inventory SET name=?,sku=?,quantity=?,price=?,category=?,warehouse=? WHERE id=?",
        (sanitize(data.get('name', existing['name'])),
         sanitize(data.get('sku', existing['sku'])),
         data.get('quantity', existing['quantity']),
         data.get('price', existing['price']),
         sanitize(data.get('category', existing['category'])),
         sanitize(data.get('warehouse', existing['warehouse'])),
         item_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    db.close()
    return jsonify({'data': dict(row), 'message': 'Item updated'})

@modules_bp.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@require_api_key('intermediate')
def delete_inventory_item(item_id):
    db = get_db()
    existing = db.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': 'Item not found'}), 404
    db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Item deleted'})


# ============================================================
# 9. MOCK WEATHER API (Public - Beginner)
# ============================================================
MOCK_WEATHER = {
    'london': {'city': 'London', 'country': 'UK', 'temp_c': 12, 'temp_f': 54, 'condition': 'Cloudy', 'humidity': 78, 'wind_kph': 15},
    'new york': {'city': 'New York', 'country': 'US', 'temp_c': 8, 'temp_f': 46, 'condition': 'Sunny', 'humidity': 45, 'wind_kph': 10},
    'tokyo': {'city': 'Tokyo', 'country': 'JP', 'temp_c': 18, 'temp_f': 64, 'condition': 'Partly Cloudy', 'humidity': 60, 'wind_kph': 8},
    'paris': {'city': 'Paris', 'country': 'FR', 'temp_c': 14, 'temp_f': 57, 'condition': 'Rainy', 'humidity': 82, 'wind_kph': 20},
    'dubai': {'city': 'Dubai', 'country': 'AE', 'temp_c': 35, 'temp_f': 95, 'condition': 'Sunny', 'humidity': 30, 'wind_kph': 12},
    'berlin': {'city': 'Berlin', 'country': 'DE', 'temp_c': 10, 'temp_f': 50, 'condition': 'Overcast', 'humidity': 70, 'wind_kph': 18},
    'sydney': {'city': 'Sydney', 'country': 'AU', 'temp_c': 25, 'temp_f': 77, 'condition': 'Sunny', 'humidity': 55, 'wind_kph': 14},
    'cairo': {'city': 'Cairo', 'country': 'EG', 'temp_c': 28, 'temp_f': 82, 'condition': 'Clear', 'humidity': 25, 'wind_kph': 6},
    'moscow': {'city': 'Moscow', 'country': 'RU', 'temp_c': -5, 'temp_f': 23, 'condition': 'Snowy', 'humidity': 85, 'wind_kph': 22},
    'baghdad': {'city': 'Baghdad', 'country': 'IQ', 'temp_c': 32, 'temp_f': 90, 'condition': 'Hot', 'humidity': 20, 'wind_kph': 8},
}

@modules_bp.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather for a city"""
    city = request.args.get('city', '').lower().strip()
    if not city:
        return jsonify({'data': list(MOCK_WEATHER.values()), 'message': 'All available cities'})
    weather = MOCK_WEATHER.get(city)
    if not weather:
        return jsonify({'error': f'City "{city}" not found', 'available_cities': list(MOCK_WEATHER.keys())}), 404
    return jsonify({'data': weather})

@modules_bp.route('/api/weather/compare', methods=['GET'])
def compare_weather():
    """Compare weather between two cities"""
    city1 = request.args.get('city1', '').lower().strip()
    city2 = request.args.get('city2', '').lower().strip()
    if not city1 or not city2:
        return jsonify({'error': 'Both city1 and city2 parameters are required'}), 400
    w1 = MOCK_WEATHER.get(city1)
    w2 = MOCK_WEATHER.get(city2)
    if not w1 or not w2:
        return jsonify({'error': 'One or both cities not found'}), 404
    return jsonify({
        'data': {
            'city1': w1,
            'city2': w2,
            'temperature_difference_c': abs(w1['temp_c'] - w2['temp_c']),
            'warmer_city': w1['city'] if w1['temp_c'] > w2['temp_c'] else w2['city']
        }
    })


# ============================================================
# 10. AI ASSISTANT (Advanced - Login Required)
# ============================================================
@modules_bp.route('/api/ai/generate', methods=['POST'])
@require_auth
def ai_generate():
    """Generate text using OpenRouter AI"""
    data = request.get_json(silent=True) or {}
    prompt = sanitize(data.get('prompt', ''))
    if not prompt or len(prompt) < 3:
        return jsonify({'error': 'Prompt is required (min 3 characters)'}), 400
    if len(prompt) > 2000:
        return jsonify({'error': 'Prompt too long (max 2000 characters)'}), 400

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your_openrouter_api_key_here':
        return jsonify({'error': 'AI service not configured', 'message': 'OpenRouter API key not set'}), 503

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful educational assistant. Keep responses concise and appropriate.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.7
            },
            timeout=30
        )
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        log_audit(g.current_user.get('user_id'), 'ai_generate', 'ai', prompt[:100])
        return jsonify({'data': {'response': content, 'model': OPENROUTER_MODEL}})
    except requests.Timeout:
        return jsonify({'error': 'AI service timeout'}), 504
    except Exception as e:
        return jsonify({'error': 'AI service error', 'details': str(e)}), 500

@modules_bp.route('/api/ai/summarize', methods=['POST'])
@require_auth
def ai_summarize():
    """Summarize text using AI"""
    data = request.get_json(silent=True) or {}
    text = sanitize(data.get('text', ''))
    if not text or len(text) < 20:
        return jsonify({'error': 'Text to summarize is required (min 20 characters)'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Text too long (max 5000 characters)'}), 400

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your_openrouter_api_key_here':
        return jsonify({'error': 'AI service not configured'}), 503

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': 'Summarize the following text concisely. Provide key points.'},
                    {'role': 'user', 'content': text}
                ],
                'max_tokens': 300,
                'temperature': 0.3
            },
            timeout=30
        )
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No summary')
        log_audit(g.current_user.get('user_id'), 'ai_summarize', 'ai')
        return jsonify({'data': {'summary': content, 'original_length': len(text)}})
    except Exception as e:
        return jsonify({'error': 'AI service error', 'details': str(e)}), 500

@modules_bp.route('/api/ai/classify', methods=['POST'])
@require_auth
def ai_classify():
    """Classify text into categories"""
    data = request.get_json(silent=True) or {}
    text = sanitize(data.get('text', ''))
    categories = data.get('categories', [])
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    if not categories:
        categories = ['Technology', 'Science', 'Business', 'Health', 'Education', 'Sports', 'Entertainment']

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your_openrouter_api_key_here':
        return jsonify({'error': 'AI service not configured'}), 503

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': f'Classify the following text into one of these categories: {", ".join(categories)}. Respond with only the category name.'},
                    {'role': 'user', 'content': text}
                ],
                'max_tokens': 50,
                'temperature': 0.1
            },
            timeout=30
        )
        result = response.json()
        category = result.get('choices', [{}])[0].get('message', {}).get('content', 'Unknown').strip()
        log_audit(g.current_user.get('user_id'), 'ai_classify', 'ai')
        return jsonify({'data': {'category': category, 'available_categories': categories}})
    except Exception as e:
        return jsonify({'error': 'AI service error', 'details': str(e)}), 500

@modules_bp.route('/api/ai/validate', methods=['POST'])
@require_auth
def ai_validate():
    """Validate/check content using AI"""
    data = request.get_json(silent=True) or {}
    text = sanitize(data.get('text', ''))
    check_type = sanitize(data.get('type', 'grammar'))
    if not text:
        return jsonify({'error': 'Text is required'}), 400

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your_openrouter_api_key_here':
        return jsonify({'error': 'AI service not configured'}), 503

    prompts = {
        'grammar': 'Check the following text for grammar and spelling errors. List any issues found and provide corrections.',
        'code': 'Review the following code for potential bugs, security issues, and best practices. Provide suggestions.',
        'email': 'Review the following email for professionalism, clarity, and tone. Suggest improvements.',
        'api': 'Validate the following API request/response for correctness and best practices.'
    }
    system_prompt = prompts.get(check_type, prompts['grammar'])

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text}
                ],
                'max_tokens': 500,
                'temperature': 0.3
            },
            timeout=30
        )
        result = response.json()
        feedback = result.get('choices', [{}])[0].get('message', {}).get('content', 'No feedback')
        log_audit(g.current_user.get('user_id'), 'ai_validate', 'ai', check_type)
        return jsonify({'data': {'feedback': feedback, 'check_type': check_type}})
    except Exception as e:
        return jsonify({'error': 'AI service error', 'details': str(e)}), 500

@modules_bp.route('/api/ai/chat', methods=['POST'])
@require_auth
def ai_chat():
    """Interactive AI chat for learning"""
    data = request.get_json(silent=True) or {}
    message = sanitize(data.get('message', ''))
    context = sanitize(data.get('context', 'general'))
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    if len(message) > 1000:
        return jsonify({'error': 'Message too long (max 1000 characters)'}), 400

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'your_openrouter_api_key_here':
        return jsonify({'error': 'AI service not configured'}), 503

    system_prompts = {
        'general': 'You are a helpful teaching assistant. Answer questions clearly and provide examples when useful.',
        'api': 'You are an API and HTTP expert. Help students understand REST APIs, HTTP methods, status codes, and CURL.',
        'security': 'You are a cybersecurity expert. Help students understand web security, authentication, and best practices.',
        'python': 'You are a Python programming tutor. Help students learn Python with clear examples.',
    }

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompts.get(context, system_prompts['general'])},
                    {'role': 'user', 'content': message}
                ],
                'max_tokens': 600,
                'temperature': 0.7
            },
            timeout=30
        )
        result = response.json()
        reply = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
        log_audit(g.current_user.get('user_id'), 'ai_chat', 'ai', context)
        return jsonify({'data': {'reply': reply, 'context': context}})
    except Exception as e:
        return jsonify({'error': 'AI service error', 'details': str(e)}), 500


# ============================================================
# UTILITY ENDPOINTS
# ============================================================
@modules_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'version': '1.0.0'
    })

@modules_bp.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'HTTP Playground API',
        'version': '1.0.0',
        'description': 'Educational HTTP playground and API training platform',
        'modules': [
            {'name': 'Library', 'path': '/api/books', 'level': 'beginner', 'auth': 'none'},
            {'name': 'Restaurant Menu', 'path': '/api/menu', 'level': 'beginner', 'auth': 'none'},
            {'name': 'Task Manager', 'path': '/api/tasks', 'level': 'beginner', 'auth': 'none'},
            {'name': 'Student Management', 'path': '/api/students', 'level': 'intermediate', 'auth': 'api_key'},
            {'name': 'Notes', 'path': '/api/notes', 'level': 'beginner', 'auth': 'none'},
            {'name': 'File Manager', 'path': '/api/files', 'level': 'intermediate', 'auth': 'api_key'},
            {'name': 'Blog', 'path': '/api/blog', 'level': 'beginner/intermediate', 'auth': 'none/api_key'},
            {'name': 'Inventory', 'path': '/api/inventory', 'level': 'intermediate', 'auth': 'api_key'},
            {'name': 'Weather', 'path': '/api/weather', 'level': 'beginner', 'auth': 'none'},
            {'name': 'AI Assistant', 'path': '/api/ai/*', 'level': 'advanced', 'auth': 'login'},
        ],
        'documentation': '/docs'
    })

@modules_bp.route('/api/echo', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def echo():
    """Echo back the request details - great for learning HTTP"""
    return jsonify({
        'method': request.method,
        'path': request.path,
        'headers': dict(request.headers),
        'args': dict(request.args),
        'body': request.get_json(silent=True),
        'ip': request.remote_addr,
        'content_type': request.content_type
    })

@modules_bp.route('/api/status-codes/<int:code>', methods=['GET'])
def status_code_demo(code):
    """Return a specific HTTP status code - for learning"""
    messages = {
        200: 'OK - Request succeeded',
        201: 'Created - Resource created successfully',
        204: 'No Content - Request succeeded with no body',
        301: 'Moved Permanently - Resource has been moved',
        400: 'Bad Request - Invalid request syntax',
        401: 'Unauthorized - Authentication required',
        403: 'Forbidden - You do not have permission',
        404: 'Not Found - Resource does not exist',
        405: 'Method Not Allowed - HTTP method not supported',
        409: 'Conflict - Resource conflict detected',
        429: 'Too Many Requests - Rate limit exceeded',
        500: 'Internal Server Error - Server failed',
        502: 'Bad Gateway - Invalid response from upstream',
        503: 'Service Unavailable - Server temporarily unavailable',
    }
    if code not in messages:
        return jsonify({'error': f'Unknown status code {code}', 'available': list(messages.keys())}), 400
    return jsonify({'status_code': code, 'message': messages[code]}), code if code < 400 else 200

@modules_bp.route('/api/headers', methods=['GET'])
def show_headers():
    """Show all request headers - for learning"""
    return jsonify({
        'your_headers': dict(request.headers),
        'your_ip': request.remote_addr,
        'tip': 'Try adding custom headers with curl -H "X-Custom: value"'
    })
