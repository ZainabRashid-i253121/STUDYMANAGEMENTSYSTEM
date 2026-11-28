import sqlite3

def test_init_db_creates_required_tables(test_db):
    with test_db.connection_scope() as db:
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "tasks", "study_sessions", "reminders", "reminder_preferences",
            "reminder_notices", "availability", "staged_imports", "sync_logs",
            "events", "processed_events"}.issubset(names)

def test_foreign_keys_enabled(test_db):
    with test_db.connection_scope() as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1

def test_user_owned_tables_reject_unknown_user(test_db):
    with test_db.connection_scope() as db:
        try:
            db.execute("INSERT INTO tasks (user_id, title, deadline) VALUES (999, 'Task', '2026-11-25')")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Foreign key constraint was not enforced")

def test_init_db_is_idempotent(test_db):
    assert test_db.init_db() is True
    assert test_db.init_db() is True


def test_init_db_migrates_existing_tasks_table(tmp_path, monkeypatch):
    import sqlite3
    from Data_Access import database
    legacy_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(legacy_path)
    connection.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            course TEXT,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE (id, user_id)
        );
    """)
    connection.close()
    monkeypatch.setattr(database, "DATABASE_PATH", legacy_path)
    assert database.init_db() is True
    with database.connection_scope() as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(tasks)")}
        indexes = {row[1] for row in db.execute("PRAGMA index_list(tasks)")}
    assert "source_import_id" in columns
    assert "study_duration_minutes" in columns
    assert "idx_tasks_import_once" in indexes


def _build_legacy_db(path):
    """A database as created by the pre-gap-fix S01-S03 code (NOT NULL deadline, old statuses)."""
    connection = sqlite3.connect(path)
    connection.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK (role = 'Registered User'),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200), course TEXT,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed')),
            completed_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source_import_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, UNIQUE (id, user_id));
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, task_id INTEGER,
            remind_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', message TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id, user_id) REFERENCES tasks(id, user_id));
        INSERT INTO users (email, password_hash, role) VALUES ('a@example.com', 'h', 'Registered User');
        INSERT INTO tasks (user_id, title, deadline, status, completed_at) VALUES
            (1, 'Pending one', '2026-12-01', 'pending', NULL),
            (1, 'Started one', '2026-12-02', 'in_progress', NULL),
            (1, 'Done one', '2026-12-03', 'completed', '2026-11-20T10:00:00+00:00');
        INSERT INTO reminders (user_id, task_id, remind_at) VALUES (1, 2, '2026-12-01T09:00:00');
    """)
    connection.commit()
    connection.close()


def test_init_db_rebuilds_legacy_tasks_table_and_keeps_data(tmp_path, monkeypatch):
    from Data_Access import database
    legacy_path = tmp_path / "legacy2.db"
    _build_legacy_db(legacy_path)
    monkeypatch.setattr(database, "DATABASE_PATH", legacy_path)
    assert database.init_db() is True
    with database.connection_scope() as db:
        rows = db.execute("SELECT id, title, deadline, status, completed_at FROM tasks ORDER BY id").fetchall()
        deadline_info = [r for r in db.execute("PRAGMA table_info(tasks)") if r[1] == "deadline"][0]
        task_columns = {row[1] for row in db.execute("PRAGMA table_info(tasks)")}
        reminder = db.execute("SELECT task_id FROM reminders").fetchone()
        fk_problems = db.execute("PRAGMA foreign_key_check").fetchall()
        indexes = {row[1] for row in db.execute("PRAGMA index_list(tasks)")}
        # the new schema accepts a missing deadline and rejects the removed statuses
        db.execute("INSERT INTO tasks (user_id, title) VALUES (1, 'No deadline')")
        with __import__("pytest").raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO tasks (user_id, title, status) VALUES (1, 'x', 'in_progress')")
    assert [(r["id"], r["status"]) for r in rows] == [(1, "incomplete"), (2, "incomplete"), (3, "completed")]
    assert rows[2]["completed_at"] == "2026-11-20T10:00:00+00:00"
    assert [r["deadline"] for r in rows] == ["2026-12-01", "2026-12-02", "2026-12-03"]
    assert deadline_info[3] == 0          # deadline is now nullable
    assert "study_duration_minutes" in task_columns
    assert reminder["task_id"] == 2       # dependent reminder still points at its task
    assert fk_problems == []
    assert "idx_tasks_import_once" in indexes


def test_init_db_migration_is_idempotent(tmp_path, monkeypatch):
    from Data_Access import database
    legacy_path = tmp_path / "legacy3.db"
    _build_legacy_db(legacy_path)
    monkeypatch.setattr(database, "DATABASE_PATH", legacy_path)
    database.init_db()
    database.init_db()
    with database.connection_scope() as db:
        assert db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 3
