import sqlite3
from datetime import datetime


class TodoDatabase:
    def __init__(self, db_name="todo.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # Initialize tables safely
        self.create_table()
        self._migrate_notes_column()
        self._init_stats_table()

    def create_table(self):
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    task_name TEXT NOT NULL,
                    due_date TEXT,
                    category TEXT DEFAULT 'Work', 
                    created_at TEXT,
                    completed_at TEXT,
                    time_spent INTEGER DEFAULT 0,
                    current_session_start TEXT,
                    session_goal_seconds INTEGER,
                    status TEXT DEFAULT 'NEW',
                    notes TEXT DEFAULT '',
                    FOREIGN KEY(parent_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds INTEGER,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (create_table): {e}")
            self.conn.rollback()

    def _migrate_notes_column(self):
        try:
            self.cursor.execute("PRAGMA table_info(tasks)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if "notes" not in columns:
                self.cursor.execute("ALTER TABLE tasks ADD COLUMN notes TEXT DEFAULT ''")
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (migrate_notes): {e}")
            self.conn.rollback()

    # --- NEW: STATS TABLE ---
    def _init_stats_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    key TEXT PRIMARY KEY,
                    value INTEGER
                )
            """)
            # Initialize distance if not exists
            self.cursor.execute("INSERT OR IGNORE INTO user_stats (key, value) VALUES ('total_distance', 0)")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (init_stats): {e}")
            self.conn.rollback()

    def get_total_distance(self):
        try:
            self.cursor.execute("SELECT value FROM user_stats WHERE key = 'total_distance'")
            row = self.cursor.fetchone()
            return row['value'] if row else 0
        except sqlite3.Error as e:
            print(f"DB Error (get_distance): {e}")
            return 0

    def add_distance(self, km_to_add):
        try:
            self.cursor.execute("UPDATE user_stats SET value = value + ? WHERE key = 'total_distance'", (km_to_add,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (add_distance): {e}")
            self.conn.rollback()

    # --- EXISTING METHODS ---
    def add_task(self, task_name, due_date=None, category="Work", parent_id=None):
        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                """INSERT INTO tasks 
                   (parent_id, task_name, due_date, category, created_at, status, time_spent, session_goal_seconds, notes) 
                   VALUES (?, ?, ?, ?, ?, 'NEW', 0, NULL, '')""",
                (parent_id, task_name, due_date, category, created_at)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"DB Error (add_task): {e}")
            self.conn.rollback()
            return None

    def update_task_notes(self, task_id, notes_text):
        try:
            self.cursor.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes_text, task_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (update_notes): {e}")
            self.conn.rollback()

    def get_tasks(self, parent_id=None):
        try:
            query = "SELECT * FROM tasks WHERE parent_id IS ?"
            self.cursor.execute(query, (parent_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"DB Error (get_tasks): {e}")
            return []

    def get_task_by_id(self, task_id):
        try:
            self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"DB Error (get_task_by_id): {e}")
            return None

    def get_task_hierarchy(self, task_id):
        # Recursive, read-only: less risk of locking, but good to handle errors
        try:
            parent = self.get_task_by_id(task_id)
            if not parent: return []
            results = [dict(parent)]
            children = self.get_tasks(parent_id=task_id)
            for child in children:
                results.extend(self.get_task_hierarchy(child['id']))
            return results
        except Exception as e:
            print(f"Error getting hierarchy: {e}")
            return []

    def get_all_archived_tasks(self, min_date=None):
        try:
            query = """
                SELECT t.*, p.task_name as parent_name 
                FROM tasks t
                LEFT JOIN tasks p ON t.parent_id = p.id
                WHERE t.status = 'ARCHIVED'
            """
            params = []
            if min_date:
                query += " AND t.completed_at >= ?"
                params.append(min_date)
            query += " ORDER BY t.completed_at DESC"
            self.cursor.execute(query, tuple(params))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"DB Error (get_archived): {e}")
            return []

    def update_task_fields(self, task_id, new_name, new_eta):
        try:
            self.cursor.execute(
                "UPDATE tasks SET task_name = ?, due_date = ? WHERE id = ?",
                (new_name, new_eta, task_id)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (update_fields): {e}")
            self.conn.rollback()

    def delete_task(self, task_id):
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (delete_task): {e}")
            self.conn.rollback()

    def start_timer(self, task_id, goal_seconds=None):
        try:
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "UPDATE tasks SET current_session_start = ?, session_goal_seconds = ?, status = 'IN_PROGRESS' WHERE id = ?",
                (start_time, goal_seconds, task_id)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (start_timer): {e}")
            self.conn.rollback()

    def stop_timer(self, task_id):
        # Returns elapsed seconds so Main App can calculate Distance
        try:
            self.cursor.execute("SELECT current_session_start, parent_id FROM tasks WHERE id = ?", (task_id,))
            row = self.cursor.fetchone()
            elapsed = 0

            if row and row['current_session_start']:
                start_str = row['current_session_start']
                end_dt = datetime.now()
                end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                elapsed = int((end_dt - start_dt).total_seconds())

                self.cursor.execute(
                    """UPDATE tasks SET 
                       time_spent = time_spent + ?, 
                       current_session_start = NULL, 
                       session_goal_seconds = NULL 
                       WHERE id = ?""",
                    (elapsed, task_id))

                self.cursor.execute(
                    """INSERT INTO sessions (task_id, start_time, end_time, duration_seconds)
                       VALUES (?, ?, ?, ?)""",
                    (task_id, start_str, end_str, elapsed)
                )

                if row['parent_id']:
                    self._propagate_time_upwards(row['parent_id'], elapsed)

                self.conn.commit()

            return elapsed
        except sqlite3.Error as e:
            print(f"DB Error (stop_timer): {e}")
            self.conn.rollback()
            return 0

    def _propagate_time_upwards(self, parent_id, seconds_to_add):
        # Helper method used inside a transaction, so we don't commit here individually
        # Exceptions will be caught by the caller (stop_timer)
        curr_id = parent_id
        while curr_id is not None:
            self.cursor.execute("UPDATE tasks SET time_spent = time_spent + ? WHERE id = ?", (seconds_to_add, curr_id))
            self.cursor.execute("SELECT parent_id FROM tasks WHERE id = ?", (curr_id,))
            res = self.cursor.fetchone()
            curr_id = res['parent_id'] if res else None

    def mark_completed(self, task_id):
        try:
            self.stop_timer(task_id)
            completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("UPDATE tasks SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
                                (completed_at, task_id))
            self._mark_children_status(task_id, 'COMPLETED', completed_at)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (mark_completed): {e}")
            self.conn.rollback()

    def archive_task(self, task_id):
        try:
            self.stop_timer(task_id)
            self.cursor.execute("UPDATE tasks SET status = 'ARCHIVED' WHERE id = ?", (task_id,))
            self._mark_children_status(task_id, 'ARCHIVED', None)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (archive_task): {e}")
            self.conn.rollback()

    def archive_all_completed(self):
        try:
            self.cursor.execute("UPDATE tasks SET status = 'ARCHIVED' WHERE status = 'COMPLETED'")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (archive_all): {e}")
            self.conn.rollback()

    def _mark_children_status(self, parent_id, status, completed_at):
        # Helper used inside transactions
        self.cursor.execute("SELECT id FROM tasks WHERE parent_id = ?", (parent_id,))
        children = self.cursor.fetchall()
        for child in children:
            self.cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                                (status, completed_at, child['id']))
            self._mark_children_status(child['id'], status, completed_at)

    def reopen_task(self, task_id):
        try:
            self.cursor.execute("UPDATE tasks SET status = 'NEW', completed_at = NULL WHERE id = ?", (task_id,))
            curr_id = task_id
            while curr_id:
                self.cursor.execute("SELECT parent_id FROM tasks WHERE id = ?", (curr_id,))
                res = self.cursor.fetchone()
                if res and res['parent_id']:
                    self.cursor.execute(
                        "UPDATE tasks SET status = 'NEW', completed_at = NULL WHERE id = ? AND status IN ('COMPLETED', 'ARCHIVED')",
                        (res['parent_id'],))
                    curr_id = res['parent_id']
                else:
                    curr_id = None
            self._mark_children_status(task_id, 'NEW', None)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error (reopen_task): {e}")
            self.conn.rollback()

    def get_tasks_for_report(self, start_date_str, end_date_str):
        try:
            query = """
                SELECT DISTINCT 
                    t.*, 
                    p.task_name as parent_name 
                FROM tasks t
                LEFT JOIN sessions s ON t.id = s.task_id
                LEFT JOIN tasks p ON t.parent_id = p.id
                WHERE 
                    (
                        (t.completed_at BETWEEN ? AND ?) OR
                        (s.start_time BETWEEN ? AND ?) OR
                        (t.created_at BETWEEN ? AND ?)
                    )
                    AND t.category != 'Personal'
            """
            params = (start_date_str, end_date_str, start_date_str, end_date_str, start_date_str, end_date_str)
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"DB Error (get_report): {e}")
            return []

    def close(self):
        try:
            self.conn.close()
        except sqlite3.Error as e:
            print(f"DB Error (close): {e}")