-- Drop existing tables if they exist (for development/reset purposes)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS career_fairs;
DROP TABLE IF EXISTS internships;
DROP TABLE IF EXISTS hackathons;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS chat_contacts;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS user_connections;
DROP TABLE IF EXISTS daily_spark_questions;
DROP TABLE IF EXISTS daily_spark_answers;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS search_history;
DROP TABLE IF EXISTS features;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS applied_hackathons;
DROP TABLE IF EXISTS user_issues;


-- Create users table
CREATE TABLE IF NOT EXISTS users (
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
    badges INTEGER DEFAULT 0,
    solved INTEGER DEFAULT 0,
    links INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_name ON users (name);

CREATE TABLE IF NOT EXISTS user_connections (
    user_id INTEGER,
    connected_user_id INTEGER,
    PRIMARY KEY (user_id, connected_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (connected_user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_user_connections_user_id ON user_connections (user_id);
CREATE INDEX IF NOT EXISTS idx_user_connections_connected_user_id ON user_connections (connected_user_id);

CREATE TABLE IF NOT EXISTS career_fairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS hackathons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE,
    location TEXT,
    description TEXT,
    theme TEXT,
    prize_pool TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_questions_user_id ON questions (user_id);

CREATE TABLE IF NOT EXISTS chat_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    sender TEXT,
    text TEXT,
    file_path TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (contact_id) REFERENCES chat_contacts(id)
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_contact_id ON chat_messages (contact_id);

CREATE TABLE IF NOT EXISTS daily_spark_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    role TEXT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS daily_spark_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    user TEXT,
    text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (question_id) REFERENCES daily_spark_questions(id)
);
CREATE INDEX IF NOT EXISTS idx_daily_spark_answers_question_id ON daily_spark_answers (question_id);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    salary TEXT,
    date_posted DATE,
    type TEXT,
    experience TEXT,
    imageUrl TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    search_term TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history (user_id);

CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    icon TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT NOT NULL,
    type TEXT NOT NULL,
    related_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id);

CREATE TABLE IF NOT EXISTS applied_hackathons (
    user_id INTEGER,
    hackathon_id INTEGER,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, hackathon_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id)
);
CREATE INDEX IF NOT EXISTS idx_applied_hackathons_user_id ON applied_hackathons (user_id);
CREATE INDEX IF NOT EXISTS idx_applied_hackathons_hackathon_id ON applied_hackathons (hackathon_id);

CREATE TABLE IF NOT EXISTS user_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, -- Foreign key to the users table (can be NULL if not logged in)
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- e.g., 'pending', 'in_progress', 'resolved'
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_user_issues_user_id ON user_issues (user_id);

-- Insert Sample Data
INSERT INTO users (name, email, activity_score, achievements, alumni_gems, department, profession, alma_mater, interviews, internships, startups, current_company, milestones, advice, likes, badges, solved, links)
VALUES
    ('John Doe', 'john.doe@example.com', 100, 'Published a paper', 10, 'Computer Science', 'Software Engineer', 'University of Tech', 'Google, Amazon', 'Microsoft', 'MyStartup', 'TechCorp', 'Founded a company', 'Work hard!', 5, 2, 10, 3),
    ('Jane Smith', 'jane.smith@example.com', 120, 'Won a hackathon', 15, 'Electrical Engineering', 'Data Scientist', 'State College', 'Facebook', 'Tesla', NULL, 'DataCo', 'Led a project', 'Be curious!', 8, 3, 15, 5),
    ('Bob Johnson', 'bob.johnson@example.com', 80, 'Patent holder', 5, 'Mechanical Engineering', 'Product Manager', 'City University', 'Apple', NULL, 'GreenTech', 'InnovateX', 'Launched a product', 'Never give up!', 3, 1, 5, 1),
    ('sri','sri@gmail.com', 80, 'Patent holder', 5, 'Mechanical Engineering', 'Product Manager', 'City University', 'Apple', NULL, 'GreenTech', 'InnovateX', 'Launched a product', 'Never give up!', 3, 1, 5, 1);

INSERT INTO user_connections (user_id, connected_user_id)
VALUES
    (1, 2),
    (1, 3),
    (2, 3);

INSERT INTO career_fairs (name, date, location, description)
VALUES
    ('Tech Career Fair', '2024-03-10', 'Tech Hall', 'Meet top tech companies'),
    ('Engineering Expo', '2024-04-15', 'City Center', 'Explore engineering opportunities');

INSERT INTO internships (title, company, start_date, end_date, description)
VALUES
    ('Software Engineering Intern', 'Google', '2024-05-20', '2024-08-15', 'Work on a real-world project'),
    ('Data Science Intern', 'Facebook', '2024-06-01', '2024-09-01', 'Analyze large datasets');

INSERT INTO hackathons (name, date, location, description, theme, prize_pool)
VALUES
    ('Hackathon X', '2024-07-01', 'Online', 'Build innovative solutions', 'AI', '$10000'),
    ('CodeFest', '2024-08-01', 'University Campus', '24-hour coding challenge', 'Web Development', '$5000');

INSERT INTO questions (user_id, question_text)
VALUES
    (1, 'What is the best programming language for beginners?'),
    (2, 'How do I prepare for a data science interview?'),
    (3, 'What are some good resources for learning web development?');

INSERT INTO chat_contacts (name)
VALUES
    ('Alice'),
    ('Bob'),
    ('Charlie');

INSERT INTO chat_messages (contact_id, sender, text, file_path)
VALUES
    (1, 'me', 'Hello Alice!', NULL),
    (1, 'Alice', 'Hi John!', NULL),
    (2, 'me', 'How is the project going?', NULL),
    (2, 'Bob', 'It is going well', 'report.pdf');

INSERT INTO daily_spark_questions (company, role, question)
VALUES
    ('Google', 'Software Engineer', 'What is the most challenging bug you have ever faced?'),
    ('Amazon', 'Data Scientist', 'Describe a time you had to deal with messy data.');

INSERT INTO daily_spark_answers (question_id, user, text, votes)
VALUES
    (1, 'Jane Smith', 'I once spent days debugging a memory leak...', 10),
    (1, 'Bob Johnson', 'A tricky off-by-one error caused a lot of problems.', 5),
    (2, 'John Doe', 'I had to clean a dataset with missing values and outliers.', 12);

INSERT INTO jobs (title, company, location, description, salary, date_posted, type, experience, imageUrl)
VALUES
    ('Software Engineer', 'TechCorp', 'New York, NY', 'Develop cutting-edge applications', '$120,000 - $150,000', '2024-02-15', 'Full-time', '2+ years', 'https://example.com/techcorp.png'),
    ('Data Scientist', 'DataCo', 'San Francisco, CA', 'Build machine learning models', '$110,000 - $140,000', '2024-02-10', 'Full-time', '1+ years', 'https://example.com/dataco.png'),
    ('Web Developer', 'WebDev Solutions', 'Austin, TX', 'Create responsive web applications', '$80,000 - $100,000', '2024-02-01', 'Full-time', '1+ years', null);

INSERT INTO search_history (user_id, search_term)
VALUES
    (1, 'Software Engineer'),
    (1, 'Data Science'),
    (2, 'Web Development');

INSERT INTO features (name, description, url, icon)
VALUES
    ('Profile', 'View and edit your profile', '/profile.html', 'person-circle'),
    ('Connections', 'Manage your connections', 'connections.html', 'people'),
    ('Jobs', 'Find job opportunities', 'career-fairs.html', 'briefcase'),
    ('Events', 'See upcoming events', 'explore-hackathons.html', 'calendar');

INSERT INTO notifications (user_id, message, type, related_id)
VALUES
    (1, 'Jane Smith connected with you!', 'connection', 2),
    (2, 'New hackathon "AI Challenge" announced!', 'hackathon', 1);

INSERT INTO applied_hackathons (user_id, hackathon_id)
VALUES
    (1, 1),
    (2, 1);

INSERT INTO user_issues (user_id, name, email, message)
VALUES
    (3, 'Bob Johnson', 'bob.johnson@example.com', 'The job listings are not loading.');