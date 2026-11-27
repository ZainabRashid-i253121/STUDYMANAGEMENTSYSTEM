"""Centralized SQLite connection and schema initialization."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "instance" / "study_management.db"

def get_connection():
    """Return a configured SQLite connection with foreign keys enabled."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

@contextmanager
def connection_scope():
    """Yield a connection, committing on success and always closing it."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def init_db():
    """Create all application tables; safe to call repeatedly."""
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role = 'Registered User'),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
        course TEXT,
        deadline TEXT,
        deadline_at TEXT,
        status TEXT NOT NULL DEFAULT 'incomplete'
            CHECK (status IN ('incomplete', 'completed')),
        completed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        source_import_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (id, user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
    CREATE TABLE IF NOT EXISTS task_priorities (
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        priority TEXT NOT NULL CHECK (priority IN ('High', 'Medium', 'Low', 'Undetermined')),
        days_until_deadline INTEGER,
        deadline TEXT,
        priority_requires_review INTEGER NOT NULL DEFAULT 0 CHECK (priority_requires_review IN (0, 1)),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (task_id, user_id),
        FOREIGN KEY (task_id, user_id) REFERENCES tasks(id, user_id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_task_priorities_user_id ON task_priorities(user_id);
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER,
        session_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'scheduled'
            CHECK (status IN ('scheduled', 'completed', 'cancelled')),
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id, user_id) REFERENCES tasks(id, user_id),
        CHECK (start_time < end_time)
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON study_sessions(user_id);
    CREATE TABLE IF NOT EXISTS reminder_preferences (
        user_id INTEGER PRIMARY KEY,
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
        deadline_enabled INTEGER NOT NULL DEFAULT 1 CHECK (deadline_enabled IN (0, 1)),
        session_enabled INTEGER NOT NULL DEFAULT 1 CHECK (session_enabled IN (0, 1)),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER,
        session_id INTEGER,
        event_type TEXT NOT NULL DEFAULT 'general'
            CHECK (event_type IN ('deadline', 'session', 'general')),
        remind_at TEXT NOT NULL,
        event_at TEXT,
        offset_seconds INTEGER,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending', 'delivering', 'delivered', 'dismissed', 'cancelled', 'skipped')),
        message TEXT,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        last_attempt_at TEXT,
        claim_token TEXT,
        claim_expires_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id, user_id) REFERENCES tasks(id, user_id),
        FOREIGN KEY (session_id) REFERENCES study_sessions(id),
        CHECK ((event_type = 'deadline' AND task_id IS NOT NULL AND session_id IS NULL) OR
               (event_type = 'session' AND session_id IS NOT NULL AND task_id IS NULL) OR
               (event_type = 'general' AND task_id IS NULL AND session_id IS NULL))
    );
    CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
    CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(user_id, status, remind_at);
    CREATE TABLE IF NOT EXISTS reminder_notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reminder_id INTEGER,
        notice_type TEXT NOT NULL,
        message TEXT NOT NULL,
        dismissed INTEGER NOT NULL DEFAULT 0 CHECK (dismissed IN (0, 1)),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE SET NULL
    );
    CREATE INDEX IF NOT EXISTS idx_reminder_notices_user ON reminder_notices(user_id, dismissed, id);
    CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CHECK (start_time < end_time)
    );
    CREATE INDEX IF NOT EXISTS idx_availability_user_id ON availability(user_id);
    CREATE TABLE IF NOT EXISTS staged_imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        course TEXT,
        deadline TEXT NOT NULL,
        deadline_at TEXT,
        status TEXT NOT NULL DEFAULT 'staged'
            CHECK (status IN ('staged', 'accepted', 'rejected')),
        accepted_task_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (accepted_task_id, user_id) REFERENCES tasks(id, user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_staged_imports_user_id ON staged_imports(user_id);
    -- PROVISIONAL pending G-01 / G-12: in-application event records (plan S01).
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        payload TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending', 'processed', 'failed')),
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        next_attempt_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        processed_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
    CREATE TABLE IF NOT EXISTS processed_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        consumer TEXT NOT NULL,
        processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
        UNIQUE (event_id, consumer)
    );
    CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        outcome TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    with connection_scope() as connection:
        connection.executescript(schema)
        # Small forward-compatible migration for databases created by S01-S03.
        task_columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)")}
        if "source_import_id" not in task_columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN source_import_id INTEGER")
        if "deadline_at" not in task_columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN deadline_at TEXT")
        staged_columns = {row[1] for row in connection.execute("PRAGMA table_info(staged_imports)")}
        if "deadline_at" not in staged_columns:
            connection.execute("ALTER TABLE staged_imports ADD COLUMN deadline_at TEXT")
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_import_once "
            "ON tasks(user_id, source_import_id) WHERE source_import_id IS NOT NULL"
        )
    _migrate_tasks_table_if_legacy()
    _migrate_reminders_table_if_legacy()
    return True


_TASKS_TABLE_SQL = """
    CREATE TABLE tasks_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
        course TEXT,
        deadline TEXT,
        deadline_at TEXT,
        status TEXT NOT NULL DEFAULT 'incomplete'
            CHECK (status IN ('incomplete', 'completed')),
        completed_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        source_import_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (id, user_id)
    )
"""


def _tasks_table_is_legacy(connection):
    """True when tasks still has a NOT NULL deadline or the old status values."""
    info = connection.execute("PRAGMA table_info(tasks)").fetchall()
    deadline_not_null = any(row[1] == "deadline" and row[3] == 1 for row in info)
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()
    old_status = bool(row and row[0] and "'pending'" in row[0])
    return deadline_not_null or old_status


def _migrate_tasks_table_if_legacy():
    """Rebuild ``tasks`` for databases created before the plan v0.2 gap-fix.

    SQLite cannot drop NOT NULL or change a CHECK in place, so the table is
    rebuilt (SQLite's documented 12-step procedure). Rows are preserved;
    ``pending`` and ``in_progress`` become ``incomplete``. Foreign keys that
    point at tasks(id, user_id) keep working because ids are copied unchanged.
    """
    connection = sqlite3.connect(DATABASE_PATH, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        if not _tasks_table_is_legacy(connection):
            return
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)")}
            import_col = "source_import_id" if "source_import_id" in columns else "NULL"
            connection.execute(_TASKS_TABLE_SQL)
            connection.execute(
                "INSERT INTO tasks_new (id, user_id, title, course, deadline, deadline_at, status, "
                "completed_at, created_at, source_import_id) "
                "SELECT id, user_id, title, course, deadline, "
                "NULL, "
                "CASE WHEN status = 'completed' THEN 'completed' ELSE 'incomplete' END, "
                f"completed_at, created_at, {import_col} FROM tasks"
            )
            connection.execute("DROP TABLE tasks")
            connection.execute("ALTER TABLE tasks_new RENAME TO tasks")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_import_once "
                "ON tasks(user_id, source_import_id) WHERE source_import_id IS NOT NULL"
            )
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise sqlite3.IntegrityError("Foreign key check failed after tasks migration.")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
    finally:
        connection.close()


def _migrate_reminders_table_if_legacy():
    """Extend the original S01 reminder table without discarding existing rows."""
    connection = sqlite3.connect(DATABASE_PATH, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        columns = {row[1] for row in connection.execute("PRAGMA table_info(reminders)")}
        if "event_type" in columns and "session_id" in columns and "claim_token" in columns:
            return
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        try:
            connection.execute("""
                CREATE TABLE reminders_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL, task_id INTEGER, session_id INTEGER,
                    event_type TEXT NOT NULL DEFAULT 'general'
                        CHECK (event_type IN ('deadline', 'session', 'general')),
                    remind_at TEXT NOT NULL, event_at TEXT, offset_seconds INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'delivering', 'delivered', 'dismissed', 'cancelled', 'skipped')),
                    message TEXT, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
                    last_attempt_at TEXT, claim_token TEXT, claim_expires_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id, user_id) REFERENCES tasks(id, user_id),
                    FOREIGN KEY (session_id) REFERENCES study_sessions(id),
                    CHECK ((event_type = 'deadline' AND task_id IS NOT NULL AND session_id IS NULL) OR
                           (event_type = 'session' AND session_id IS NOT NULL AND task_id IS NULL) OR
                           (event_type = 'general' AND task_id IS NULL AND session_id IS NULL))
                )
            """)
            old_columns = columns
            event_type_expr = (
                "CASE WHEN task_id IS NOT NULL THEN 'deadline' ELSE 'general' END"
                if "task_id" in old_columns else "'general'"
            )
            task_id_expr = "task_id" if "task_id" in old_columns else "NULL"
            remind_at_expr = "remind_at" if "remind_at" in old_columns else "CURRENT_TIMESTAMP"
            status_expr = (
                "CASE WHEN status IN ('pending','delivered','dismissed') THEN status ELSE 'pending' END"
                if "status" in old_columns else "'pending'"
            )
            message_expr = "message" if "message" in old_columns else "NULL"
            created_expr = "created_at" if "created_at" in old_columns else "CURRENT_TIMESTAMP"
            connection.execute(f"""
                INSERT INTO reminders_new
                    (id,user_id,task_id,event_type,remind_at,status,message,created_at)
                SELECT id,user_id,{task_id_expr},{event_type_expr},{remind_at_expr},
                       {status_expr},{message_expr},{created_expr}
                FROM reminders
            """)
            connection.execute("DROP TABLE reminders")
            connection.execute("ALTER TABLE reminders_new RENAME TO reminders")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(user_id,status,remind_at)")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise sqlite3.IntegrityError("Foreign key check failed after reminders migration.")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
    finally:
        connection.close()
