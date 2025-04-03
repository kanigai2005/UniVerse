from fastapi import FastAPI, HTTPException
import sqlite3
from datetime import date

app = FastAPI()

DATABASE_NAME = "explore.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
async def startup():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            activity_score INTEGER,
            achievements TEXT,
            alumni_gems INTEGER
        )
    """)

    # Create career_fairs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS career_fairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            location TEXT,
            description TEXT
        )
    """)

    # Create internships table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            start_date TEXT,
            end_date TEXT,
            description TEXT
        )
    """)

    # Create hackathons table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hackathons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            location TEXT,
            description TEXT
        )
    """)

    # Insert dummy data (if tables are empty)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users (name, email, activity_score, achievements, alumni_gems) VALUES (?, ?, ?, ?, ?)", [
            ("Alex Johnson", "alex@example.com", 50, "Mentorship Pro, Top Contributor", 10),
            ("Sarah Lee", "sarah@example.com", 42, "Job Connector", 8),
            ("Michael Carter", "michael@example.com", 38, "Mentor Pro", 5),
        ])

    cursor.execute("SELECT COUNT(*) FROM career_fairs")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO career_fairs (name, date, location, description) VALUES (?, ?, ?, ?)", [
            ("Tech Career Fair", "2024-12-15", "San Francisco", "Meet top tech companies."),
            ("Engineering Jobs", "2025-01-10", "New York", "Find engineering jobs."),
        ])

    cursor.execute("SELECT COUNT(*) FROM internships")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO internships (title, company, start_date, end_date, description) VALUES (?, ?, ?, ?, ?)", [
            ("Software Dev Intern", "Google", "2024-12-01", "2025-03-01", "Work on cool projects."),
            ("Data Science Intern", "Amazon", "2025-01-15", "2025-04-15", "Analyze large datasets."),
        ])

    cursor.execute("SELECT COUNT(*) FROM hackathons")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO hackathons (name, date, location, description) VALUES (?, ?, ?, ?)", [
            ("AI Hackathon", "2024-12-10", "Online", "Develop innovative AI solutions."),
            ("Web Dev Challenge", "2025-01-20", "San Francisco", "Showcase your web development skills."),
        ])

    conn.commit()
    conn.close()

@app.get("/career_fairs")
async def get_career_fairs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM career_fairs WHERE date >= ? ORDER BY date ASC", (str(date.today()),))
    career_fairs = cursor.fetchall()
    conn.close()
    return [dict(fair) for fair in career_fairs]

@app.get("/internships")
async def get_internships():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM internships WHERE start_date >= ? ORDER BY start_date ASC", (str(date.today()),))
    internships = cursor.fetchall()
    conn.close()
    return [dict(internship) for internship in internships]

@app.get("/hackathons")
async def get_hackathons():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hackathons WHERE date >= ? ORDER BY date ASC", (str(date.today()),))
    hackathons = cursor.fetchall()
    conn.close()
    return [dict(hackathon) for hackathon in hackathons]

@app.get("/leaderboard")
async def get_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY activity_score DESC, alumni_gems DESC")
    users = cursor.fetchall()
    conn.close()

    return [
        {
            "name": user["name"],
            "activity_score": user["activity_score"],
            "achievements": user["achievements"].split(",") if user["achievements"] else [],
            "alumni_gems": user["alumni_gems"]
        }
        for user in users
    ]

@app.get("/user/{username}")
async def get_user(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user["name"],
        "email": user["email"],
        "activity_score": user["activity_score"],
        "achievements": user["achievements"].split(",") if user["achievements"] else [],
        "alumni_gems": user["alumni_gems"]
    }
@app.get("/")
async def root():
    return {"message": "Welcome to the Explore API!"}