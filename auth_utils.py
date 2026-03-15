import os
import json
import hashlib
from typing import Dict

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _load_users() -> Dict[str, str]:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: Dict[str, str]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str) -> bool:
    """Create a new user. Returns True on success, False if user exists."""
    users = _load_users()
    if username in users:
        return False
    users[username] = _hash_password(password)
    _save_users(users)
    return True


def verify_user(username: str, password: str) -> bool:
    users = _load_users()
    if username not in users:
        return False
    return users.get(username) == _hash_password(password)


def list_users():
    return list(_load_users().keys())
