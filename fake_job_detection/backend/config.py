# ============================================================
# config.py
# All settings in one simple place.
# ------------------------------------------------------------
# Values are loaded from environment variables.
# Never store real passwords, API keys, or secrets in GitHub.
# ============================================================

import os

# ---- Flask secret key ----
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "change-me-in-production"
)

# ---- Supabase PostgreSQL connection details ----
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# ---- Path to the trained machine learning model ----
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "model",
        "best_model.pkl"
    )
)