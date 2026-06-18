# ============================================================
# database.py
# Simple functions to talk to the PostgreSQL (Supabase) database.
# We use psycopg2, a beginner-friendly PostgreSQL library.
# ------------------------------------------------------------
# Install once:  pip install psycopg2-binary
# ============================================================

import psycopg2
import psycopg2.extras  # lets us read rows as dictionaries

import config


def get_connection():
    """Open and return a new connection to the database."""
    connection = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    return connection


# ------------------------------------------------------------
# USER FUNCTIONS
# ------------------------------------------------------------
def create_user(full_name, email, hashed_password):
    """Insert a new user. Returns the new user's id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (full_name, email, password)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (full_name, email, hashed_password),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def get_user_by_email(email):
    """Find one user by email. Returns a dictionary or None."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


# ------------------------------------------------------------
# PREDICTION FUNCTIONS
# ------------------------------------------------------------
def save_prediction(user_id, data, result):
    """Save one job check.
    'data'   = the job posting the user entered (a dictionary)
    'result' = the prediction output (a dictionary)
    """
    conn = get_connection()
    cur = conn.cursor()

    # Extract database elements and ensure scalar numeric values
    pred_res = result.get("predicted_result")
    
    fake_prob = result.get("fake_probability", 0.0)
    if hasattr(fake_prob, "item"):
        fake_prob = fake_prob.item()

    conf_pct = result.get("confidence_percentage", 0.0)
    if hasattr(conf_pct, "item"):
        conf_pct = conf_pct.item()

    risk_lvl = result.get("risk_level")
    
    warning_signs = result.get("warning_signs", [])
    if isinstance(warning_signs, list):
        warning_signs_str = ", ".join(warning_signs)
    else:
        warning_signs_str = str(warning_signs)

    cur.execute(
        """
        INSERT INTO predictions (
            user_id, job_title, company_name, salary, location,
            employment_type, experience, education, description,
            predicted_result, fake_probability, confidence_percentage,
            risk_level, warning_signs
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            data.get("job_title", ""),
            data.get("company_name", ""),
            data.get("salary", ""),
            data.get("location", ""),
            data.get("employment_type", ""),
            data.get("experience", ""),
            data.get("education", ""),
            data.get("description", ""),
            pred_res,
            fake_prob,
            conf_pct,
            risk_lvl,
            warning_signs_str,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_user_predictions(user_id):
    """Return all checks made by one user (newest first)."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT * FROM predictions
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
