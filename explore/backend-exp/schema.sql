-- Drop existing tables if they exist (for development/reset purposes)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS career_fairs;
DROP TABLE IF EXISTS internships;
DROP TABLE IF EXISTS hackathons;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS chat_contacts;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS user_connections;
DROP TABLE IF EXISTS daily_spark_questions; -- Added daily_spark_questions table
DROP TABLE IF EXISTS daily_spark_answers; -- Added daily_spark_answers table

-- Create users table
-- Table: users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    activity_score INTEGER DEFAULT 0,
    achievements TEXT,
    alumni_gems INTEGER DEFAULT 0,
    department TEXT,
    profession TEXT,
    alma_mater TEXT,
    interviews TEXT,
    internships TEXT,
    startups TEXT,
    current_company TEXT,
    milestones TEXT,
    advice TEXT,
    likes INTEGER DEFAULT 0,
    badges INTEGER DEFAULT 0,  -- Added badges column
    solved INTEGER DEFAULT 0,  -- Added solved column
    links INTEGER DEFAULT 0    -- Added links column
);

-- Table: user_connections
CREATE TABLE user_connections (
    user_id INTEGER,
    connected_user_id INTEGER,
    PRIMARY KEY (user_id, connected_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (connected_user_id) REFERENCES users(id)
);

-- Table: career_fairs
CREATE TABLE career_fairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

-- Table: internships
CREATE TABLE internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT
);

-- Table: hackathons
CREATE TABLE hackathons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT
);

-- Table: questions
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Table: chat_contacts
CREATE TABLE chat_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

-- Table: chat_messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    sender TEXT,
    text TEXT,
    file_path TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES chat_contacts(id)
);

-- Table: daily_spark_questions (New table for Daily Spark questions)
CREATE TABLE daily_spark_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    role TEXT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: daily_spark_answers (New table for Daily Spark answers)
CREATE TABLE daily_spark_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    user TEXT,
    text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES daily_spark_questions(id)
);

-- Inserting values into the 'users' table
INSERT INTO users (name, email, activity_score, achievements, alumni_gems, department, profession, alma_mater, interviews, internships, startups, current_company, milestones, advice, likes, badges, solved, links)
VALUES
    ('Alice Johnson', 'alice.j@example.com', 180, 'Published book', 70, 'Literature', 'Author', 'Oxford', 'Yes', 'No', 'No', 'Self-employed', 'Published novel', 'Write daily', 15, 0, 0, 0),
    ('John Doe', 'john.doe@example.com', 150, 'Published paper, Patent holder', 50, 'Engineering', 'Engineer', 'MIT', 'Yes', 'Yes', 'Yes', 'TechCorp', 'Patent granted', 'Innovate', 20, 0, 0, 0),
    ('Jane Smith', 'jane.smith@example.com', 120, 'Award winner', 30, 'Arts', 'Artist', 'Royal College of Art', 'No', 'No', 'Yes', 'ArtStudio', 'Exhibition held', 'Be creative', 10, 0, 0, 0),
    ('David Lee', 'david.lee@example.com', 200, 'Multiple patents', 80, 'Computer Science', 'Software Architect', 'Stanford', 'Yes', 'Yes', 'Yes', 'Google', 'Led major project', 'Learn constantly', 25, 0, 0, 0),
    ('Emily White', 'emily.white@example.com', 160, 'Published research', 60, 'Biology', 'Researcher', 'Harvard', 'Yes', 'Yes', 'No', 'BioTech Inc.', 'Discovered new gene', 'Collaborate', 18, 0, 0, 0);

-- Inserting values into the 'user_connections' table
INSERT INTO user_connections (user_id, connected_user_id)
VALUES
    (1, 2),  -- Alice connected to John
    (1, 3),  -- Alice connected to Jane
    (2, 4),  -- John connected to David
    (3, 5),  -- Jane connected to Emily
    (4, 5),  -- David connected to Emily
    (2, 5),  -- John connected to Emily
    (3, 4);  -- Jane connected to David

-- Inserting values into the 'career_fairs' table
INSERT INTO career_fairs (name, date, location, description)
VALUES
    ('Tech Career Fair', '2024-11-15', 'San Francisco', 'For tech professionals'),
    ('Art Career Fair', '2024-12-05', 'London', 'For artists and designers'),
    ('Engineering Expo', '2025-01-20', 'New York', 'For engineers and scientists');

-- Inserting values into the 'internships' table
INSERT INTO internships (title, company, start_date, end_date, description)
VALUES
    ('Software Intern', 'Google', '2024-06-01', '2024-08-31', 'Software development internship'),
    ('Design Intern', 'ArtStudio', '2024-07-01', '2024-09-30', 'Graphic design internship'),
    ('Research Intern', 'BioTech Inc.', '2024-06-15', '2024-08-15', 'Biological research internship');

-- Inserting values into the 'hackathons' table
INSERT INTO hackathons (name, date, location, description)
VALUES
    ('AI Hackathon', '2025-03-20', 'Online', 'AI development challenge'),
    ('Web Development Hackathon', '2025-04-25', 'London', 'Web development competition');

-- Inserting values into the 'questions' table
INSERT INTO questions (user_id, question_text, created_at, likes)
VALUES
    (1, 'How to write a novel?', '2024-10-20 10:00:00', 5),
    (2, 'Best practices for software architecture?', '2024-10-21 12:00:00', 8),
    (3, 'Tips for art exhibitions?', '2024-10-22 14:00:00', 3),
    (4, 'How to get a patent?', '2024-10-23 16:00:00', 10),
    (5, 'How to discover new genes?', '2024-10-24 18:00:00', 7);

-- Inserting values into the 'chat_contacts' table
INSERT INTO chat_contacts (name)
VALUES
    ('Alice Johnson'),
    ('John Doe'),
    ('Jane Smith'),
    ('David Lee'),
    ('Emily White');

-- Inserting values into the 'chat_messages' table
INSERT INTO chat_messages (contact_id, sender, text, timestamp)
VALUES
    (1, 'me', 'Hello Alice!', '2024-10-25 09:00:00'),
    (2, 'me', 'Hi John, how are you?', '2024-10-25 10:00:00'),
    (3, 'me', 'Jane, any art tips?', '2024-10-25 11:00:00'),
    (4, 'me', 'David, about the project...', '2024-10-25 12:00:00'),
    (5, 'me', 'Emily, gene research update?', '2024-10-25 13:00:00');

-- Inserting sample data into daily_spark_questions
INSERT INTO daily_spark_questions (company, role, question) VALUES
('Example Corp', 'Software Intern', 'Describe a time you faced a technical challenge and how you overcame it.'),
('Google', 'Software Engineer', 'Explain the concept of garbage collection in Java.'),
('Amazon', 'Product Manager', 'How would you prioritize features for a new e-commerce platform?');

-- Inserting sample data into daily_spark_answers
INSERT INTO daily_spark_answers (question_id, user, text, votes) VALUES
(1, 'Student A', 'Here is my answer...', 5),
(1, 'Alumnus B', 'This is how I handled it...', 2),
(2, 'Student A', 'Garbage collection is...', 5),
(2, 'Alumnus B', 'In simple terms...', 2),
(3, 'Alumnus C', 'I would start by...', 8);
