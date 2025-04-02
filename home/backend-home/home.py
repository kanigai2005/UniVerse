from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import datetime
import os

app = FastAPI()

# Set up templates and static directories
templates = Jinja2Templates(directory="home/frontend-home")
app.mount("/static", StaticFiles(directory="home/frontend-home/static"), name="static")

# Database connection
db_path = os.path.join(os.path.dirname(__file__), 'universe.db')


def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.post("/api/search")
async def search(request: Request):
    """
    Handles search queries.
    Fetches matching events and alumni from the database.
    Inserts the search query into the search_history table.
    Returns the results as JSON.
    """
    body = await request.json()
    query = body.get("query", "").lower()

    conn = get_db_connection()
    events = conn.execute(
        'SELECT * FROM events WHERE event_name LIKE ? OR description LIKE ?',
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    alumni = conn.execute(
        'SELECT * FROM alumni WHERE name LIKE ? OR career_path LIKE ?',
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    conn.execute(
        'INSERT INTO search_history (query, timestamp) VALUES (?, ?)',
        (query, datetime.datetime.now())
    )
    conn.commit()
    conn.close()

    results = [dict(event) for event in events] + [dict(alumnus) for alumnus in alumni]
    return JSONResponse(content={"results": results})


@app.get("/api/search_history")
def search_history():
    """
    Retrieves the user's search history from the database.
    Returns the history as JSON.
    """
    conn = get_db_connection()
    history = conn.execute(
        'SELECT * FROM search_history ORDER BY timestamp DESC'
    ).fetchall()
    conn.close()
    return JSONResponse(content={"history": [dict(row) for row in history]})


@app.get("/api/suggestions")
def suggestions(query: str = ""):
    """
    Retrieves suggestions from the database based on the user's input.
    """
    query = query.lower()
    conn = get_db_connection()
    suggestions = conn.execute(
        '''
        SELECT query FROM suggestions 
        WHERE query LIKE ? 
        ORDER BY LENGTH(query) - LENGTH(REPLACE(query, ?, "")) DESC
        ''',
        ('%' + query + '%', query)
    ).fetchall()
    conn.close()
    return JSONResponse(content={"suggestions": [row[0] for row in suggestions]})


def create_tables():
    """
    Creates the necessary tables in the database if they don't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            description TEXT,
            date TEXT,
            location TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumni (
            alumni_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            career_path TEXT,
            achievements TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            search_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Call create_tables() when the app starts
@app.on_event("startup")
def startup_event():
    create_tables()

    # Populate data (for testing)
    conn = get_db_connection()
    conn.execute("INSERT OR IGNORE INTO events (event_name, description) VALUES ('Hackathon 2024', 'Coding challenge')")
    conn.execute("INSERT OR IGNORE INTO events (event_name, description) VALUES ('Alumni Meetup', 'Networking event')")
    conn.execute("INSERT OR IGNORE INTO events (event_name, description) VALUES ('Webinar: Career Tips', 'Career development')")

    conn.execute("INSERT OR IGNORE INTO alumni (name, career_path) VALUES ('John Doe', 'Software Engineer')")
    conn.execute("INSERT OR IGNORE INTO alumni (name, career_path) VALUES ('Jane Smith', 'Data Scientist')")

    # Insert initial suggestions
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Hackathon')")
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Alumni Meetup')")
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Career Tips')")
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Hack')")
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Alumni')")
    conn.execute("INSERT OR IGNORE INTO suggestions (query) VALUES ('Career')")
    conn.commit()
    conn.close()


@app.get("/")
def index(request: Request):
    """
    Renders the home page (index.html).
    """
    return templates.TemplateResponse("home.html", {"request": request})