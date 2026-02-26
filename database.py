"""
Database module - SQLite initialization, deep freeze support, and rich seed data
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

    # API Keys table (with usage tracking)
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT UNIQUE NOT NULL,
        scope TEXT NOT NULL DEFAULT 'basic',
        is_active INTEGER DEFAULT 1,
        request_count INTEGER DEFAULT 0,
        max_requests INTEGER DEFAULT 20,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Migrate: add request_count / max_requests if missing
    try:
        c.execute("SELECT request_count FROM api_keys LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE api_keys ADD COLUMN request_count INTEGER DEFAULT 0")
        c.execute("ALTER TABLE api_keys ADD COLUMN max_requests INTEGER DEFAULT 20")

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

    # ===== DEEP FREEZE: User modifications tracking =====
    c.execute('''CREATE TABLE IF NOT EXISTS user_modifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        api_key_id INTEGER,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        original_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )''')

    # ===== APPLICATION MODULE TABLES =====
    # All tables have: is_frozen (baseline data), created_by_user (who created), created_by_key (which API key)

    # 1. Library
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT,
        genre TEXT,
        year INTEGER,
        available INTEGER DEFAULT 1,
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 5. Notes
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        category TEXT,
        is_pinned INTEGER DEFAULT 0,
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
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
        is_frozen INTEGER DEFAULT 0,
        created_by_user INTEGER,
        created_by_key INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()

    # Migrate existing tables: add new columns if missing
    _migrate_columns(conn)

    # Seed sample data
    _seed_data(conn)
    conn.close()


def _migrate_columns(conn):
    """Add is_frozen, created_by_user, created_by_key columns to existing tables"""
    tables = ['books', 'menu_items', 'tasks', 'students', 'notes', 'files', 'blog_posts', 'inventory']
    for table in tables:
        for col, default in [('is_frozen', '0'), ('created_by_user', 'NULL'), ('created_by_key', 'NULL')]:
            try:
                conn.execute(f"SELECT {col} FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} INTEGER DEFAULT {default}")
    conn.commit()
    # Mark all existing data as frozen
    for table in tables:
        conn.execute(f"UPDATE {table} SET is_frozen = 1 WHERE is_frozen = 0 AND created_by_user IS NULL")
    conn.commit()


def _seed_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] > 0:
        return

    # ==================== BOOKS (15) ====================
    books = [
        ('The Great Gatsby', 'F. Scott Fitzgerald', '978-0743273565', 'Fiction', 1925, 1),
        ('To Kill a Mockingbird', 'Harper Lee', '978-0446310789', 'Fiction', 1960, 1),
        ('1984', 'George Orwell', '978-0451524935', 'Dystopian', 1949, 1),
        ('Clean Code', 'Robert C. Martin', '978-0132350884', 'Technology', 2008, 1),
        ('The Pragmatic Programmer', 'David Thomas', '978-0135957059', 'Technology', 2019, 1),
        ('Sapiens', 'Yuval Noah Harari', '978-0062316097', 'History', 2014, 1),
        ('Atomic Habits', 'James Clear', '978-0735211292', 'Self-Help', 2018, 1),
        ('The Art of War', 'Sun Tzu', '978-1599869773', 'Philosophy', -500, 1),
        ('Dune', 'Frank Herbert', '978-0441013593', 'Science Fiction', 1965, 1),
        ('Python Crash Course', 'Eric Matthes', '978-1593279288', 'Technology', 2019, 1),
        ('The Alchemist', 'Paulo Coelho', '978-0062315007', 'Fiction', 1988, 1),
        ('Brave New World', 'Aldous Huxley', '978-0060850524', 'Dystopian', 1932, 1),
        ('Introduction to Algorithms', 'Thomas Cormen', '978-0262033848', 'Technology', 2009, 1),
        ('A Brief History of Time', 'Stephen Hawking', '978-0553380163', 'Science', 1988, 1),
        ('The Lean Startup', 'Eric Ries', '978-0307887894', 'Business', 2011, 1),
    ]
    c.executemany("INSERT INTO books (title,author,isbn,genre,year,available,is_frozen) VALUES (?,?,?,?,?,?,1)", books)

    # ==================== MENU (15) ====================
    menu = [
        ('Grilled Salmon', 'Fresh Atlantic salmon with herbs and lemon butter', 24.99, 'Main Course', 1, None),
        ('Caesar Salad', 'Crispy romaine with parmesan and croutons', 12.99, 'Appetizer', 1, None),
        ('Margherita Pizza', 'Classic tomato, mozzarella, and fresh basil', 16.99, 'Main Course', 1, None),
        ('Chocolate Lava Cake', 'Warm chocolate cake with vanilla ice cream', 9.99, 'Dessert', 1, None),
        ('Espresso', 'Double shot Italian espresso', 4.99, 'Beverage', 1, None),
        ('Beef Burger', 'Angus beef with cheddar, lettuce, and special sauce', 18.99, 'Main Course', 1, None),
        ('Chicken Shawarma', 'Marinated chicken with garlic sauce and pickles', 14.99, 'Main Course', 1, None),
        ('Tom Yum Soup', 'Spicy Thai soup with shrimp and mushrooms', 11.99, 'Appetizer', 1, None),
        ('Tiramisu', 'Classic Italian coffee-flavored dessert', 8.99, 'Dessert', 1, None),
        ('Fresh Lemonade', 'Freshly squeezed lemonade with mint', 5.99, 'Beverage', 1, None),
        ('Falafel Plate', 'Crispy falafel with hummus and tahini', 12.99, 'Main Course', 1, None),
        ('Mango Smoothie', 'Fresh mango blended with yogurt', 7.99, 'Beverage', 1, None),
        ('Bruschetta', 'Toasted bread with tomatoes, basil, and olive oil', 9.99, 'Appetizer', 1, None),
        ('Sushi Roll Set', 'Assorted sushi rolls with wasabi and ginger', 22.99, 'Main Course', 1, None),
        ('Apple Pie', 'Warm homemade apple pie with cinnamon', 7.99, 'Dessert', 1, None),
    ]
    c.executemany("INSERT INTO menu_items (name,description,price,category,is_available,image_url,is_frozen) VALUES (?,?,?,?,?,?,1)", menu)

    # ==================== TASKS (12) ====================
    tasks = [
        ('Setup Development Environment', 'Install Python, Node.js, and Docker', 'completed', 'high', '2026-03-01', 'Alaadin'),
        ('Design Database Schema', 'Create ERD and normalize tables', 'in_progress', 'high', '2026-03-05', 'Alaadin'),
        ('Write Unit Tests', 'Cover all API endpoints with tests', 'pending', 'medium', '2026-03-10', None),
        ('Deploy to Production', 'Setup CI/CD pipeline and deploy', 'pending', 'high', '2026-03-15', None),
        ('Create API Documentation', 'Write comprehensive docs with examples', 'completed', 'medium', '2026-03-01', 'Sara'),
        ('Implement Authentication', 'Add JWT and API key auth', 'completed', 'high', '2026-02-28', 'Alaadin'),
        ('Setup Monitoring', 'Add logging and error tracking', 'pending', 'low', '2026-03-20', None),
        ('Optimize Database Queries', 'Add indexes and optimize slow queries', 'in_progress', 'medium', '2026-03-08', 'Ahmed'),
        ('Code Review', 'Review pull requests from team', 'pending', 'medium', '2026-03-12', 'Sara'),
        ('Security Audit', 'Run security checks and fix vulnerabilities', 'pending', 'high', '2026-03-18', None),
        ('Write README', 'Create comprehensive project documentation', 'completed', 'low', '2026-02-25', 'Alaadin'),
        ('Load Testing', 'Test application under high concurrency', 'in_progress', 'medium', '2026-03-10', 'Ahmed'),
    ]
    c.executemany("INSERT INTO tasks (title,description,status,priority,due_date,assigned_to,is_frozen) VALUES (?,?,?,?,?,?,1)", tasks)

    # ==================== STUDENTS (10) ====================
    students = [
        ('Alice Johnson', 'alice@university.edu', 'STU001', 'Computer Science', 3.8, 2023),
        ('Bob Smith', 'bob@university.edu', 'STU002', 'Mathematics', 3.5, 2022),
        ('Carol White', 'carol@university.edu', 'STU003', 'Physics', 3.9, 2024),
        ('David Brown', 'david@university.edu', 'STU004', 'Artificial Intelligence', 3.7, 2023),
        ('Eva Martinez', 'eva@university.edu', 'STU005', 'Computer Science', 3.6, 2024),
        ('Frank Lee', 'frank@university.edu', 'STU006', 'Engineering', 3.4, 2022),
        ('Grace Kim', 'grace@university.edu', 'STU007', 'Data Science', 3.95, 2023),
        ('Hassan Ali', 'hassan@university.edu', 'STU008', 'Computer Science', 3.2, 2024),
        ('Iris Chen', 'iris@university.edu', 'STU009', 'Mathematics', 3.85, 2023),
        ('James Wilson', 'james@university.edu', 'STU010', 'Physics', 3.1, 2022),
    ]
    c.executemany("INSERT INTO students (name,email,student_id,major,gpa,enrollment_year,is_frozen) VALUES (?,?,?,?,?,?,1)", students)

    # ==================== NOTES (8) ====================
    notes = [
        ('Meeting Notes', 'Discussed Q1 roadmap and sprint planning. Action items: finalize API design, setup CI/CD, review security policy.', 'Work', 1),
        ('Shopping List', 'Milk, bread, eggs, coffee, pasta, olive oil, tomatoes', 'Personal', 0),
        ('API Design Tips', 'Use proper HTTP methods and status codes. Always version your APIs. Document everything.', 'Learning', 1),
        ('Project Ideas', 'Build a weather dashboard, Create a task management API, Design a blog platform with AI', 'Ideas', 0),
        ('Git Commands', 'git rebase -i HEAD~3, git stash pop, git cherry-pick <hash>, git bisect start', 'Learning', 1),
        ('Book Recommendations', 'Clean Code, Design Patterns, Refactoring, The Phoenix Project, Staff Engineer', 'Personal', 0),
        ('Sprint Retrospective', 'What went well: API deployment. What to improve: test coverage. Action: add integration tests.', 'Work', 1),
        ('Docker Cheatsheet', 'docker build -t app . | docker run -p 5000:5000 app | docker compose up -d', 'Learning', 1),
    ]
    c.executemany("INSERT INTO notes (title,content,category,is_pinned,is_frozen) VALUES (?,?,?,?,1)", notes)

    # ==================== BLOG POSTS (6) ====================
    posts = [
        ('Getting Started with REST APIs', 'REST (Representational State Transfer) is an architectural style for designing networked applications. In this guide, we explore GET, POST, PUT, DELETE methods and how they map to CRUD operations. Every API interaction follows a request-response pattern over HTTP.', 'Admin', 'api,rest,beginner'),
        ('Understanding HTTP Methods', 'HTTP defines several methods indicating the desired action: GET retrieves data without side effects, POST creates new resources, PUT updates existing resources entirely, PATCH updates partially, and DELETE removes resources. Each has specific semantics and safety guarantees.', 'Admin', 'http,methods,tutorial'),
        ('API Security Best Practices', 'Securing your API is crucial. Always use HTTPS, implement proper authentication with JWT or API keys, validate all inputs, apply rate limiting, use parameterized queries to prevent SQL injection, and set proper CORS headers.', 'Admin', 'security,api,best-practices'),
        ('CURL Tutorial for Beginners', 'CURL is a command-line tool for making HTTP requests. Start with simple GET requests: curl https://api.example.com/data. Add headers with -H flag, send POST data with -d flag, and use -X to specify the HTTP method.', 'Admin', 'curl,tutorial,beginner'),
        ('API Automation with n8n', 'n8n is an open-source workflow automation tool. Connect HTTP Request nodes to any API endpoint, chain multiple requests, add conditional logic, and schedule automated workflows. Perfect for monitoring, data sync, and alerts.', 'Admin', 'n8n,automation,workflow'),
        ('Introduction to AI APIs', 'Modern AI APIs like OpenRouter provide access to powerful language models. Send a prompt via POST request and receive generated text. Use cases include chatbots, content generation, text classification, summarization, and translation.', 'Admin', 'ai,openrouter,api'),
    ]
    c.executemany("INSERT INTO blog_posts (title,content,author,tags,is_frozen) VALUES (?,?,?,?,1)", posts)

    # ==================== INVENTORY (12) ====================
    inv = [
        ('Laptop Pro 16', 'LAP-001', 50, 999.99, 'Electronics', 'Warehouse A'),
        ('Wireless Mouse', 'MOU-002', 200, 29.99, 'Accessories', 'Warehouse A'),
        ('USB-C Cable', 'CAB-003', 500, 9.99, 'Accessories', 'Warehouse B'),
        ('Monitor 27"', 'MON-004', 30, 349.99, 'Electronics', 'Warehouse A'),
        ('Mechanical Keyboard', 'KEY-005', 150, 79.99, 'Accessories', 'Warehouse B'),
        ('Webcam HD', 'WEB-006', 100, 49.99, 'Electronics', 'Warehouse A'),
        ('Desk Lamp LED', 'LMP-007', 75, 34.99, 'Office', 'Warehouse B'),
        ('Notebook A5', 'NTB-008', 300, 4.99, 'Office', 'Warehouse B'),
        ('Standing Desk', 'DSK-009', 20, 599.99, 'Office', 'Warehouse A'),
        ('Wireless Headphones', 'HPH-010', 80, 149.99, 'Electronics', 'Warehouse A'),
        ('Printer Ink Set', 'INK-011', 5, 39.99, 'Office', 'Warehouse B'),
        ('External SSD 1TB', 'SSD-012', 60, 119.99, 'Electronics', 'Warehouse A'),
    ]
    c.executemany("INSERT INTO inventory (name,sku,quantity,price,category,warehouse,is_frozen) VALUES (?,?,?,?,?,?,1)", inv)

    conn.commit()
