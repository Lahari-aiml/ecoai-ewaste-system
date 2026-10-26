-- EcoAI Database Schema
-- SQLite3 with Foreign Key constraints enabled

PRAGMA foreign_keys = ON;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- 'user' or 'admin'
    is_active INTEGER NOT NULL DEFAULT 1, -- 1 for active, 0 for deactivated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE, -- 'Repair', 'Reuse', 'Recycle'
    description TEXT NOT NULL,
    badge_color TEXT NOT NULL DEFAULT 'success',
    icon TEXT NOT NULL DEFAULT 'bi-cpu'
);

-- 3. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL UNIQUE,
    recommendation_text TEXT NOT NULL,
    instructions TEXT NOT NULL,
    safety_guidelines TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
);

-- 4. E-Waste Reference Records Table
CREATE TABLE IF NOT EXISTS ewaste_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
);

-- 5. User Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    input_text TEXT NOT NULL,
    predicted_category_id INTEGER NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    model_used TEXT DEFAULT 'NLP + Deep Learning Ensemble',
    nlp_prediction TEXT,
    dl_prediction TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (predicted_category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

-- 6. Service Providers Table
CREATE TABLE IF NOT EXISTS service_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    offers_pickup INTEGER NOT NULL DEFAULT 1, -- 1 = yes, 0 = no
    is_active INTEGER NOT NULL DEFAULT 1, -- 1 = active, 0 = inactive
    verification_status TEXT NOT NULL DEFAULT 'Demo / Sample', -- 'Verified' or 'Demo / Sample'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

-- 7. Pickup Requests Table
CREATE TABLE IF NOT EXISTS pickup_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    prediction_id INTEGER,
    provider_id INTEGER NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    preferred_date TEXT NOT NULL,
    instructions TEXT,
    status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Confirmed', 'Picked Up', 'Completed', 'Cancelled', 'Rejected'
    status_notes TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES predictions (id) ON DELETE SET NULL,
    FOREIGN KEY (provider_id) REFERENCES service_providers (id) ON DELETE CASCADE
);

-- Indexes for high-performance querying and integrity
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions (user_id);
CREATE INDEX IF NOT EXISTS idx_pickup_user ON pickup_requests (user_id);
CREATE INDEX IF NOT EXISTS idx_pickup_provider ON pickup_requests (provider_id);
CREATE INDEX IF NOT EXISTS idx_providers_category ON service_providers (category_id);
CREATE INDEX IF NOT EXISTS idx_providers_city ON service_providers (city);
