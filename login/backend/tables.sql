-- Table: users

 drop table if exists users;
drop table if exists otps;



CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Index for username (for faster lookups)
CREATE INDEX idx_users_username ON users (username);

-- Index for email (for faster lookups)
CREATE INDEX idx_users_email ON users (email);

-- Table: otps
CREATE TABLE otps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
);

-- Index for email (for faster lookups and deleting expired OTPs)
CREATE INDEX idx_otps_email ON otps (email);

-- Index for expires_at (for faster deletion of expired OTPs)
CREATE INDEX idx_otps_expires_at ON otps (expires_at);