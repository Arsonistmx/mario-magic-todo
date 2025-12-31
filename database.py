import sqlite3
from datetime import datetime, timedelta


class TodoDatabase:
    def __init__(self, db_name="todo.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()
        self._migrate_notes_column()

    def create_table(self):
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

    def _migrate_notes_column(self):
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if "notes" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN notes TEXT DEFAULT ''")
            self.conn.commit()

    def add_task(self, task_name, due_date=None, category="Work", parent_id=None):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """INSERT INTO tasks 
               (parent_id, task_name, due_date, category, created_at, status, time_spent, session_goal_seconds, notes) 
               VALUES (?, ?, ?, ?, ?, 'NEW', 0, NULL, '')""",
            (parent_id, task_name, due_date, category, created_at)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_task_notes(self, task_id, notes_text):
        self.cursor.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes_text, task_id))
        self.conn.commit()

    def get_tasks(self, parent_id=None):
        query = "SELECT * FROM tasks WHERE parent_id IS ?"
        self.cursor.execute(query, (parent_id,))
        return self.cursor.fetchall()

    def get_task_by_id(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return self.cursor.fetchone()

    # --- NEW: Recursive Fetch for Single Task Report ---
    def get_task_hierarchy(self, task_id):
        """Fetches a task and all its children recursively."""
        parent = self.get_task_by_id(task_id)
        if not parent: return []

        results = [dict(parent)]
        children = self.get_tasks(parent_id=task_id)
        for child in children:
            results.extend(self.get_task_hierarchy(child['id']))
        return results

    def get_all_archived_tasks(self, min_date=None):
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

    def update_task_fields(self, task_id, new_name, new_eta):
        self.cursor.execute(
            "UPDATE tasks SET task_name = ?, due_date = ? WHERE id = ?",
            (new_name, new_eta, task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def start_timer(self, task_id, goal_seconds=None):
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "UPDATE tasks SET current_session_start = ?, session_goal_seconds = ?, status = 'IN_PROGRESS' WHERE id = ?",
            (start_time, goal_seconds, task_id)
        )
        self.conn.commit()

    def stop_timer(self, task_id):
        self.cursor.execute("SELECT current_session_start, parent_id FROM tasks WHERE id = ?", (task_id,))
        row = self.cursor.fetchone()

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

    def _propagate_time_upwards(self, parent_id, seconds_to_add):
        curr_id = parent_id
        while curr_id is not None:
            self.cursor.execute("UPDATE tasks SET time_spent = time_spent + ? WHERE id = ?", (seconds_to_add, curr_id))
            self.cursor.execute("SELECT parent_id FROM tasks WHERE id = ?", (curr_id,))
            res = self.cursor.fetchone()
            curr_id = res['parent_id'] if res else None

    def mark_completed(self, task_id):
        self.stop_timer(task_id)
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE tasks SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
                            (completed_at, task_id))
        self._mark_children_status(task_id, 'COMPLETED', completed_at)
        self.conn.commit()

    def archive_task(self, task_id):
        self.stop_timer(task_id)
        self.cursor.execute("UPDATE tasks SET status = 'ARCHIVED' WHERE id = ?", (task_id,))
        self._mark_children_status(task_id, 'ARCHIVED', None)
        self.conn.commit()

    def archive_all_completed(self):
        self.cursor.execute("UPDATE tasks SET status = 'ARCHIVED' WHERE status = 'COMPLETED'")
        self.conn.commit()

    def _mark_children_status(self, parent_id, status, completed_at):
        self.cursor.execute("SELECT id FROM tasks WHERE parent_id = ?", (parent_id,))
        children = self.cursor.fetchall()
        for child in children:
            self.cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                                (status, completed_at, child['id']))
            self._mark_children_status(child['id'], status, completed_at)

    def reopen_task(self, task_id):
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

    def get_tasks_for_report(self, start_date_str, end_date_str):
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

    def close(self):
        self.conn.close()