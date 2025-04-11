from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from datetime import date, datetime
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import uvicorn
import sqlite3

app = FastAPI()

# --- Database Setup ---
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'explore.db')}"
print(f"Database URL: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    activity_score = Column(Integer)
    achievements = Column(Text)
    alumni_gems = Column(Integer)

class CareerFair(Base):
    __tablename__ = "career_fairs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    location = Column(String)
    description = Column(Text)

class Internship(Base):
    __tablename__ = "internships"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)

class Hackathon(Base):
    __tablename__ = "hackathons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    location = Column(String)
    description = Column(Text)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # Assuming users table exists
    question_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)

# --- Pydantic Models for Request/Response ---
class QuestionCreate(BaseModel):
    question_text: str

class QuestionOut(BaseModel):
    id: int
    user_id: int
    question_text: str
    created_at: datetime
    likes: int

    class Config:
        orm_mode = True

# --- Frontend Serving ---
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend-exp")
explore_html_path = os.path.join(frontend_dir, "explore.html")
career_fairs_html_path = os.path.join(frontend_dir, "career-fairs.html")
expertqa_html_path = os.path.join(frontend_dir, "expertqa.html")
explore_hackathon_html_path = os.path.join(frontend_dir, "explore-hackathons.html")
internship_html_path = os.path.join(frontend_dir, "intership.html")
leader_profile_html_path = os.path.join(frontend_dir, "leader-profile.html")
leaderboard_html_path = os.path.join(frontend_dir, "leaderboard.html")
static_dir = os.path.join(frontend_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_explore_html():
    return FileResponse(explore_html_path)

@app.get("/career-fairs.html")
async def serve_career_fairs_html():
    return FileResponse(career_fairs_html_path)

@app.get("/expertqa.html")
async def serve_expertqa_html():
    return FileResponse(expertqa_html_path)

@app.get("/explore-hackathons.html")
async def serve_explore_hackathon_html():
    return FileResponse(explore_hackathon_html_path)

@app.get("/intership.html")
async def serve_intership_html():
    return FileResponse(internship_html_path)

@app.get("/leader-profile.html")
async def serve_leader_profile_html():
    return FileResponse(leader_profile_html_path)

@app.get("/leaderboard.html")
async def serve_leaderboard_html():
    return FileResponse(leaderboard_html_path)

# --- API Endpoints for Expert Q&A ---
BASE_API_PATH = "/api"

@app.get(f"{BASE_API_PATH}/questions/popular", response_model=List[QuestionOut])
async def get_popular_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.likes.desc(), Question.created_at.desc()).all()
    return questions

@app.post(f"{BASE_API_PATH}/questions", response_model=QuestionOut)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    # In a real application, get the user_id from the logged-in user
    db_question = Question(question_text=question.question_text, user_id=1) # Assuming user_id 1 for now
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.get(f"{BASE_API_PATH}/users/{{user_id}}/questions", response_model=List[QuestionOut])
async def get_user_questions(user_id: int, db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.user_id == user_id).order_by(Question.created_at.desc()).all()
    return questions

@app.post(f"{BASE_API_PATH}/questions/{{question_id}}/like")
async def like_question(question_id: int, db: Session = Depends(get_db)):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question:
        db_question.likes += 1
        db.commit()
        db.refresh(db_question)
        return {"message": f"Question {question_id} liked!"}
    else:
        raise HTTPException(status_code=404, detail="Question not found")

# --- Existing API Endpoints (No Changes Needed for Q&A) ---
@app.get(f"{BASE_API_PATH}/career_fairs")
async def get_career_fairs(db: Session = Depends(get_db)):
    career_fairs = db.query(CareerFair).all()
    return career_fairs

@app.get(f"{BASE_API_PATH}/internships")
async def get_internships(db: Session = Depends(get_db)):
    internships = db.query(Internship).filter(Internship.start_date >= date.today()).order_by(Internship.start_date).all()
    return internships

@app.get(f"{BASE_API_PATH}/hackathons")
async def get_hackathons(db: Session = Depends(get_db)):
    hackathons = db.query(Hackathon).filter(Hackathon.date >= date.today()).order_by(Hackathon.date).all()
    return hackathons

@app.get(f"{BASE_API_PATH}/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.activity_score.desc(), User.alumni_gems.desc()).all()
    return [
        {
            "name": user.name,
            "activity_score": user.activity_score,
            "achievements": user.achievements.split(",") if user.achievements else [],
            "alumni_gems": user.alumni_gems
        }
        for user in users
    ]

@app.get(f"{BASE_API_PATH}/user/{{username}}")
async def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "name": user.name,
        "email": user.email,
        "activity_score": user.activity_score,
        "achievements": user.achievements.split(",") if user.achievements else [],
        "alumni_gems": user.alumni_gems
    }

# --- Database Initialization ---
async def initialize_database():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'explore.db')
    schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    conn = None
    try:
        print(f"Initializing database from schema: {schema_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        with open(schema_file, 'r') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        conn.commit()
        print("Database initialized successfully from schema.")
    except sqlite3.Error as e:
        print(f"Error initializing database from schema: {e}")
    finally:
        if conn:
            conn.close()

# --- Main Execution ---
async def main():
    await initialize_database()
    uvicorn.run("explore.backend-exp.exp:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())