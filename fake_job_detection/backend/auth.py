# ============================================================
# auth.py
# Simple helper functions for Registration and Login.
# ------------------------------------------------------------
# We use werkzeug.security (comes with Flask) to hash passwords.
# ============================================================

from werkzeug.security import generate_password_hash, check_password_hash

import database


def register_user(full_name, email, password):
    """Create a new account.
    Returns (success, message).
    """
    # 1. Check if the email is already used.
    existing = database.get_user_by_email(email)
    if existing is not None:
        return False, "An account with this email already exists."

    # 2. Hash the password so we never store the real one.
    hashed = generate_password_hash(password)

    # 3. Save the user.
    database.create_user(full_name, email, hashed)
    return True, "Account created successfully. Please log in."


def login_user(email, password):
    """Check email + password.
    Returns (success, message, user).
    'user' is a dictionary if login worked, otherwise None.
    """
    user = database.get_user_by_email(email)

    if user is None:
        return False, "No account found with this email.", None

    if not check_password_hash(user["password"], password):
        return False, "Incorrect password.", None

    return True, "Login successful.", user
