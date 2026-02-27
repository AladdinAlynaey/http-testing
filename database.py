"""
HTTP Playground v3.0 — Database Layer
20 Modules, Dual API Keys (standard + ai), Deep Freeze, 200+ seed records
"""
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'platform.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # ---------- USERS ----------
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ---------- API KEYS (dual: standard + ai) ----------
    c.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT UNIQUE NOT NULL,
        key_type TEXT NOT NULL DEFAULT 'standard',
        scope TEXT DEFAULT 'basic',
        request_count INTEGER DEFAULT 0,
        max_requests INTEGER DEFAULT 15,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    # Migration: add key_type if missing
    try:
        c.execute("SELECT key_type FROM api_keys LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE api_keys ADD COLUMN key_type TEXT NOT NULL DEFAULT 'standard'")

    # ---------- AUDIT LOGS ----------
    c.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        resource TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ---------- RATE LIMITS ----------
    c.execute("""CREATE TABLE IF NOT EXISTS rate_limits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ---------- LOGIN ATTEMPTS ----------
    c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        success INTEGER DEFAULT 0,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ---------- USER MODIFICATIONS (Deep Freeze tracking) ----------
    c.execute("""CREATE TABLE IF NOT EXISTS user_modifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        original_data TEXT,
        user_key TEXT,
        user_id INTEGER,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Migration: add user_id to user_modifications
    try:
        c.execute("SELECT user_id FROM user_modifications LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE user_modifications ADD COLUMN user_id INTEGER")

    # ================================================================
    # MODULE TABLES (20 modules)
    # ================================================================

    # 1. Books
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, author TEXT NOT NULL, isbn TEXT,
        genre TEXT, year INTEGER, available INTEGER DEFAULT 1,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 2. Menu Items
    c.execute("""CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, description TEXT, price REAL NOT NULL,
        category TEXT, is_available INTEGER DEFAULT 1,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 3. Tasks
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT,
        status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'medium',
        due_date TEXT, assigned_to TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 4. Students
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT, student_id TEXT,
        major TEXT, gpa REAL, enrollment_year INTEGER,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 5. Notes
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, content TEXT,
        category TEXT DEFAULT 'General', is_pinned INTEGER DEFAULT 0,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 6. Files
    c.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
        file_type TEXT, file_size INTEGER,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 7. Blog Posts
    c.execute("""CREATE TABLE IF NOT EXISTS blog_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, content TEXT NOT NULL,
        author TEXT, tags TEXT, is_published INTEGER DEFAULT 1,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 8. Inventory
    c.execute("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, sku TEXT, quantity INTEGER DEFAULT 0,
        price REAL, category TEXT, warehouse TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 9. Products (e-commerce)
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, description TEXT, price REAL NOT NULL,
        category TEXT, brand TEXT, rating REAL DEFAULT 0,
        stock INTEGER DEFAULT 0, image_url TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 10. Movies
    c.execute("""CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, director TEXT, genre TEXT,
        year INTEGER, rating REAL, runtime INTEGER,
        language TEXT DEFAULT 'English',
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 11. Recipes
    c.execute("""CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT, cuisine TEXT,
        difficulty TEXT DEFAULT 'easy', prep_time INTEGER,
        cook_time INTEGER, servings INTEGER, ingredients TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 12. Events
    c.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT, location TEXT,
        event_date TEXT, event_time TEXT, category TEXT,
        capacity INTEGER, organizer TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 13. Contacts
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL, last_name TEXT,
        email TEXT, phone TEXT, company TEXT,
        job_title TEXT, city TEXT, country TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 14. Music / Songs
    c.execute("""CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, artist TEXT NOT NULL,
        album TEXT, genre TEXT, duration INTEGER,
        year INTEGER, is_explicit INTEGER DEFAULT 0,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 15. Quotes
    c.execute("""CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL, author TEXT NOT NULL,
        category TEXT, language TEXT DEFAULT 'English',
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 16. Countries
    c.execute("""CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, capital TEXT, continent TEXT,
        population INTEGER, area_km2 REAL, currency TEXT,
        language TEXT, calling_code TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 17. Jokes
    c.execute("""CREATE TABLE IF NOT EXISTS jokes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setup TEXT NOT NULL, punchline TEXT NOT NULL,
        category TEXT DEFAULT 'general', rating REAL DEFAULT 0,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 18. Vehicles
    c.execute("""CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        make TEXT NOT NULL, model TEXT NOT NULL, year INTEGER,
        type TEXT, color TEXT, price REAL,
        fuel_type TEXT, mileage INTEGER,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 19. Courses (online learning)
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, instructor TEXT, category TEXT,
        level TEXT DEFAULT 'beginner', duration_hours REAL,
        price REAL, rating REAL DEFAULT 0, enrolled INTEGER DEFAULT 0,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # 20. Pets (pet adoption)
    c.execute("""CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, species TEXT NOT NULL, breed TEXT,
        age INTEGER, color TEXT, weight REAL,
        adopted INTEGER DEFAULT 0, shelter TEXT,
        is_frozen INTEGER DEFAULT 0, created_by_user INTEGER DEFAULT 0, created_by_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    _seed_data(conn)
    conn.close()


def _seed_data(conn):
    c = conn.cursor()

    # ---- Books (15) ----
    if c.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        books = [
            ('The Great Gatsby','F. Scott Fitzgerald','978-0743273565','Fiction',1925,1),
            ('1984','George Orwell','978-0451524935','Dystopian',1949,1),
            ('To Kill a Mockingbird','Harper Lee','978-0446310789','Fiction',1960,1),
            ('Clean Code','Robert C. Martin','978-0132350884','Technology',2008,1),
            ('The Pragmatic Programmer','David Thomas','978-0135957059','Technology',2019,1),
            ('Python Crash Course','Eric Matthes','978-1593279288','Technology',2019,1),
            ('A Brief History of Time','Stephen Hawking','978-0553380163','Science',1988,1),
            ('Sapiens','Yuval Noah Harari','978-0062316097','History',2014,1),
            ('Dune','Frank Herbert','978-0441172719','Science Fiction',1965,1),
            ('The Art of War','Sun Tzu','978-1599869773','Philosophy',500,1),
            ('Atomic Habits','James Clear','978-0735211292','Self-Help',2018,1),
            ('Deep Work','Cal Newport','978-1455586691','Self-Help',2016,1),
            ('The Lean Startup','Eric Ries','978-0307887894','Business',2011,1),
            ('Brave New World','Aldous Huxley','978-0060850524','Dystopian',1932,1),
            ('Think and Grow Rich','Napoleon Hill','978-1585424337','Business',1937,1),
        ]
        c.executemany("INSERT INTO books (title,author,isbn,genre,year,available,is_frozen) VALUES (?,?,?,?,?,?,1)", books)

    # ---- Menu Items (15) ----
    if c.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
        menu = [
            ('Grilled Salmon','Fresh Atlantic salmon with herbs',28.99,'Main Course',1),
            ('Caesar Salad','Crispy romaine with parmesan',12.99,'Appetizer',1),
            ('Chocolate Lava Cake','Warm molten chocolate center',9.99,'Dessert',1),
            ('Margherita Pizza','Classic tomato and mozzarella',16.99,'Main Course',1),
            ('Tiramisu','Italian coffee-flavored dessert',8.99,'Dessert',1),
            ('Beef Burger','Angus beef with cheddar',14.99,'Main Course',1),
            ('Mango Smoothie','Fresh tropical mango blend',6.99,'Beverage',1),
            ('Garlic Bread','Toasted with herb butter',5.99,'Appetizer',1),
            ('Grilled Chicken','Herb-marinated chicken breast',18.99,'Main Course',1),
            ('French Fries','Crispy golden fries',4.99,'Sides',1),
            ('Mushroom Soup','Creamy wild mushroom',7.99,'Appetizer',1),
            ('Iced Latte','Cold brew with milk',5.49,'Beverage',1),
            ('Pad Thai','Stir-fried rice noodles',15.99,'Main Course',1),
            ('Apple Pie','Classic American dessert',7.49,'Dessert',1),
            ('Fresh Orange Juice','Freshly squeezed',4.99,'Beverage',1),
        ]
        c.executemany("INSERT INTO menu_items (name,description,price,category,is_available,is_frozen) VALUES (?,?,?,?,?,1)", menu)

    # ---- Tasks (12) ----
    if c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        tasks = [
            ('Learn HTTP Methods','Understand GET, POST, PUT, DELETE','completed','high','2026-01-15','Student'),
            ('Practice CURL Commands','Run 10 CURL examples','in_progress','high','2026-02-01','Student'),
            ('Build REST API','Create a simple API with Flask','pending','medium','2026-03-01','Developer'),
            ('Study Authentication','Learn JWT and API keys','pending','high','2026-02-15','Student'),
            ('Database Design','Design schema for a web app','completed','medium','2026-01-20','Developer'),
            ('Write Unit Tests','Cover all endpoints','pending','medium','2026-03-10','Developer'),
            ('Deploy to Production','Set up server and domain','pending','high','2026-03-15','DevOps'),
            ('API Documentation','Write OpenAPI spec','in_progress','medium','2026-02-28','Developer'),
            ('Security Audit','Review all endpoints','pending','high','2026-03-20','Security'),
            ('Performance Testing','Load test the API','pending','low','2026-04-01','DevOps'),
            ('Code Review','Review pull requests','in_progress','medium','2026-02-25','Developer'),
            ('CI/CD Pipeline','Set up automated deployment','pending','medium','2026-03-25','DevOps'),
        ]
        c.executemany("INSERT INTO tasks (title,description,status,priority,due_date,assigned_to,is_frozen) VALUES (?,?,?,?,?,?,1)", tasks)

    # ---- Students (10) ----
    if c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        students = [
            ('Ahmed Al-Rashid','ahmed@uni.edu','STU-2024-001','Computer Science',3.85,2024),
            ('Sara Johnson','sara.j@uni.edu','STU-2023-015','Data Science',3.92,2023),
            ('Omar Hassan','omar.h@uni.edu','STU-2024-008','Software Engineering',3.45,2024),
            ('Fatima Al-Zahra','fatima@uni.edu','STU-2022-030','Cybersecurity',3.78,2022),
            ('John Smith','john.s@uni.edu','STU-2023-022','Computer Science',3.60,2023),
            ('Layla Ibrahim','layla@uni.edu','STU-2024-011','AI & ML',3.95,2024),
            ('Carlos Rodriguez','carlos@uni.edu','STU-2023-045','Web Development',3.50,2023),
            ('Aisha Patel','aisha@uni.edu','STU-2024-003','Database Systems',3.70,2024),
            ('Wei Zhang','wei.z@uni.edu','STU-2022-018','Cloud Computing',3.88,2022),
            ('Emma Wilson','emma.w@uni.edu','STU-2024-025','Network Security',3.65,2024),
        ]
        c.executemany("INSERT INTO students (name,email,student_id,major,gpa,enrollment_year,is_frozen) VALUES (?,?,?,?,?,?,1)", students)

    # ---- Notes (8) ----
    if c.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
        notes = [
            ('HTTP Methods Overview','GET=Read, POST=Create, PUT=Update, DELETE=Remove','Learning',1),
            ('REST API Best Practices','Use nouns for resources, HTTP verbs for actions','Work',1),
            ('CURL Cheat Sheet','curl -X POST -H header -d data URL','Learning',0),
            ('Status Codes','200=OK, 201=Created, 400=Bad Request, 401=Unauthorized, 404=Not Found, 500=Server Error','Learning',1),
            ('Authentication Types','Basic Auth, Bearer Token, API Key, OAuth2','Learning',0),
            ('JSON Format','Key-value pairs with strings, numbers, arrays, objects','Learning',0),
            ('Project Ideas','Build a todo API, weather dashboard, blog platform','Ideas',0),
            ('Security Notes','Always validate input, use HTTPS, sanitize data','Work',1),
        ]
        c.executemany("INSERT INTO notes (title,content,category,is_pinned,is_frozen) VALUES (?,?,?,?,1)", notes)

    # ---- Blog Posts (6) ----
    if c.execute("SELECT COUNT(*) FROM blog_posts").fetchone()[0] == 0:
        posts = [
            ('Getting Started with REST APIs','REST APIs use HTTP methods to perform CRUD operations on resources. This guide covers the basics of building and consuming RESTful services.','Tech Team','api,rest,beginner',1),
            ('CURL for Beginners','CURL is a command-line tool for making HTTP requests. Learn how to use it for testing APIs with practical examples.','Tech Team','curl,tutorial,http',1),
            ('Understanding HTTP Status Codes','Status codes tell you what happened with your request. Learn the difference between 2xx, 3xx, 4xx, and 5xx responses.','Tech Team','http,status-codes,tutorial',1),
            ('API Authentication Deep Dive','Compare different authentication methods: API keys, JWT tokens, OAuth2, and when to use each one.','Tech Team','security,auth,api-keys',1),
            ('Building Your First API','Step-by-step guide to building a REST API with Flask, including routing, error handling, and data validation.','Tech Team','flask,python,tutorial',1),
            ('API Security Best Practices','Protect your APIs with rate limiting, input validation, CORS, and proper authentication.','Tech Team','security,best-practices',1),
        ]
        c.executemany("INSERT INTO blog_posts (title,content,author,tags,is_published,is_frozen) VALUES (?,?,?,?,?,1)", posts)

    # ---- Inventory (12) ----
    if c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == 0:
        inv = [
            ('Mechanical Keyboard','KB-001',150,89.99,'Electronics','Warehouse A'),
            ('Wireless Mouse','MS-002',200,34.99,'Electronics','Warehouse A'),
            ('USB-C Hub','HB-003',75,49.99,'Electronics','Warehouse B'),
            ('Monitor Stand','ST-004',50,29.99,'Furniture','Warehouse B'),
            ('Webcam HD 1080p','WC-005',100,59.99,'Electronics','Warehouse A'),
            ('Desk Lamp LED','LM-006',80,24.99,'Furniture','Warehouse C'),
            ('Laptop Sleeve 15"','SL-007',200,19.99,'Accessories','Warehouse C'),
            ('Ethernet Cable 2m','EC-008',500,7.99,'Cables','Warehouse A'),
            ('Power Strip 6-port','PS-009',120,15.99,'Electronics','Warehouse B'),
            ('Screen Cleaner Kit','CL-010',300,9.99,'Accessories','Warehouse C'),
            ('HDMI Cable 3m','HD-011',250,12.99,'Cables','Warehouse A'),
            ('Mouse Pad XL','MP-012',180,14.99,'Accessories','Warehouse B'),
        ]
        c.executemany("INSERT INTO inventory (name,sku,quantity,price,category,warehouse,is_frozen) VALUES (?,?,?,?,?,?,1)", inv)

    # ---- Products (10) ----
    if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ('Wireless Earbuds Pro','Active noise cancellation, 30h battery',79.99,'Audio','SoundMax',4.7,500,None),
            ('Smart Watch X','Heart rate, GPS, water resistant',199.99,'Wearables','TechWear',4.5,300,None),
            ('Bluetooth Speaker','360° surround, IPX7 waterproof',49.99,'Audio','SoundMax',4.3,800,None),
            ('Laptop Backpack','Anti-theft, USB charging port',39.99,'Bags','TravelPro',4.6,600,None),
            ('Portable Charger 20K','Fast charging, dual USB-C',29.99,'Electronics','PowerUp',4.4,1000,None),
            ('Yoga Mat Premium','Non-slip, eco-friendly, 6mm',24.99,'Fitness','FitLife',4.8,400,None),
            ('LED Desk Lamp','Touch control, adjustable brightness',34.99,'Home','BrightLight',4.2,350,None),
            ('Mechanical Pencil Set','0.5mm, 0.7mm with leads',12.99,'Stationery','WriteWell',4.1,900,None),
            ('Water Bottle 1L','Insulated, keeps cold 24h',19.99,'Accessories','HydroFlow',4.5,700,None),
            ('Phone Stand','Adjustable, foldable, aluminum',15.99,'Electronics','TechGear',4.3,1200,None),
        ]
        c.executemany("INSERT INTO products (name,description,price,category,brand,rating,stock,image_url,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", products)

    # ---- Movies (10) ----
    if c.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 0:
        movies = [
            ('The Shawshank Redemption','Frank Darabont','Drama',1994,9.3,142,'English'),
            ('Inception','Christopher Nolan','Sci-Fi',2010,8.8,148,'English'),
            ('Parasite','Bong Joon-ho','Thriller',2019,8.5,132,'Korean'),
            ('The Dark Knight','Christopher Nolan','Action',2008,9.0,152,'English'),
            ('Spirited Away','Hayao Miyazaki','Animation',2001,8.6,125,'Japanese'),
            ('Interstellar','Christopher Nolan','Sci-Fi',2014,8.7,169,'English'),
            ('The Godfather','Francis Ford Coppola','Crime',1972,9.2,175,'English'),
            ('Pulp Fiction','Quentin Tarantino','Crime',1994,8.9,154,'English'),
            ('Coco','Lee Unkrich','Animation',2017,8.4,105,'English'),
            ('The Matrix','The Wachowskis','Sci-Fi',1999,8.7,136,'English'),
        ]
        c.executemany("INSERT INTO movies (title,director,genre,year,rating,runtime,language,is_frozen) VALUES (?,?,?,?,?,?,?,1)", movies)

    # ---- Recipes (8) ----
    if c.execute("SELECT COUNT(*) FROM recipes").fetchone()[0] == 0:
        recipes = [
            ('Spaghetti Carbonara','Classic Italian pasta with egg and bacon','Italian','easy',10,20,4,'spaghetti,eggs,bacon,parmesan,black pepper'),
            ('Chicken Stir Fry','Quick and healthy Asian-style dish','Asian','easy',15,10,2,'chicken,soy sauce,vegetables,rice,ginger'),
            ('Beef Tacos','Mexican street-style tacos','Mexican','easy',15,15,4,'beef,tortillas,salsa,onion,cilantro'),
            ('Mushroom Risotto','Creamy Italian rice dish','Italian','medium',10,30,3,'arborio rice,mushrooms,parmesan,butter,broth'),
            ('Greek Salad','Fresh Mediterranean salad','Mediterranean','easy',10,0,2,'tomatoes,cucumber,feta,olives,olive oil'),
            ('Pad Thai','Thai stir-fried noodles','Thai','medium',20,15,3,'rice noodles,shrimp,peanuts,bean sprouts,lime'),
            ('Banana Pancakes','Fluffy breakfast pancakes','American','easy',5,15,2,'bananas,eggs,flour,butter,maple syrup'),
            ('Tom Kha Gai','Thai coconut chicken soup','Thai','medium',15,25,4,'chicken,coconut milk,galangal,lemongrass,mushrooms'),
        ]
        c.executemany("INSERT INTO recipes (title,description,cuisine,difficulty,prep_time,cook_time,servings,ingredients,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", recipes)

    # ---- Events (8) ----
    if c.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        events = [
            ('Tech Conference 2026','Annual technology summit','Convention Center','2026-06-15','09:00','Technology',500,'TechOrg'),
            ('Web Dev Workshop','Hands-on Flask & React workshop','Room 204','2026-04-10','14:00','Workshop',30,'CodeAcademy'),
            ('AI Hackathon','24-hour AI challenge','Innovation Hub','2026-05-20','08:00','Hackathon',100,'AI Society'),
            ('Networking Mixer','Meet fellow developers','Rooftop Lounge','2026-03-28','18:00','Social',75,'DevCommunity'),
            ('Security Seminar','Cybersecurity best practices','Auditorium B','2026-04-25','10:00','Seminar',200,'SecureIT'),
            ('Open Source Day','Contributing to open source','Lab 3','2026-05-05','09:00','Workshop',40,'OSS Foundation'),
            ('Career Fair','Tech companies recruiting','Main Hall','2026-06-01','10:00','Career',300,'University'),
            ('API Design Masterclass','RESTful API design patterns','Online','2026-04-18','16:00','Masterclass',50,'APIguru'),
        ]
        c.executemany("INSERT INTO events (title,description,location,event_date,event_time,category,capacity,organizer,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", events)

    # ---- Contacts (10) ----
    if c.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] == 0:
        contacts = [
            ('Alice','Johnson','alice@example.com','+1-555-0101','Google','Software Engineer','San Francisco','USA'),
            ('Bob','Smith','bob@example.com','+44-20-7946-0958','Microsoft','Product Manager','London','UK'),
            ('Yuki','Tanaka','yuki@example.com','+81-3-1234-5678','Sony','Designer','Tokyo','Japan'),
            ('Ahmed','Hassan','ahmed@example.com','+971-50-123-4567','Emirates','Data Analyst','Dubai','UAE'),
            ('Maria','Garcia','maria@example.com','+34-91-123-4567','Telefonica','Developer','Madrid','Spain'),
            ('Chen','Wei','chen@example.com','+86-10-1234-5678','Alibaba','CTO','Beijing','China'),
            ('Fatima','Al-Sayed','fatima@example.com','+966-50-123-4567','Aramco','Engineer','Riyadh','Saudi Arabia'),
            ('James','Wilson','james@example.com','+61-2-1234-5678','Canva','Frontend Dev','Sydney','Australia'),
            ('Priya','Sharma','priya@example.com','+91-98-1234-5678','Infosys','Backend Dev','Mumbai','India'),
            ('Lucas','Mueller','lucas@example.com','+49-30-1234-5678','SAP','DevOps','Berlin','Germany'),
        ]
        c.executemany("INSERT INTO contacts (first_name,last_name,email,phone,company,job_title,city,country,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", contacts)

    # ---- Songs (10) ----
    if c.execute("SELECT COUNT(*) FROM songs").fetchone()[0] == 0:
        songs = [
            ('Bohemian Rhapsody','Queen','A Night at the Opera','Rock',354,1975,0),
            ('Blinding Lights','The Weeknd','After Hours','Pop',200,2020,0),
            ('Shape of You','Ed Sheeran','÷ (Divide)','Pop',234,2017,0),
            ('Lose Yourself','Eminem','8 Mile OST','Hip Hop',326,2002,1),
            ('Hotel California','Eagles','Hotel California','Rock',391,1977,0),
            ('Billie Jean','Michael Jackson','Thriller','Pop',294,1983,0),
            ('Despacito','Luis Fonsi','Vida','Latin Pop',228,2017,0),
            ('Stairway to Heaven','Led Zeppelin','Led Zeppelin IV','Rock',482,1971,0),
            ('Rolling in the Deep','Adele','21','Soul',228,2011,0),
            ('Imagine','John Lennon','Imagine','Rock',187,1971,0),
        ]
        c.executemany("INSERT INTO songs (title,artist,album,genre,duration,year,is_explicit,is_frozen) VALUES (?,?,?,?,?,?,?,1)", songs)

    # ---- Quotes (10) ----
    if c.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0:
        quotes = [
            ('The only way to do great work is to love what you do.','Steve Jobs','Motivation','English'),
            ('Talk is cheap. Show me the code.','Linus Torvalds','Programming','English'),
            ('First, solve the problem. Then, write the code.','John Johnson','Programming','English'),
            ('Any fool can write code that a computer can understand. Good programmers write code that humans can understand.','Martin Fowler','Programming','English'),
            ('The best time to plant a tree was 20 years ago. The second best time is now.','Chinese Proverb','Wisdom','English'),
            ('In the middle of difficulty lies opportunity.','Albert Einstein','Motivation','English'),
            ('Simplicity is the soul of efficiency.','Austin Freeman','Programming','English'),
            ('Code is like humor. When you have to explain it, it is bad.','Cory House','Programming','English'),
            ('The function of good software is to make the complex appear to be simple.','Grady Booch','Programming','English'),
            ('It always seems impossible until it is done.','Nelson Mandela','Motivation','English'),
        ]
        c.executemany("INSERT INTO quotes (text,author,category,language,is_frozen) VALUES (?,?,?,?,1)", quotes)

    # ---- Countries (10) ----
    if c.execute("SELECT COUNT(*) FROM countries").fetchone()[0] == 0:
        countries = [
            ('United States','Washington D.C.','North America',331000000,9833520,'USD','English','+1'),
            ('United Kingdom','London','Europe',67800000,242495,'GBP','English','+44'),
            ('Japan','Tokyo','Asia',125700000,377975,'JPY','Japanese','+81'),
            ('United Arab Emirates','Abu Dhabi','Asia',9900000,83600,'AED','Arabic','+971'),
            ('Germany','Berlin','Europe',83200000,357022,'EUR','German','+49'),
            ('Brazil','Brasilia','South America',212600000,8515767,'BRL','Portuguese','+55'),
            ('Australia','Canberra','Oceania',25700000,7692024,'AUD','English','+61'),
            ('India','New Delhi','Asia',1380000000,3287263,'INR','Hindi','+91'),
            ('Saudi Arabia','Riyadh','Asia',34800000,2149690,'SAR','Arabic','+966'),
            ('South Korea','Seoul','Asia',51800000,100210,'KRW','Korean','+82'),
        ]
        c.executemany("INSERT INTO countries (name,capital,continent,population,area_km2,currency,language,calling_code,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", countries)

    # ---- Jokes (8) ----
    if c.execute("SELECT COUNT(*) FROM jokes").fetchone()[0] == 0:
        jokes = [
            ('Why do programmers prefer dark mode?','Because light attracts bugs!','programming',4.5),
            ('What is a programmer\'s favorite hangout place?','Foo Bar!','programming',3.8),
            ('Why was the JavaScript developer sad?','Because he didn\'t Node how to Express himself.','programming',4.2),
            ('What did the server say to the client?','HTTP 200 — everything is OK!','programming',3.5),
            ('Why do Java developers wear glasses?','Because they can\'t C#!','programming',4.0),
            ('How many programmers does it take to change a light bulb?','None — that\'s a hardware problem!','programming',4.3),
            ('What\'s a computer\'s favorite snack?','Microchips!','general',3.2),
            ('Why did the API go to therapy?','It had too many unresolved issues.','programming',4.1),
        ]
        c.executemany("INSERT INTO jokes (setup,punchline,category,rating,is_frozen) VALUES (?,?,?,?,1)", jokes)

    # ---- Vehicles (8) ----
    if c.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 0:
        vehicles = [
            ('Toyota','Camry',2024,'Sedan','White',28000,'Gasoline',0),
            ('Tesla','Model 3',2024,'Sedan','Black',42000,'Electric',0),
            ('BMW','X5',2023,'SUV','Blue',62000,'Gasoline',35000),
            ('Honda','Civic',2024,'Sedan','Silver',26000,'Gasoline',0),
            ('Ford','F-150',2024,'Truck','Red',55000,'Gasoline',0),
            ('Mercedes','C-Class',2023,'Sedan','Gray',45000,'Gasoline',20000),
            ('Audi','Q7',2024,'SUV','Black',70000,'Gasoline',0),
            ('Hyundai','Ioniq 5',2024,'SUV','Green',45000,'Electric',0),
        ]
        c.executemany("INSERT INTO vehicles (make,model,year,type,color,price,fuel_type,mileage,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", vehicles)

    # ---- Courses (8) ----
    if c.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        courses = [
            ('Python for Beginners','Dr. Sarah Chen','Programming','beginner',12.5,0,4.8,5200),
            ('Web Development Bootcamp','John Doe','Web Development','intermediate',48.0,49.99,4.7,12000),
            ('Data Science with Python','Prof. Alex Kim','Data Science','intermediate',30.0,39.99,4.6,8500),
            ('Machine Learning A-Z','Dr. Lisa Wang','AI & ML','advanced',40.0,59.99,4.9,15000),
            ('JavaScript Mastery','Chris Brown','Programming','beginner',20.0,29.99,4.5,9800),
            ('DevOps Engineering','Mike Johnson','DevOps','advanced',35.0,44.99,4.4,3200),
            ('Cybersecurity Fundamentals','Prof. Omar Ali','Security','beginner',15.0,0,4.7,7600),
            ('Cloud Computing with AWS','Emily Davis','Cloud','intermediate',25.0,34.99,4.3,4100),
        ]
        c.executemany("INSERT INTO courses (title,instructor,category,level,duration_hours,price,rating,enrolled,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", courses)

    # ---- Pets (8) ----
    if c.execute("SELECT COUNT(*) FROM pets").fetchone()[0] == 0:
        pets = [
            ('Buddy','Dog','Golden Retriever',3,'Golden',30.5,0,'Happy Paws Shelter'),
            ('Whiskers','Cat','Persian',2,'White',4.2,0,'Cat Haven'),
            ('Max','Dog','German Shepherd',5,'Black & Tan',35.0,1,'City Animal Rescue'),
            ('Luna','Cat','Siamese',1,'Cream',3.5,0,'Cat Haven'),
            ('Charlie','Dog','Labrador',4,'Chocolate',28.0,0,'Happy Paws Shelter'),
            ('Bella','Cat','Maine Coon',3,'Tabby',5.8,1,'Feline Friends'),
            ('Rocky','Dog','Bulldog',2,'Brindle',22.0,0,'City Animal Rescue'),
            ('Milo','Cat','British Shorthair',1,'Gray',4.0,0,'Feline Friends'),
        ]
        c.executemany("INSERT INTO pets (name,species,breed,age,color,weight,adopted,shelter,is_frozen) VALUES (?,?,?,?,?,?,?,?,1)", pets)

    conn.commit()
