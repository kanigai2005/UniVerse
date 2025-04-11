-- schema.sql

-- Drop existing tables if they exist (for development/reset purposes)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS career_fairs;
DROP TABLE IF EXISTS internships;
DROP TABLE IF EXISTS hackathons;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS chat_contacts;
DROP TABLE IF EXISTS chat_messages;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    activity_score INTEGER,
    achievements TEXT,
    alumni_gems INTEGER,
    department TEXT,
    profession TEXT,
    alma_mater TEXT,
    interviews TEXT,
    internships TEXT,
    startups TEXT,
    current_company TEXT,
    milestones TEXT,
    advice TEXT,
    likes INTEGER DEFAULT 0
);

-- Create career_fairs table
CREATE TABLE career_fairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

-- Create internships table
CREATE TABLE internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT
);

-- Create hackathons table
CREATE TABLE hackathons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create chat_contacts table
CREATE TABLE IF NOT EXISTS chat_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    sender TEXT NOT NULL,
    text TEXT,
    file_path TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES chat_contacts(id)
);


-- Insert sample data into users table
INSERT INTO users (name, email, activity_score, achievements, alumni_gems, department, profession, alma_mater, interviews, internships, startups, current_company, milestones, advice, likes) VALUES
('John Doe', 'john.doe@example.com', 150, 'Published paper, Patent holder', 50, 'Computer Science', 'Software Engineer', 'MIT', 'Google Interview', 'Google Intern', 'Tech Startup', 'Google', 'Promoted to Senior Engineer', 'Keep learning!', 10),
('Jane Smith', 'jane.smith@example.com', 120, 'Award winner', 30, 'Electrical Engineering', 'Hardware Engineer', 'Stanford', 'Apple Interview', 'Apple Intern', 'Hardware Startup', 'Apple', 'Led a major project', 'Network well!', 8),
('Alice Johnson', 'alice.johnson@example.com', 180, 'Published book', 70, 'Mechanical Engineering', 'Aerospace Engineer', 'Caltech', 'SpaceX Interview', 'SpaceX Intern', 'Aerospace Startup', 'SpaceX', 'Designed a rocket component', 'Be persistent!', 12);

-- Insert sample data into career_fairs table
INSERT INTO career_fairs (name, date, location, description) VALUES
('Tech Career Fair', '2026-03-15', 'San Francisco', 'Meet top tech companies.'),
('Engineering Expo', '2026-04-20', 'New York', 'Opportunities for engineers.');

-- Insert sample data into internships table
INSERT INTO internships (title, company, start_date, end_date, description) VALUES
('Software Development Intern', 'Google', '2026-06-01', '2024-08-31', 'Work on cutting-edge projects.'),
('Hardware Engineering Intern', 'Apple', '2026-06-15', '2024-09-15', 'Design and test hardware components.');

-- Insert sample data into hackathons table
INSERT INTO hackathons (name, date, location, description) VALUES
('AI Hackathon', '2026-03-20', 'Online', 'Build AI-powered solutions.'),
('Web Development Hackathon', '2025-04-25', 'London', 'Create innovative web applications.');

-- Insert sample data into questions table
INSERT INTO questions (user_id, question_text, likes) VALUES
(1, 'What is the best way to prepare for a Google interview?', 5),
(2, 'How can I network effectively at a career fair?', 3),
(3, 'What are some tips for landing an internship at SpaceX?', 7);

-- Insert sample data into chat_contacts table
INSERT INTO chat_contacts (name) VALUES
('Alice Johnson'),
('Bob Williams');

-- Insert sample data into chat_messages table
INSERT INTO chat_messages (contact_id, sender, text) VALUES
(1, 'me', 'Hi Alice, how are you?'),
(1, 'Alice', 'Im doing well, thanks!'),
(2, 'me', 'Hey Bob, whats up?'),
(2, 'Bob', 'Not much, just working on a project.');