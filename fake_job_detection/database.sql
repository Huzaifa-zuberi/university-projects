-- ============================================================
-- Fake Job Detection in Pakistan
-- Database Schema  (PostgreSQL / Supabase)
-- ------------------------------------------------------------
-- HOW TO USE:
-- 1. Open your Supabase project.
-- 2. Go to the "SQL Editor".
-- 3. Paste this whole file and click "Run".
-- This creates two tables: users and predictions.
-- ============================================================


-- ------------------------------------------------------------
-- TABLE 1: users
-- People who can log in and check jobs.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,                 -- unique id for each user
    full_name     VARCHAR(100) NOT NULL,              -- user's full name
    email         VARCHAR(120) UNIQUE NOT NULL,       -- email used to log in (unique)
    password      VARCHAR(255) NOT NULL,              -- hashed password (never plain text)
    created_at    TIMESTAMP DEFAULT NOW()             -- when the account was created
);


-- ------------------------------------------------------------
-- TABLE 2: predictions
-- Every job check made, linked to the user who made it.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id                       SERIAL PRIMARY KEY,       -- unique id for each check
    user_id                  INTEGER NOT NULL,         -- which user made it (FOREIGN KEY)

    -- ---- Job posting data entered by the user ----
    job_title                VARCHAR(200) NOT NULL,
    company_name             VARCHAR(200),
    salary                   VARCHAR(100),
    location                 VARCHAR(150),
    employment_type          VARCHAR(50),
    experience               VARCHAR(100),
    education                VARCHAR(100),
    description              TEXT NOT NULL,

    -- ---- Prediction result data ----
    predicted_result         VARCHAR(10)  NOT NULL CHECK (predicted_result IN ('Real', 'Fake')),
    fake_probability         NUMERIC(5,2) NOT NULL CHECK (fake_probability BETWEEN 0 AND 100),
    confidence_percentage    NUMERIC(5,2) NOT NULL CHECK (confidence_percentage BETWEEN 0 AND 100),
    risk_level               VARCHAR(10)  NOT NULL CHECK (risk_level IN ('Low', 'Medium', 'High')),
    warning_signs            TEXT,                     -- detected warnings (comma separated)

    created_at               TIMESTAMP DEFAULT NOW(),  -- when this check was saved

    -- ---- Relationship ----
    -- Link each prediction to a user. If a user is deleted,
    -- their predictions are deleted too (ON DELETE CASCADE).
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- Helpful index so loading a user's history is fast.
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions (user_id);
