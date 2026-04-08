# setup_db.py
import sqlite3
import os

# Create database directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Connect to SQLite database
conn = sqlite3.connect('tenants.db')
cursor = conn.cursor()

# Create tenants table
cursor.execute('''
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    tier TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active',
    max_users INTEGER DEFAULT 10,
    max_transactions INTEGER DEFAULT 1000,
    trial_ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    role TEXT DEFAULT 'member',
    status TEXT DEFAULT 'active',
    mfa_enabled INTEGER DEFAULT 0,
    mfa_secret TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
)
''')

# Create invitations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS invitations (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
)
''')

conn.commit()
conn.close()

print("✅ Database tables created successfully")
print("   - tenants table")
print("   - users table")
print("   - invitations table")
