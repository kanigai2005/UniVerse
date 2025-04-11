-- schema.sql

-- Drop tables if they exist (for development/testing)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS career_fairs;
DROP TABLE IF EXISTS internships;
DROP TABLE IF EXISTS hackathons;
DROP TABLE IF EXISTS questions; -- Added drop for questions
DROP TABLE IF EXISTS likes;     -- Added drop for likes

-- Create users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    activity_score INTEGER,
    achievements TEXT,
    alumni_gems INTEGER
);

CREATE TABLE career_fairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

CREATE TABLE internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT
);

CREATE TABLE hackathons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Optional: Create a likes table to handle many-to-many relationship
-- and prevent duplicate likes by the same user
CREATE TABLE IF NOT EXISTS likes (
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, question_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
);


-- Insert initial data into users
INSERT INTO users (name, email, activity_score, achievements, alumni_gems) VALUES
('Alex Johnson', 'alex@example.com', 50, 'Mentorship Pro, Top Contributor', 10),
('Sarah Lee', 'sarah@example.com', 42, 'Job Connector', 8),
('Michael Carter', 'michael@example.com', 38, 'Mentor Pro', 5),
('Emily White', 'emily@example.org', 60, 'Event Organizer, Speaker', 12);

-- Insert initial data into career_fairs
INSERT INTO career_fairs (name, date, location, description) VALUES
('Past Tech Fair', '2024-12-15', 'San Francisco', 'Meet top tech companies.'),
('Upcoming Engineering Jobs', '2025-05-10', 'New York', 'Find engineering jobs.'),
('Current Business Expo', '2025-04-04', 'Chicago', 'Explore business opportunities.');

-- Insert initial data into internships
INSERT INTO internships (title, company, start_date, end_date, description) VALUES
('Past Software Intern', 'Google', '2026-12-01', '2025-03-01', 'Work on cool projects.'),
('Future Data Science Intern', 'Amazon', '2025-06-15', '2025-09-15', 'Analyze large datasets.'),
('Current Marketing Intern', 'Microsoft', '2026-04-01', '2025-08-01', 'Assist with marketing campaigns.');

-- Insert initial data into hackathons
INSERT INTO hackathons (name, date, location, description) VALUES
('AI Hackathon', '2025-04-10', 'Online', 'Develop innovative AI solutions.'),
('Web Dev Challenge', '2025-05-20', 'San Francisco', 'Showcase your web development skills.'),
('Mobile App Competition', '2025-06-05', 'New York', 'Build the next great mobile app.');

INSERT OR IGNORE INTO questions (user_id, question_text) VALUES
(1, 'What are some good resources for learning Python?'),
(2, 'How can I improve my resume for software engineering roles?'),
(3, 'What are the key skills employers look for in marketing interns?'),
(1, 'Could someone explain the basics of machine learning?'),
(3, 'What are some common interview questions for data science positions?');

-- Add some initial likes
INSERT OR IGNORE INTO questions (id, likes) VALUES
(1, 5),
(2, 12),
(3, 3),
(4, 8),
(5, 1);

-- Add some initial likes (using the likes table - optional)
INSERT OR IGNORE INTO likes (user_id, question_id) VALUES
(2, 1),
(3, 1),
(4, 1),
(5, 1),
(1, 2),
(3, 2),
(4, 2),
(5, 2),
(1, 3),
(2, 3),
(1, 4),
(2, 4),
(3, 4),
(1, 5);