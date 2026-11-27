import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from Data_Access import database

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test.db")
    database.init_db()
    return database

@pytest.fixture
def user_id(test_db):
    with test_db.connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("student@example.com", "test-hash", "Registered User"),
        )
        return cursor.lastrowid
