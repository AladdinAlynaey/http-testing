"""
Deep Freeze System — Per-user sandboxes with auto-revert

Rules:
- POST (user creates) → auto-deleted after 2 hours
- PUT (user modifies) → reverts to original after 1 hour
- DELETE (user deletes) → item restored after 1 hour
- Frozen (baseline) data is never permanently modified
- Superadmin can add permanent frozen data
"""
import json
import threading
import time
from datetime import datetime, timedelta
from database import get_db

# Module table names for reference
MODULE_TABLES = [
    'books', 'menu_items', 'tasks', 'students', 'notes', 'files', 'blog_posts', 'inventory',
    'products', 'movies', 'recipes', 'events', 'contacts', 'songs', 'quotes', 'countries',
    'jokes', 'vehicles', 'courses', 'pets'
]

# Table column definitions for restoration
TABLE_COLUMNS = {
    'books': ['title', 'author', 'isbn', 'genre', 'year', 'available'],
    'menu_items': ['name', 'description', 'price', 'category', 'is_available', 'image_url'],
    'tasks': ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to'],
    'students': ['name', 'email', 'student_id', 'major', 'gpa', 'enrollment_year'],
    'notes': ['title', 'content', 'category', 'is_pinned'],
    'files': ['filename', 'original_name', 'file_type', 'file_size', 'uploaded_by'],
    'blog_posts': ['title', 'content', 'author', 'tags', 'is_published'],
    'inventory': ['name', 'sku', 'quantity', 'price', 'category', 'warehouse'],
    'products': ['name', 'description', 'price', 'category', 'brand', 'rating', 'stock', 'image_url'],
    'movies': ['title', 'director', 'genre', 'year', 'rating', 'runtime', 'language', 'plot'],
    'recipes': ['title', 'description', 'cuisine', 'difficulty', 'prep_time', 'cook_time', 'servings', 'ingredients'],
    'events': ['title', 'description', 'location', 'event_date', 'event_time', 'category', 'capacity', 'organizer'],
    'contacts': ['first_name', 'last_name', 'email', 'phone', 'company', 'job_title', 'city', 'country'],
    'songs': ['title', 'artist', 'album', 'genre', 'duration', 'year', 'explicit'],
    'quotes': ['text', 'author', 'category', 'language'],
    'countries': ['name', 'capital', 'continent', 'population', 'area_km2', 'currency', 'language'],
    'jokes': ['setup', 'punchline', 'category', 'rating'],
    'vehicles': ['make', 'model', 'year', 'type', 'color', 'price', 'fuel_type', 'mileage'],
    'courses': ['title', 'instructor', 'category', 'level', 'duration_hours', 'price', 'rating', 'enrolled'],
    'pets': ['name', 'species', 'breed', 'age', 'color', 'weight', 'shelter', 'adopted'],
}


def track_modification(table_name, record_id, action, original_data=None, user_id=None, api_key_id=None):
    """
    Track a user's modification for deep freeze auto-revert.
    action: 'create', 'update', 'delete'
    """
    db = get_db()
    if action == 'create':
        expires = datetime.utcnow() + timedelta(hours=2)
    else:  # update or delete
        expires = datetime.utcnow() + timedelta(hours=1)

    original_json = json.dumps(original_data) if original_data else None

    db.execute(
        """INSERT INTO user_modifications
           (user_id, api_key_id, table_name, record_id, action, original_data, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, api_key_id, table_name, record_id, action, original_json, expires.strftime('%Y-%m-%d %H:%M:%S'))
    )
    db.commit()
    db.close()


def get_record_snapshot(table_name, record_id):
    """Get a snapshot of a record's current data for later restoration."""
    db = get_db()
    row = db.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,)).fetchone()
    db.close()
    if not row:
        return None
    data = dict(row)
    # Remove internal columns
    for key in ['id', 'is_frozen', 'created_by_user', 'created_by_key', 'created_at', 'updated_at']:
        data.pop(key, None)
    return data


def freeze_cleanup():
    """
    Background cleanup task — runs every 60 seconds.
    Reverts expired user modifications:
    - Deletes user-created records (POST) after 2h
    - Reverts user-modified records (PUT) after 1h
    - Restores user-deleted records (DELETE) after 1h
    """
    while True:
        try:
            db = get_db()
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            # Get all expired modifications
            expired = db.execute(
                "SELECT * FROM user_modifications WHERE expires_at <= ?",
                (now,)
            ).fetchall()

            for mod in expired:
                table = mod['table_name']
                record_id = mod['record_id']
                action = mod['action']

                if action == 'create':
                    # Delete user-created record
                    db.execute(f"DELETE FROM {table} WHERE id = ? AND is_frozen = 0", (record_id,))

                elif action == 'update':
                    # Revert to original data
                    if mod['original_data']:
                        original = json.loads(mod['original_data'])
                        cols = TABLE_COLUMNS.get(table, [])
                        set_parts = []
                        values = []
                        for col in cols:
                            if col in original:
                                set_parts.append(f"{col} = ?")
                                values.append(original[col])
                        if set_parts:
                            values.append(record_id)
                            db.execute(
                                f"UPDATE {table} SET {', '.join(set_parts)} WHERE id = ?",
                                values
                            )

                elif action == 'delete':
                    # Restore deleted frozen record
                    if mod['original_data']:
                        original = json.loads(mod['original_data'])
                        cols = TABLE_COLUMNS.get(table, [])
                        available_cols = [c for c in cols if c in original]
                        placeholders = ', '.join(['?'] * (len(available_cols) + 2))
                        col_names = ', '.join(available_cols + ['id', 'is_frozen'])
                        values = [original[c] for c in available_cols] + [record_id, 1]
                        # Only restore if not already existing
                        exists = db.execute(f"SELECT id FROM {table} WHERE id = ?", (record_id,)).fetchone()
                        if not exists:
                            db.execute(
                                f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                                values
                            )

                # Remove the processed modification
                db.execute("DELETE FROM user_modifications WHERE id = ?", (mod['id'],))

            db.commit()
            db.close()
        except Exception as e:
            print(f"[Deep Freeze] Cleanup error: {e}")

        time.sleep(60)  # Run every 60 seconds


def start_freeze_daemon():
    """Start the deep freeze cleanup as a background daemon thread."""
    thread = threading.Thread(target=freeze_cleanup, daemon=True, name='deep-freeze-daemon')
    thread.start()
    print("[Deep Freeze] 🧊 Cleanup daemon started (checks every 60s)")
    return thread


def get_freeze_info():
    """Get stats about pending modifications."""
    db = get_db()
    stats = {
        'pending_creates': db.execute("SELECT COUNT(*) FROM user_modifications WHERE action='create'").fetchone()[0],
        'pending_updates': db.execute("SELECT COUNT(*) FROM user_modifications WHERE action='update'").fetchone()[0],
        'pending_deletes': db.execute("SELECT COUNT(*) FROM user_modifications WHERE action='delete'").fetchone()[0],
    }
    db.close()
    stats['total_pending'] = sum(stats.values())
    return stats
