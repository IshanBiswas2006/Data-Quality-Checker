import os
import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

AVATAR_COLORS = [
    "#111827",  # Charcoal / Black
    "#24282E",  # Dark Slate
    "#4B5563",  # Slate Gray
    "#858B94",  # Light Gray
]

def _resolve_db_path(db_path: Optional[str] = None) -> str:
    if db_path:
        return db_path
    if current_app:
        return current_app.config.get("USERS_DB_PATH", "instance/users.db")
    return "instance/users.db"

def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    resolved_path = _resolve_db_path(db_path)
    if resolved_path != ":memory:":
        parent_dir = Path(resolved_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(resolved_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    conn = get_db(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                avatar_color TEXT DEFAULT '#111827',
                avatar_icon TEXT DEFAULT 'user',
                bio TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_saved_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                analysis_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                total_rows INTEGER DEFAULT 0,
                total_columns INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_user ON user_saved_analyses(user_id);")
    conn.close()

def _user_to_dict(row: sqlite3.Row, include_hash: bool = False) -> Dict[str, Any]:
    d = dict(row)
    if not include_hash:
        d.pop("password_hash", None)
    return d

def create_user(
    email: str,
    name: str,
    password: str,
    avatar_color: Optional[str] = None,
    bio: str = "",
    db_path: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    email = (email or "").strip().lower()
    name = (name or "").strip()
    password = password or ""

    if not name or len(name) < 2:
        return None, "Full name must be at least 2 characters long."
    if len(name) > 100:
        return None, "Full name cannot exceed 100 characters."

    if not email or not EMAIL_REGEX.match(email):
        return None, "Please enter a valid email address."

    if len(password) < 8:
        return None, "Password must be at least 8 characters long."

    if not avatar_color or avatar_color not in AVATAR_COLORS:
        # Pick color deterministically based on name/email
        color_idx = sum(ord(c) for c in (email or name)) % len(AVATAR_COLORS)
        avatar_color = AVATAR_COLORS[color_idx]

    password_hash = generate_password_hash(password)

    conn = get_db(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, name, password_hash, avatar_color, bio)
                VALUES (?, ?, ?, ?, ?)
                """,
                (email, name, password_hash, avatar_color, bio.strip())
            )
            user_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _user_to_dict(row), None
    except sqlite3.IntegrityError:
        return None, "An account with this email address already exists."
    finally:
        conn.close()

def authenticate_user(
    email: str,
    password: str,
    db_path: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        return None, "Email and password are required."

    conn = get_db(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            return None, "Invalid email or password."

        if not check_password_hash(row["password_hash"], password):
            return None, "Invalid email or password."

        # Update last login timestamp
        with conn:
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))

        updated_row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        return _user_to_dict(updated_row), None
    finally:
        conn.close()

def get_user_by_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    conn = get_db(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row) if row else None
    finally:
        conn.close()

def get_user_by_email(email: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not email:
        return None
    conn = get_db(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return _user_to_dict(row) if row else None
    finally:
        conn.close()

def update_profile(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_color: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    conn = get_db(db_path)
    try:
        current = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not current:
            return False, "User not found."

        new_name = name.strip() if name is not None else current["name"]
        new_email = email.strip().lower() if email is not None else current["email"]
        new_bio = bio.strip() if bio is not None else current["bio"]
        new_color = avatar_color.strip() if avatar_color is not None else current["avatar_color"]

        if not new_name or len(new_name) < 2:
            return False, "Name must be at least 2 characters long."
        if len(new_name) > 100:
            return False, "Name cannot exceed 100 characters."

        if not new_email or not EMAIL_REGEX.match(new_email):
            return False, "Please enter a valid email address."

        if new_color and new_color not in AVATAR_COLORS:
            new_color = current["avatar_color"]

        # Check if email is already taken by another user
        if new_email != current["email"]:
            existing = conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, user_id)).fetchone()
            if existing:
                return False, "This email address is already in use by another account."

        with conn:
            conn.execute(
                """
                UPDATE users
                SET name = ?, email = ?, bio = ?, avatar_color = ?
                WHERE id = ?
                """,
                (new_name, new_email, new_bio, new_color, user_id)
            )
        return True, "Profile updated successfully."
    finally:
        conn.close()

def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    if not current_password or not new_password:
        return False, "Both current and new passwords are required."

    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long."

    conn = get_db(db_path)
    try:
        user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False, "User not found."

        if not check_password_hash(user["password_hash"], current_password):
            return False, "Current password is incorrect."

        new_hash = generate_password_hash(new_password)
        with conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))

        return True, "Password changed successfully."
    finally:
        conn.close()

def save_user_analysis(
    user_id: int,
    analysis_id: str,
    filename: str,
    total_rows: int = 0,
    total_columns: int = 0,
    db_path: Optional[str] = None
) -> bool:
    conn = get_db(db_path)
    try:
        with conn:
            # Check if this analysis is already saved for this user
            existing = conn.execute(
                "SELECT id FROM user_saved_analyses WHERE user_id = ? AND analysis_id = ?",
                (user_id, analysis_id)
            ).fetchone()
            if not existing:
                conn.execute(
                    """
                    INSERT INTO user_saved_analyses (user_id, analysis_id, filename, total_rows, total_columns)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, analysis_id, filename, total_rows, total_columns)
                )
        return True
    finally:
        conn.close()

def get_user_analyses(user_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM user_saved_analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def delete_saved_analysis(user_id: int, analysis_id: str, db_path: Optional[str] = None) -> bool:
    conn = get_db(db_path)
    try:
        with conn:
            conn.execute(
                "DELETE FROM user_saved_analyses WHERE user_id = ? AND analysis_id = ?",
                (user_id, analysis_id)
            )
        return True
    finally:
        conn.close()
