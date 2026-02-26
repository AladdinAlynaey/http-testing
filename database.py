"""
Database module - SQLite initialization and helpers
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'platform.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # API Keys table
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT UNIQUE NOT NULL,
        scope TEXT NOT NULL DEFAULT 'basic',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Audit logs
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        resource TEXT,
        ip_address TEXT,
        user_agent TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Rate limit blocks
    c.execute('''CREATE TABLE IF NOT EXISTS rate_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        block_type TEXT NOT NULL,
        reason TEXT,
        blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )''')

    # Login attempts
    c.execute('''CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        success INTEGER DEFAULT 0,
        ip_address TEXT,
        attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # ===== APPLICATION MODULE TABLES =====

    # 1. Library
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT,
        genre TEXT,
        year INTEGER,
        available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2. Restaurant Menu
    c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        is_available INTEGER DEFAULT 1,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 3. Task Manager
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        priority TEXT DEFAULT 'medium',
        due_date TEXT,
        assigned_to TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 4. Student Management
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        student_id TEXT UNIQUE,
        major TEXT,
        gpa REAL,
        enrollment_year INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 5. Notes
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        category TEXT,
        is_pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 6. File metadata (uploads stored on disk)
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        uploaded_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 7. Blog
    c.execute('''CREATE TABLE IF NOT EXISTS blog_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        tags TEXT,
        is_published INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 8. Inventory
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE,
        quantity INTEGER DEFAULT 0,
        price REAL,
        category TEXT,
        warehouse TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()

    # Seed sample data
    _seed_data(conn)
    conn.close()

def _seed_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] > 0:
        return

    # Books
    books = [
        ('The Great Gatsby', 'F. Scott Fitzgerald', '978-0743273565', 'Fiction', 1925, 1),
        ('To Kill a Mockingbird', 'Harper Lee', '978-0446310789', 'Fiction', 1960, 1),
        ('1984', 'George Orwell', '978-0451524935', 'Dystopian', 1949, 1),
        ('Clean Code', 'Robert C. Martin', '978-0132350884', 'Technology', 2008, 1),
        ('The Pragmatic Programmer', 'David Thomas', '978-0135957059', 'Technology', 2019, 1),
    ]
    c.executemany("INSERT INTO books (title,author,isbn,genre,year,available) VALUES (?,?,?,?,?,?)", books)

    # Menu items
    menu = [
        ('Grilled Salmon', 'Fresh Atlantic salmon with herbs', 24.99, 'Main Course', 1, None),
        ('Caesar Salad', 'Crispy romaine with parmesan', 12.99, 'Appetizer', 1, None),
        ('Margherita Pizza', 'Classic tomato and mozzarella', 16.99, 'Main Course', 1, None),
        ('Chocolate Lava Cake', 'Warm chocolate cake with ice cream', 9.99, 'Dessert', 1, None),
        ('Espresso', 'Double shot Italian espresso', 4.99, 'Beverage', 1, None),
    ]
    c.executemany("INSERT INTO menu_items (name,description,price,category,is_available,image_url) VALUES (?,?,?,?,?,?)", menu)

    # Tasks
    tasks = [
        ('Setup Development Environment', 'Install Python, Node.js, and Docker', 'completed', 'high', '2026-03-01', 'Alaadin'),
        ('Design Database Schema', 'Create ERD and normalize tables', 'in_progress', 'high', '2026-03-05', 'Alaadin'),
        ('Write Unit Tests', 'Cover all API endpoints', 'pending', 'medium', '2026-03-10', None),
        ('Deploy to Production', 'Setup CI/CD pipeline', 'pending', 'high', '2026-03-15', None),
    ]
    c.executemany("INSERT INTO tasks (title,description,status,priority,due_date,assigned_to) VALUES (?,?,?,?,?,?)", tasks)

    # Students
    students = [
        ('Alice Johnson', 'alice@university.edu', 'STU001', 'Computer Science', 3.8, 2023),
        ('Bob Smith', 'bob@university.edu', 'STU002', 'Mathematics', 3.5, 2022),
        ('Carol White', 'carol@university.edu', 'STU003', 'Physics', 3.9, 2024),
    ]
    c.executemany("INSERT INTO students (name,email,student_id,major,gpa,enrollment_year) VALUES (?,?,?,?,?,?)", students)

    # Notes
    notes = [
        ('Meeting Notes', 'Discussed Q1 roadmap and sprint planning', 'Work', 1),
        ('Shopping List', 'Milk, bread, eggs, coffee', 'Personal', 0),
        ('API Design Tips', 'Use proper HTTP methods and status codes', 'Learning', 1),
    ]
    c.executemany("INSERT INTO notes (title,content,category,is_pinned) VALUES (?,?,?,?)", notes)

    # Blog posts
    posts = [
        ('Getting Started with REST APIs', 'REST (Representational State Transfer) is an architectural style for designing networked applications. In this guide, we will explore the fundamental concepts...', 'Admin', 'api,rest,beginner'),
        ('Understanding HTTP Methods', 'HTTP defines several methods indicating the desired action: GET retrieves data, POST creates resources, PUT updates, DELETE removes...', 'Admin', 'http,methods,tutorial'),
        ('API Security Best Practices', 'Securing your API is crucial. Always use HTTPS, implement proper authentication, validate inputs, and apply rate limiting...', 'Admin', 'security,api,best-practices'),
    ]
    c.executemany("INSERT INTO blog_posts (title,content,author,tags) VALUES (?,?,?,?)", posts)

    # Inventory
    inv = [
        ('Laptop', 'LAP-001', 50, 999.99, 'Electronics', 'Warehouse A'),
        ('Wireless Mouse', 'MOU-002', 200, 29.99, 'Accessories', 'Warehouse A'),
        ('USB-C Cable', 'CAB-003', 500, 9.99, 'Accessories', 'Warehouse B'),
        ('Monitor 27"', 'MON-004', 30, 349.99, 'Electronics', 'Warehouse A'),
    ]
    c.executemany("INSERT INTO inventory (name,sku,quantity,price,category,warehouse) VALUES (?,?,?,?,?,?)", inv)

    conn.commit()
