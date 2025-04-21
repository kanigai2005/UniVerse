from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form, Request
from sqlalchemy import create_engine, Column, Integer, Boolean, String, Date, Text, DateTime, func, ForeignKey, desc, Table
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, EmailStr
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.dialects.sqlite import DATE as SQLiteDATE
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

Base.metadata.create_all(bind=engine)

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
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    activity_score = Column(Integer, default=0)
    achievements = Column(Text)
    alumni_gems = Column(Integer, default=0)
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
    badges = Column(Integer, default=0)
    solved = Column(Integer, default=0)
    links = Column(Integer, default=0)

    connections = relationship("UserConnection", foreign_keys="[UserConnection.user_id]", back_populates="user")
    connected_users = relationship("UserConnection", foreign_keys="[UserConnection.connected_user_id]", back_populates="connected_user")
    questions = relationship("Question", back_populates="user")
    issues = relationship("UserIssue", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    applied_hackathons = relationship("AppliedHackathon", back_populates="user")


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
    theme = Column(String)
    prize_pool = Column(String)
    applications = relationship("AppliedHackathon", back_populates="hackathon")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    user = relationship("User", back_populates="questions")

class ChatContact(Base):
    __tablename__ = "chat_contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    messages = relationship("ChatMessage", back_populates="contact")
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("chat_contacts.id"))
    sender = Column(String)     # 'me' or 'other'
    text = Column(String, nullable=True)
    file_path = Column(String, nullable=True)     # Store file path
    timestamp = Column(DateTime, default=datetime.utcnow)
    contact = relationship("ChatContact", back_populates="messages")


class DailySparkQuestion(Base):
    __tablename__ = "daily_spark_questions"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    role = Column(String)
    question = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    answers = relationship("DailySparkAnswer", back_populates="question")

class DailySparkAnswer(Base):
    __tablename__ = "daily_spark_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("daily_spark_questions.id"))
    user = Column(String)
    text = Column(Text)
    votes = Column(Integer, default=0)
    question = relationship("DailySparkQuestion", back_populates="answers")

class Job(Base):   # Added Job model
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    description = Column(Text)
    salary = Column(String)
    date_posted = Column(Date, default=date.today)
    type = Column(String)
    experience = Column(String)
    imageUrl = Column(String, nullable=True)

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)   # Store user ID as string
    search_term = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    url = Column(String)
    icon = Column(String)

class AppliedHackathon(Base):
    __tablename__ = "applied_hackathons"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    hackathon_id = Column(Integer, ForeignKey("hackathons.id"), primary_key=True)
    applied_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="applied_hackathons")
    hackathon = relationship("Hackathon", back_populates="applications")

    def __repr__(self):
        return f"<AppliedHackathon user_id={self.user_id}, hackathon_id={self.hackathon_id}, applied_at={self.applied_at}>"

class UserIssue(Base):
    __tablename__ = "user_issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

    user = relationship("User", back_populates="issues") # Assuming you add 'issues' relationship to User model

class UserConnection(Base):
    __tablename__ = "user_connections"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    connected_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="connections")
    connected_user = relationship("User", foreign_keys=[connected_user_id], back_populates="connected_users")

class AlumniResponse(BaseModel):
    id: int
    name: str
    profession: str
    alma_mater: Optional[str] = ""
    interviews: Optional[str] = ""
    internships: Optional[str] = ""
    startups: Optional[str] = ""
    current_company: Optional[str] = ""
    milestones: Optional[str] = ""
    advice: Optional[str] = ""
    department: str
    likes: int

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
    interviews: Optional[str] = None
    internships: Optional[str] = None
    startups: Optional[str] = None
    current_company: str
    milestones: str
    advice: str
    likes: int
    badges: Optional[int] = None
    solved: Optional[int] = None
    links: Optional[int] = None

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

class JobOut(BaseModel): #added JobOut
    id: int
    title: str
    company: str
    location: str
    description: str
    salary: str
    date_posted: date
    type: str
    experience: str
    imageUrl: Optional[str] = None

    class Config:
        from_attributes = True

class HackathonOut(BaseModel):
    id: int
    name: str
    date: date
    location: str
    description: str
    theme: Optional[str] = None
    prize_pool: Optional[str] = None

    class Config:
        from_attributes = True   # Use this instead of orm_mode in Pydantic v2


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

class DailySparkSubmit(BaseModel):
    text: str

class SearchResult(BaseModel):
    name: str

    class Config:
        from_attributes = True

class SearchHistoryItem(BaseModel):
    id: int
    user_id: str
    search_term: str
    timestamp: datetime

    class Config:
        from_attributes = True

class Event(BaseModel):
    id: int
    name: str
    description: str
    date: date
    location: str

    class Config:
        from_attributes = True

class FeatureOut(BaseModel):
    id: int
    name: str
    description: str
    url: str
    icon: str

    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    id: int
    message: str
    type: str
    related_id: Optional[int] = None
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class NotificationMarkRead(BaseModel):
    notification_ids: List[int]

class UserIssueCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class UserIssueResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    message: str
    submitted_at: datetime
    status: str

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

async def send_hackathon_reminders(db: Session):
    twenty_four_hours_from_now = datetime.utcnow() + timedelta(hours=24)
    upcoming_hackathons = db.query(Hackathon).filter(Hackathon.date <= twenty_four_hours_from_now, Hackathon.date > datetime.utcnow()).all()

    for hackathon in upcoming_hackathons:
        applied_users = db.query(User).join(
            AppliedHackathon, AppliedHackathon.c.user_id == User.id
        ).filter(AppliedHackathon.c.hackathon_id == hackathon.id).all()

        for user in applied_users:
            existing_reminder = db.query(Notification).filter(
                Notification.user_id == user.id,
                Notification.type == "hackathon_reminder",
                Notification.related_id == hackathon.id
            ).first()
            if not existing_reminder:
                notification = Notification(
                    user_id=user.id,
                    message=f"Reminder: Your hackathon '{hackathon.name}' starts in 24 hours.",
                    type="hackathon_reminder",
                    related_id=hackathon.id
                )
                db.add(notification)
    db.commit()

# You would call this function periodically
# asyncio.create_task(send_hackathon_reminders(SessionLocal()))

def create_new_hackathon_notifications(db: Session, hackathon: Hackathon):
    users = db.query(User).all()   # Or filter based on interests
    for user in users:
        notification = Notification(
            user_id=user.id,
            message=f"New Hackathon Alert: '{hackathon.name}' is now available!",
            type="new_hackathon",
            related_id=hackathon.id
        )
        db.add(notification)
    db.commit()

def create_new_job_notifications(db: Session, job: Job):
    users = db.query(User).all()   # Or filter based on profession/department
    for user in users:
        notification = Notification(
            user_id=user.id,
            message=f"New Job Alert: '{job.title}' at {job.company}!",
            type="new_job",
            related_id=job.id
        )
        db.add(notification)
    db.commit()

def create_new_internship_notifications(db: Session, internship: Internship):
    users = db.query(User).all()   # Or filter based on department/interest
    for user in users:
        notification = Notification(
            user_id=user.id,
            message=f"New Internship Opportunity: '{internship.title}' at {internship.company}!",
            type="new_internship",
            related_id=internship.id
        )
        db.add(notification)
    db.commit()

def create_daily_spark_notification(db: Session, question: DailySparkQuestion):
    users = db.query(User).all()
    for user in users:
        notification = Notification(
            user_id=user.id,
            message="Solve today’s Daily Spark!",
            type="daily_spark",
            related_id=question.id
        )
        db.add(notification)
    db.commit()

def create_alumni_roadmap_notification(db: Session, roadmap_title: str): # You'll need a way to track new roadmaps
    users = db.query(User).all()
    for user in users:
        notification = Notification(
            user_id=user.id,
            message=f"New roadmap from top alumni: '{roadmap_title}'",
            type="alumni_roadmap"
            # You might not have a related_id for general roadmaps
        )
        db.add(notification)
    db.commit()

# You would call these functions when new items are added to the respective tables

@app.get("/")
async def serve_home_html():
    return serve_file(home_html_path)

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if user:
        logged_in_user_id = user.id
        print(f"[exp.py] Serving home for user ID: {logged_in_user_id}")
        return templates.TemplateResponse("home.html", {"request": request, "user_id": logged_in_user_id})
    else:
        return HTMLResponse("User not found.", status_code=404)

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
async def serve_profile(request: Request, username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if user:
        logger.info(f"[exp.py] Serving profile for user ID: {user.id}")
        return templates.TemplateResponse("profile.html", {"request": request, "user_id": user.id})
    else:
        return HTMLResponse("User not found.", status_code=404)
    
@app.get("/connection.html", response_class=FileResponse)
async def serve_connections():
    return serve_file(connections_html_path)

@app.get("/notifications.html", response_class=FileResponse)
async def serve_notifications_html():
    return serve_file(os.path.join(frontend_dir, "notifications.html"))

@app.get("/help.html", response_class=FileResponse)
async def serve_help_html():
    return serve_file(os.path.join(frontend_dir, "help.html"))

# --- API Endpoints for Expert Q&A ---
BASE_API_PATH = "/api"

@app.get(f"{BASE_API_PATH}/questions/popular", response_model=List[QuestionOut])
async def get_popular_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.likes.desc(), Question.created_at.desc()).all()
    return questions

@app.post(f"{BASE_API_PATH}/questions", response_model=QuestionOut)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    logged_in_user_id = os.environ.get("LOGGED_IN_USER_ID")
    user_id = int(logged_in_user_id) if logged_in_user_id else 1 # Default to 1 if not available
    db_question = Question(question_text=question.question_text, user_id=user_id)
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

@app.get(f"{BASE_API_PATH}/users/{{username}}", response_model=UserResponse)
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/alumni/top-liked", response_model=Dict[str, List[AlumniResponse]])
async def get_top_liked_alumni(db: Session = Depends(get_db)):
    """
    Retrieves the top 5 liked alumni, grouped by department. Handles cases where a department might have fewer than 5 alumni.
    """
    try:
        # Query the top 5 liked alumni overall
        top_alumni = db.query(User).order_by(desc(User.likes)).limit(5).all()

        # Group the alumni by department
        grouped_alumni: Dict[str, List[AlumniResponse]] = {}
        for alumni in top_alumni:
            if alumni.department:   # Only process alumni with a department
                if alumni.department not in grouped_alumni:
                    grouped_alumni[alumni.department] = []

                #  Create an instance of AlumniResponse from the SQLAlchemy User object
                alumni_response = AlumniResponse(
                    id=alumni.id,
                    name=alumni.name,
                    profession=alumni.profession,
                    department=alumni.department,
                    likes=alumni.likes,
                    # Populate other fields from the User model
                )
                grouped_alumni[alumni.department].append(alumni_response)

        return grouped_alumni

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
    # Use the relationship to find connected users
    connected_users = [conn.connected_user for conn in user.connections]
    return connected_users

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
    user.connections.append(UserConnection(connected_user=suggestion_user))
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
    logged_in_user_id = os.environ.get("LOGGED_IN_USER_ID")
    user = f"User-{logged_in_user_id}" if logged_in_user_id else "Anonymous"
    if "question" in data.text.lower():
        new_question = DailySparkQuestion(question=data.text)
        db.add(new_question)
    else:
        today_question = db.query(DailySparkQuestion).order_by(DailySparkQuestion.created_at.desc()).first()
        if not today_question:
            raise HTTPException(status_code=404, detail="Today's question not found")
        new_answer = DailySparkAnswer(question_id=today_question.id, text=data.text, user=user)
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

# --- New API Endpoints for Hackathons, Feed, and Jobs ---

@app.get("/api/todays-feed", response_model=DailySparkQuestionOut)
async def get_todays_question_feed(db: Session = Depends(get_db)):
    """
    Retrieve today's Daily Spark question for the feed.
    """
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


@app.get(f"{BASE_API_PATH}/events", response_model=List[dict])
async def get_todays_feed_events(db: Session = Depends(get_db)):
    #  "Today's feed" is subjective.  Here's a basic approach:
    #  1.  Recent Internships
    #  2.  Recent Hackathons
    #  3.  Recent Job Postings
    #  Combine and sort by date.

    internships = db.query(Internship).filter(Internship.start_date <= date.today()).order_by(desc(Internship.start_date)).limit(2).all()
    hackathons = db.query(Hackathon).filter(Hackathon.date <= date.today()).order_by(desc(Hackathon.date)).limit(2).all()
    jobs = db.query(Job).order_by(desc(Job.date_posted)).limit(2).all()

    feed_items = [
        {"type": "internship", "data": internship, "date": internship.start_date} for internship in internships
    ] + [
        {"type": "hackathon", "data": hackathon, "date": hackathon.date} for hackathon in hackathons
    ] + [
        {"type": "job", "data": job, "date": job.date_posted} for job in jobs
    ]

    feed_items.sort(key=lambda item: item["date"], reverse=True)  # Sort by date

    # Convert to a list of dictionaries
    feed_list = []
    for item in feed_items:
        item_dict = {"type": item["type"]}
        if item["type"] == "internship":
            item_dict["data"] = {
                "id": item["data"].id,
                "title": item["data"].title,
                "company": item["data"].company,
                "start_date": item["data"].start_date,
                "end_date": item["data"].end_date,
                "description": item["data"].description,
            }
        elif item["type"] == "hackathon":
             item_dict["data"] = {
                "id": item["data"].id,
                "name": item["data"].name,
                "date": item["data"].date,
                "location": item["data"].location,
                "description": item["data"].description,
                "theme": item["data"].theme,
                "prize_pool": item["data"].prize_pool
            }
        elif item["type"] == "job":
            item_dict["data"] = {
                "id": item["data"].id,
                "title": item["data"].title,
                "company": item["data"].company,
                "location": item["data"].location,
                "description": item["data"].description,
                "salary": item["data"].salary,
                "date_posted": item["data"].date_posted,
                "type": item["data"].type,
                "experience": item["data"].experience,
                "imageUrl": item["data"].imageUrl
            }
        feed_list.append(item_dict)
    return feed_list


@app.get("/api/features", response_model=List[FeatureOut])
async def get_features_list(db: Session = Depends(get_db)):
    """
    Retrieve all features.
    """
    features = db.query(Feature).all()
    return features

@app.get("/api/search", response_model=List[SearchResult])
async def search_resources(term: str, db: Session = Depends(get_db)):
    """
    Search for resources (users, events, jobs, etc.) based on a term.
    """
    # Implement your search logic here. This is a placeholder.
    # You'll need to query your database tables (users, CareerFair, Hackathon, Job)
    # and combine the results. For simplicity, this example only searches users.

    users = db.query(User).filter(User.name.ilike(f"%{term}%")).all()
    career_fairs = db.query(CareerFair).filter(CareerFair.name.ilike(f"%{term}%")).all()
    hackathons = db.query(Hackathon).filter(Hackathon.name.ilike(f"%{term}%")).all()
    jobs = db.query(Job).filter(Job.title.ilike(f"%{term}%")).all()

    # Combine results and convert to the SearchResult model
    results = [SearchResult(name=user.name) for user in users]
    results.extend([SearchResult(name=fair.name) for fair in career_fairs])
    results.extend([SearchResult(name=hack.name) for hack in hackathons])
    results.extend([SearchResult(name=job.title) for job in jobs])
    return results

@app.get(f"{BASE_API_PATH}/users/{{username}}/notifications", response_model=List[NotificationOut])
async def get_user_notifications_list(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notifications = db.query(Notification).filter(Notification.user_id == user.id).order_by(desc(Notification.created_at)).all()
    return notifications

@app.post(f"{BASE_API_PATH}/notifications/mark-read")
async def mark_notifications_as_read(notification_data: NotificationMarkRead, db: Session = Depends(get_db)):
    for notification_id in notification_data.notification_ids:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = 1   # Assuming 1 represents True in your DB
    db.commit()
    return {"message": "Notifications marked as read"}

@app.post("/api/search-history")
async def save_user_search_history(
    search_term: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda db: get_current_user(db)) # Simplified dependency
):
    """
    Save a search term to the user's search history.
    """
    if current_user:
        db_search_history = SearchHistory(user_id=str(current_user.id), search_term=search_term)
        db.add(db_search_history)
        db.commit()
        db.refresh(db_search_history)
        return {"message": "Search term saved"}
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/api/search-history", response_model=List[SearchHistoryItem])
async def get_user_search_history(db: Session = Depends(get_db), current_user: Optional[User] = Depends(lambda db: get_current_user(db))):
    """
    Retrieve the search history for the current user.
    """
    if current_user:
        history = db.query(SearchHistory).filter(SearchHistory.user_id == str(current_user.id)).order_by(SearchHistory.timestamp.desc()).all()
        return history
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

async def get_current_user(db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        # --- Placeholder for Token Verification ---
        # In a real application, you would verify the token against your authentication system.
        # For this example, we'll just try to find a user with the token as their ID.
        logged_in_user_id_str = os.environ.get("LOGGED_IN_USER_ID")
        if logged_in_user_id_str:
            try:
                user = db.query(User).filter(User.id == int(logged_in_user_id_str)).first()
                return user
            except ValueError:
                return None
            except Exception as e:
                logger.error(f"Error during fake token verification: {e}")
                return None
    return None

@app.post(f"{BASE_API_PATH}/help/submit-issue", response_model=UserIssueResponse)
async def submit_user_issue_report(issue: UserIssueCreate, db: Session = Depends(get_db), current_user: Optional[User] = Depends(lambda db: get_current_user(db))):
    user_id = current_user.id if current_user else None
    db_issue = UserIssue(
        user_id=user_id,
        name=issue.name,
        email=issue.email,
        message=issue.message
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue


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
    config = uvicorn.Config("exp:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())