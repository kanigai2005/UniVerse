from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, func, ForeignKey, desc, Table
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Dict, Optional
from datetime import date, datetime
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import asyncio
import uvicorn
import sqlite3
import uuid
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Database Setup ---
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'explore.db')}"
logger.info(f"Database URL: {DATABASE_URL}")
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
    department = Column(String)
    profession = Column(String)
    alma_mater = Column(String)
    interviews = Column(Text)
    internships = Column(Text)
    startups = Column(Text)
    current_company = Column(String)
    milestones = Column(Text)
    advice = Column(Text)
    likes = Column(Integer, default=0)
    badges = Column(Text, nullable=True)
    solved = Column(Integer, nullable=True)
    links = Column(Text, nullable=True)

    connections = relationship("User", secondary="user_connections", primaryjoin="User.id==user_connections.c.user_id", secondaryjoin="User.id==user_connections.c.connected_user_id")

user_connections = Table(
    "user_connections",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("connected_user_id", Integer, ForeignKey("users.id")),
)

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
    user_id = Column(Integer, ForeignKey("users.id"))
    question_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)

class ChatContact(Base):
    __tablename__ = "chat_contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("chat_contacts.id"))
    sender = Column(String)  # 'me' or 'other'
    text = Column(String, nullable=True)
    file_path = Column(String, nullable=True)  # Store file path
    timestamp = Column(DateTime, default=datetime.utcnow)

class DailySparkQuestion(Base):
    __tablename__ = "daily_spark_questions"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    role = Column(String)
    question = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailySparkAnswer(Base):
    __tablename__ = "daily_spark_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("daily_spark_questions.id"))
    user = Column(String)
    text = Column(Text)
    votes = Column(Integer, default=0)

class AlumniResponse(BaseModel):
    id: int
    name: str
    profession: str
    alma_mater: str
    interviews: str
    internships: str
    startups: str
    current_company: str
    milestones: str
    advice: str
    department: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    activity_score: int
    achievements: str
    alumni_gems: int
    department: str
    profession: str
    alma_mater: str
    interviews: str
    internships: str
    startups: str
    current_company: str
    milestones: str
    advice: str
    likes: int
    badges: Optional[str] = None
    solved: Optional[int] = None
    links: Optional[str] = None

    class Config:
        from_attributes = True

class DailySparkQuestionOut(BaseModel):
    id: int
    company: str
    role: str
    question: str
    answers: List["DailySparkAnswerOut"]

    class Config:
        from_attributes = True

class DailySparkAnswerOut(BaseModel):
    id: int
    user: str
    text: str
    votes: int

    class Config:
        from_attributes = True

class DailySparkSubmit(BaseModel):
    text: str

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
        from_attributes = True

class ChatMessageCreate(BaseModel):
    contact_id: int
    text: Optional[str] = None
    file_path: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: int
    contact_id: int
    sender: str
    text: Optional[str] = None
    file_path: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatContactOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# --- Frontend Serving ---
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-exp")
home_html_path = os.path.join(frontend_dir, "home.html")
daily_spark_html_path = os.path.join(frontend_dir, "dailyspark.html")
explore_html_path = os.path.join(frontend_dir, "explore.html")
career_fairs_html_path = os.path.join(frontend_dir, "career-fairs.html")
expertqa_html_path = os.path.join(frontend_dir, "expertqa.html")
explore_hackathon_html_path = os.path.join(frontend_dir, "explore-hackathons.html")
internship_html_path = os.path.join(frontend_dir, "intership.html")
leader_profile_html_path = os.path.join(frontend_dir, "leader-profile.html")
leaderboard_html_path = os.path.join(frontend_dir, "leaderboard.html")
alumni_roadmap_html_path = os.path.join(frontend_dir, "alumni-roadmaps.html")
chat_html_path = os.path.join(frontend_dir, "chat.html")
connections_html_path = os.path.join(frontend_dir, "connection.html")
profile_html_path = os.path.join(frontend_dir, "profile.html")
static_dir = os.path.join(frontend_dir, "static")
templates = Jinja2Templates(directory=frontend_dir)

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

def serve_file(file_path: str):
    logger.info(f"Serving file: {file_path}")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/")
async def serve_home_html():
    return serve_file(home_html_path)

@app.get("/home.html", response_class=FileResponse)
async def serve_home():
    return serve_file(os.path.join(frontend_dir, "home.html"))

@app.get("/dailyspark.html", response_class=FileResponse)
async def serve_daily_spark():
    return serve_file(os.path.join(frontend_dir, "dailyspark.html"))

@app.get("/explore.html", response_class=FileResponse)
async def serve_explore():
    return serve_file(os.path.join(frontend_dir, "explore.html"))

@app.get("/career-fairs.html")
async def serve_career_fairs_html():
    return serve_file(career_fairs_html_path)

@app.get("/expertqa.html")
async def serve_expertqa_html():
    return serve_file(expertqa_html_path)

@app.get("/explore-hackathons.html")
async def serve_explore_hackathon_html():
    return serve_file(explore_hackathon_html_path)

@app.get("/intership.html")
async def serve_internship_html():
    return serve_file(internship_html_path)

@app.get("/leader-profile.html")
async def serve_leader_profile_html():
    return serve_file(leader_profile_html_path)

@app.get("/leaderboard.html")
async def serve_leaderboard_html():
    return serve_file(leaderboard_html_path)

@app.get("/alumni-roadmaps.html")
async def serve_alumni_roadmap_html():
    return serve_file(alumni_roadmap_html_path)

@app.get("/chat.html")
async def serve_chat_html():
    return serve_file(chat_html_path)

@app.get("/profile.html", response_class=HTMLResponse)
async def serve_profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/connection.html", response_class=FileResponse)
async def serve_connections():
    return serve_file(connections_html_path)

# --- API Endpoints for Expert Q&A ---
BASE_API_PATH = "/api"

@app.get(f"{BASE_API_PATH}/questions/popular", response_model=List[QuestionOut])
async def get_popular_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.likes.desc(), Question.created_at.desc()).all()
    return questions

@app.post(f"{BASE_API_PATH}/questions", response_model=QuestionOut)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    db_question = Question(question_text=question.question_text, user_id=1)
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

# --- Existing API Endpoints ---
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

@app.get(f"{BASE_API_PATH}/user/{{username}}", response_model=UserResponse)
async def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get(f"{BASE_API_PATH}/alumni/top-liked", response_model=Dict[str, List[AlumniResponse]])
async def get_top_liked_alumni(db: Session = Depends(get_db)):
    alumni = db.query(User).filter(User.department.isnot(None)).order_by(desc(User.likes)).limit(5).all()
    grouped_alumni = {}
    for a in alumni:
        if a.department not in grouped_alumni:
            grouped_alumni[a.department] = []
        grouped_alumni[a.department].append(a)
    return grouped_alumni

@app.get(f"{BASE_API_PATH}/alumni/{{alumni_id}}", response_model=AlumniResponse)
async def get_alumni_details(alumni_id: int, db: Session = Depends(get_db)):
    alumni = db.query(User).filter(User.id == alumni_id).first()
    if alumni is None:
        raise HTTPException(status_code=404, detail="Alumni not found")
    return alumni

@app.get(f"{BASE_API_PATH}/alumni/{{alumni_id}}/like")
async def like_alumni(alumni_id: int, db: Session = Depends(get_db)):
    alumni = db.query(User).filter(User.id == alumni_id).first()
    if alumni:
        alumni.likes += 1
        db.commit()
        db.refresh(alumni)
        return {"message": "Alumni liked successfully"}
    else:
        raise HTTPException(status_code=404, detail="Alumni not found")

# --- Chat API Endpoints ---
@app.get(f"{BASE_API_PATH}/contacts", response_model=List[ChatContactOut])
async def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(ChatContact).all()
    return contacts

@app.get(f"{BASE_API_PATH}/chat/{{contact_id}}", response_model=List[ChatMessageOut])
async def get_chat_history(contact_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.contact_id == contact_id).order_by(ChatMessage.timestamp).all()
    return messages

@app.post(f"{BASE_API_PATH}/send-message", response_model=ChatMessageOut)
async def send_message(message: ChatMessageCreate, db: Session = Depends(get_db)):
    try:
        db_message = ChatMessage(contact_id=message.contact_id, text=message.text, sender='me')
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {e}")

@app.post(f"{BASE_API_PATH}/upload-file")
async def upload_file(
    contact_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        db_message = ChatMessage(contact_id=contact_id, file_path=unique_filename, sender='me')
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return {"file_path": unique_filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/{file_path:path}")
async def get_uploaded_file(file_path: str):
    full_path = os.path.join("uploads", file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

# --- Profile and Connections API Endpoints ---
@app.get(f"{BASE_API_PATH}/users/{{username}}", response_model=UserResponse)
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get(f"{BASE_API_PATH}/users/{{username}}/connections", response_model=List[UserResponse])
async def get_user_connections(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    connections = db.query(User).join(user_connections, (user_connections.c.connected_user_id == User.id)).filter(user_connections.c.user_id == user.id).all()
    return connections

@app.get(f"{BASE_API_PATH}/users/{{username}}/suggestions", response_model=List[UserResponse])
async def get_user_suggestions(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    suggestions = db.query(User).filter(User.id != user.id).limit(10).all()
    return suggestions

@app.post(f"{BASE_API_PATH}/users/{{username}}/follow/{{suggestion_username}}")
async def follow_user(username: str, suggestion_username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    suggestion_user = db.query(User).filter(User.name == suggestion_username).first()
    if not user or not suggestion_user:
        raise HTTPException(status_code=404, detail="User not found")
    user.connections.append(suggestion_user)
    db.commit()
    return {"message": f"Followed {suggestion_username}"}

@app.post(f"{BASE_API_PATH}/users/{{username}}/edit")
async def edit_user_profile(username: str, request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in form_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    db.commit()
    return {"message": "Profile updated successfully"}

# --- Daily Spark API Endpoints ---
@app.get(f"{BASE_API_PATH}/daily-spark/today", response_model=DailySparkQuestionOut)
async def get_todays_question(db: Session = Depends(get_db)):
    today_question = db.query(DailySparkQuestion).order_by(DailySparkQuestion.created_at.desc()).first()
    if not today_question:
        raise HTTPException(status_code=404, detail="Today's question not found")
    answers = db.query(DailySparkAnswer).filter(DailySparkAnswer.question_id == today_question.id).all()
    return DailySparkQuestionOut(
        id=today_question.id,
        company=today_question.company,
        role=today_question.role,
        question=today_question.question,
        answers=answers
    )

@app.get(f"{BASE_API_PATH}/daily-spark/top-liked", response_model=List[DailySparkQuestionOut])
async def get_top_liked_questions(db: Session = Depends(get_db)):
    questions = db.query(DailySparkQuestion).join(DailySparkAnswer, DailySparkAnswer.question_id == DailySparkQuestion.id, isouter=True).group_by(DailySparkQuestion.id).order_by(desc(func.sum(DailySparkAnswer.votes))).limit(5).all()
    result = []
    for question in questions:
        answers = db.query(DailySparkAnswer).filter(DailySparkAnswer.question_id == question.id).all()
        result.append(DailySparkQuestionOut(
            id=question.id,
            company=question.company,
            role=question.role,
            question=question.question,
            answers=answers
        ))
    return result

@app.post(f"{BASE_API_PATH}/daily-spark/submit")
async def submit_question_or_answer(data: DailySparkSubmit, db: Session = Depends(get_db)):
    if "question" in data.text.lower():
        new_question = DailySparkQuestion(question=data.text)
        db.add(new_question)
    else:
        today_question = db.query(DailySparkQuestion).order_by(DailySparkQuestion.created_at.desc()).first()
        if not today_question:
            raise HTTPException(status_code=404, detail="Today's question not found")
        new_answer = DailySparkAnswer(question_id=today_question.id, text=data.text, user="Anonymous")
        db.add(new_answer)
    db.commit()
    return {"message": "Submission successful"}

@app.post(f"{BASE_API_PATH}/daily-spark/upvote/{{question_id}}/{{answer_id}}")
async def upvote_answer(question_id: int, answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id, DailySparkAnswer.question_id == question_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    answer.votes += 1
    db.commit()
    return {"votes": answer.votes}

@app.post(f"{BASE_API_PATH}/daily-spark/downvote/{{question_id}}/{{answer_id}}")
async def downvote_answer(question_id: int, answer_id: int, db: Session = Depends(get_db)):
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id, DailySparkAnswer.question_id == question_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    answer.votes -= 1
    db.commit()
    return {"votes": answer.votes}

# --- Database Initialization ---
async def initialize_database():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'explore.db')
    schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    conn = None
    try:
        logger.info(f"Initializing database from schema: {schema_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        with open(schema_file, 'r') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        conn.commit()
        logger.info("Database initialized successfully from schema.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database from schema: {e}")
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_file}")
    finally:
        if conn:
            conn.close()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Main Execution ---
async def main():
    await initialize_database()
    uvicorn.run("exp:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())