# -*- coding: utf-8 -*-
import os
import asyncio
import uvicorn
import sqlite3
import uuid
import secrets
import random
import smtplib
import logging
from email.mime.text import MIMEText
from urllib.parse import urlencode
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Annotated

from fastapi import FastAPI, HTTPException, Depends, Header, Body, Request, Form, Response
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.sqlite import DATE as SQLiteDATE # Keep if specific SQLite date handling needed
# Import create_engine explicitly if not already
from sqlalchemy import create_engine


from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# --- Configure logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) # Use __name__ for logger name

# --- FastAPI App ---
app = FastAPI()

# --- Configuration (Move sensitive data to environment variables/secrets management) ---
# Use absolute paths for reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'explore.db')}"
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend-exp") # Assumes frontend is one level up
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

logger.info(f"Database URL: {DATABASE_URL}")
logger.info(f"Frontend Directory: {FRONTEND_DIR}")
logger.info(f"Static Directory: {STATIC_DIR}")

# --- Email Configuration (Use Environment Variables) ---
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com") # Replace with your actual server if not Gmail
MAIL_PORT = int(os.environ.get("MAIL_PORT", 465)) # Use 587 for TLS, 465 for SSL
MAIL_USERNAME = os.environ.get("MAIL_USERNAME") # MUST BE SET
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") # MUST BE SET
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME) # Defaults to username

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # name = Column(String, nullable=True) # REMOVED: To match DB state causing 'no such column' error
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False) # Stores the bcrypt hash
    is_student = Column(Boolean, default=True)
    is_alumni = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    activity_score = Column(Integer, default=0)
    achievements = Column(Text, nullable=True)
    alumni_gems = Column(Integer, default=0)
    department = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    alma_mater = Column(String, nullable=True)
    interviews = Column(Text, nullable=True)
    internships = Column(Text, nullable=True)
    startups = Column(Text, nullable=True)
    current_company = Column(String, nullable=True)
    milestones = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    likes = Column(Integer, default=0)
    badges = Column(Integer, default=0)
    solved = Column(Integer, default=0)
    links = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) # Use database time

    connections = relationship("UserConnection", foreign_keys="[UserConnection.user_id]", back_populates="user")
    connected_users = relationship("UserConnection", foreign_keys="[UserConnection.connected_user_id]", back_populates="connected_user")
    questions = relationship("Question", back_populates="user")
    issues = relationship("UserIssue", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    applied_hackathons = relationship("AppliedHackathon", back_populates="user")

class UserConnection(Base):
    __tablename__ = "user_connections"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    connected_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user = relationship("User", foreign_keys=[user_id], back_populates="connections")
    connected_user = relationship("User", foreign_keys=[connected_user_id], back_populates="connected_users")

class CareerFair(Base):
    __tablename__ = "career_fairs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Internship(Base):
    __tablename__ = "internships"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Hackathon(Base):
    __tablename__ = "hackathons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    theme = Column(String, nullable=True)
    prize_pool = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    applications = relationship("AppliedHackathon", back_populates="hackathon")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    question_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="questions")

class ChatContact(Base):
    __tablename__ = "chat_contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    messages = relationship("ChatMessage", back_populates="contact")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("chat_contacts.id"))
    sender = Column(String, nullable=True)
    text = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    contact = relationship("ChatContact", back_populates="messages")

class DailySparkQuestion(Base):
    __tablename__ = "daily_spark_questions"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    answers = relationship("DailySparkAnswer", back_populates="question")

class DailySparkAnswer(Base):
    __tablename__ = "daily_spark_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("daily_spark_questions.id"))
    user = Column(String) # Consider linking to User ID
    text = Column(Text, nullable=False)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    question = relationship("DailySparkQuestion", back_populates="answers")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    salary = Column(String, nullable=True)
    date_posted = Column(Date, nullable=True)
    type = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_term = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # user = relationship("User") # Optional

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="notifications")

class AppliedHackathon(Base):
    __tablename__ = "applied_hackathons"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    hackathon_id = Column(Integer, ForeignKey("hackathons.id"), primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="applied_hackathons")
    hackathon = relationship("Hackathon", back_populates="applications")

class UserIssue(Base):
    __tablename__ = "user_issues"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False) # Reporter name
    email = Column(String, nullable=False) # Reporter email
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="issues")

# --- Create Tables ---
# This command ensures tables exist. It does NOT modify existing tables (like adding the 'name' column).
# If the database schema changes significantly, use migrations (e.g., Alembic).
Base.metadata.create_all(bind=engine)
logger.info("Database tables checked/created.")

# --- Dependency ---
def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Password Utils ---
# --- Password Utils (Secure) ---
# Restore or add these functions:
def hash_password(password: str) -> str:
    """Hashes a password using the configured context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    if not plain_password or not hashed_password:
        logger.debug("Verify password called with empty plain or hashed password.")
        return False
    try:
        # Check if the hash is in a recognized format
        if not pwd_context.identify(hashed_password):
             logger.warning(f"Attempted to verify password with unrecognized hash format: {hashed_password[:10]}...")
             # CRITICAL: If the format is unknown, verification MUST fail.
             return False
        # If format is recognized, proceed with verification
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # This might be redundant due to the identify check, but safe to keep
        logger.warning(f"Verification failed due to UnknownHashError for hash: {hashed_password[:10]}...")
        return False
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False # Fail verification on any unexpected error
    
# --- OTP Storage (Simple In-Memory) ---
# NOTE: This is lost on server restart. Use Redis or DB for persistence.
otp_storage: Dict[str, Dict[str, str | datetime]] = {}

# --- Pydantic Models ---
# (Kept concise, assuming definitions from previous steps are correct and match DB without 'name')

class OrmConfig:
    from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8: raise ValueError("Password must be at least 8 characters long")
        return value

class UserUpdate(BaseModel):
    alma_mater: Optional[str] = None
    profession: Optional[str] = None
    department: Optional[str] = None
    achievements: Optional[str] = None
    interviews: Optional[str] = None
    internships: Optional[str] = None
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    model_config = ConfigDict(extra='ignore') # Ignore extra fields

class UserResponse(UserBase):
    id: int
    is_student: bool
    is_alumni: bool
    is_admin: bool
    activity_score: int
    achievements: Optional[str] = None
    alumni_gems: int
    department: Optional[str] = None
    profession: Optional[str] = None
    alma_mater: Optional[str] = None
    interviews: Optional[str] = None
    internships: Optional[str] = None
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    likes: int
    badges: int
    solved: int
    links: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AlumniResponse(BaseModel):
    id: int
    username: str
    profession: Optional[str] = None
    alma_mater: Optional[str] = None
    department: Optional[str] = None
    likes: int
    interviews: Optional[str] = None
    internships: Optional[str] = None
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DailySparkAnswerOut(BaseModel):
    id: int
    user: str
    text: str
    votes: int
    model_config = ConfigDict(from_attributes=True)

class DailySparkQuestionOut(BaseModel):
    id: int
    company: Optional[str] = None
    role: Optional[str] = None
    question: str
    answers: List[DailySparkAnswerOut] = []
    model_config = ConfigDict(from_attributes=True)

class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    salary: Optional[str] = None
    date_posted: Optional[date] = None
    type: Optional[str] = None
    experience: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None

class JobCreate(JobBase): pass

class JobOut(JobBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class HackathonBase(BaseModel):
    name: str
    date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    prize_pool: Optional[str] = None
    url: Optional[str] = None

class HackathonCreate(HackathonBase): pass

class HackathonOut(HackathonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InternshipBase(BaseModel):
    title: str
    company: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    url: Optional[str] = None

class InternshipCreate(InternshipBase): pass

class InternshipOut(InternshipBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CareerFairBase(BaseModel):
    name: str
    date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

class CareerFairCreate(CareerFairBase): pass

class CareerFairOut(CareerFairBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class QuestionCreate(BaseModel):
    question_text: str

class QuestionOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    question_text: str
    created_at: datetime
    likes: int
    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(BaseModel):
    contact_id: int
    text: Optional[str] = None
    file_path: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: int
    contact_id: int
    sender: Optional[str] = None
    text: Optional[str] = None
    file_path: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatContactOut(BaseModel):
    id: int
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DailySparkSubmit(BaseModel):
    text: str

class SearchResult(BaseModel):
    type: str
    id: int
    name: str
    url: Optional[str] = None

class SearchHistoryItem(BaseModel):
    id: int
    user_id: int
    search_term: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class Event(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date: Optional[date] = None
    location: Optional[str] = None
    url: Optional[str] = None
    type: str
    model_config = ConfigDict(from_attributes=True)

class FeatureOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class NotificationOut(BaseModel):
    id: int
    message: str
    type: str
    related_id: Optional[int] = None
    created_at: datetime
    is_read: bool
    model_config = ConfigDict(from_attributes=True)

class NotificationMarkRead(BaseModel):
    notification_ids: List[int]

class UserIssueCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class UserIssueResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    email: str
    message: str
    submitted_at: datetime
    status: str
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str
    @field_validator("new_password")
    def validate_password(cls, value):
        if len(value) < 8: raise ValueError("Password must be at least 8 characters long")
        return value

# -*- coding: utf-8 -*-
import os
import asyncio
import uvicorn
import sqlite3
import uuid
import secrets
import random
import smtplib
import logging
from email.mime.text import MIMEText
from urllib.parse import urlencode
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Annotated

from fastapi import FastAPI, HTTPException, Depends, Header, Body, Request, Form, Response
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, Session, relationship # Keep Session for type hints
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.sqlite import DATE as SQLiteDATE
# Import create_engine explicitly
from sqlalchemy import create_engine

# Assuming models are defined elsewhere (e.g., models.py)
# from .models import Base, User, Job, Hackathon, ... # Example import
# Assuming schemas are defined elsewhere (e.g., schemas.py)
# from .schemas import UserCreate, UserResponse, JobOut, ... # Example import

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# --- Configure logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) # Use __name__ for logger name

# --- FastAPI App ---
app = FastAPI()

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'explore.db')}"
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend-exp")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

logger.info(f"Database URL: {DATABASE_URL}")
logger.info(f"Frontend Directory: {FRONTEND_DIR}")
logger.info(f"Static Directory: {STATIC_DIR}")

# --- Email Configuration ---
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base and Models are assumed to be defined elsewhere ---
# Base = declarative_base() # Definition excluded
# class User(Base): ... # Definition excluded
# class Job(Base): ... # Definition excluded
# ... etc.

# --- Create Tables ---
# You would typically call this after importing Base and defining/importing models
# Base.metadata.create_all(bind=engine)
# logger.info("Database tables checked/created.") # Keep log message if create_all is called

# --- Dependency ---
def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Password Utils ---
def hash_password(password: str) -> str:
    """Hashes a password using the configured context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    if not plain_password or not hashed_password:
        logger.debug("Verify password called with empty plain or hashed password.")
        return False
    try:
        if not pwd_context.identify(hashed_password):
             logger.warning(f"Attempted to verify password with unrecognized hash format: {hashed_password[:10]}...")
             return False
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        logger.warning(f"Verification failed due to UnknownHashError for hash: {hashed_password[:10]}...")
        return False
    except Exception as e:
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False

# --- OTP Storage (Simple In-Memory) ---
otp_storage: Dict[str, Dict[str, str | datetime]] = {}

# --- Pydantic Models are assumed to be defined elsewhere ---
# class UserCreate(BaseModel): ... # Definition excluded
# class UserResponse(BaseModel): ... # Definition excluded
# ... etc.

# --- Pydantic Models ---
# ... (all your class definitions like UserResponse, AlumniResponse, etc.)

# --- Explicitly update forward references ---
# Add these lines:
UserResponse.model_rebuild()
AlumniResponse.model_rebuild()
DailySparkAnswerOut.model_rebuild()
DailySparkQuestionOut.model_rebuild() # Depends on DailySparkAnswerOut
JobOut.model_rebuild()
HackathonOut.model_rebuild()
InternshipOut.model_rebuild()
CareerFairOut.model_rebuild()
QuestionOut.model_rebuild()
ChatMessageOut.model_rebuild()
ChatContactOut.model_rebuild()
SearchResult.model_rebuild()
SearchHistoryItem.model_rebuild()
Event.model_rebuild()
FeatureOut.model_rebuild()
NotificationOut.model_rebuild()
UserIssueResponse.model_rebuild()
# Add any other Pydantic models used as response_models or nested within them

logger.info("Pydantic models rebuilt.")

# --- Frontend Serving Setup ---
# ... (rest of your code starting from here)

# --- Frontend Serving Setup ---
if not os.path.exists(FRONTEND_DIR):
     logger.error(f"Frontend directory not found: {FRONTEND_DIR}")
templates = Jinja2Templates(directory=FRONTEND_DIR if os.path.exists(FRONTEND_DIR) else ".")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}. Static files will not be served.")

# --- Authentication Dependencies ---
security = HTTPBasic()
security_optional = HTTPBasic(auto_error=False)

# NOTE: The 'User' type hint below relies on the User model being defined/imported
def get_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)], db: Session = Depends(get_db)) -> 'User': # Use forward reference if needed
    """
    Authenticates user based on HTTP Basic Auth.
    Raises 401 if invalid/missing credentials.
    """
    # This query relies on the User model being defined/imported
    user = db.query(User).filter( # Replace 'User' with actual imported model name
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    if not verify_password(credentials.password, user.hashed_password):
        logger.debug(f"API Auth failed: Incorrect password for user '{credentials.username}'. Hash check failed.")
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    logger.info(f"API Auth successful for user '{user.username}'.")
    return user

# NOTE: The 'User' type hint below relies on the User model being defined/imported
async def get_optional_current_user(credentials: Annotated[Optional[HTTPBasicCredentials], Depends(security_optional)], db: Session = Depends(get_db)) -> Optional['User']: # Use forward reference if needed
    """
    Tries Basic Auth if provided, returns None if missing/invalid.
    """
    if credentials is None:
        return None

    # This query relies on the User model being defined/imported
    user = db.query(User).filter( # Replace 'User' with actual imported model name
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        return None
    logger.info(f"(Optional API Auth) User '{user.username}' authenticated.") 
    return user

# --- Utility Functions ---
def serve_file(file_path: str):
    """Safely serves a file from the FRONTEND directory if it exists."""
    abs_file_path = os.path.join(FRONTEND_DIR, file_path)
    logger.info(f"Attempting to serve file: {abs_file_path}")
    if os.path.exists(abs_file_path) and os.path.isfile(abs_file_path):
        return FileResponse(abs_file_path)
    else:
        logger.error(f"File not found: {abs_file_path}")
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")

async def send_otp_email(email: str, otp: str):
    """Sends OTP email using configured settings."""
    if not all([MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER]):
        logger.error("Email configuration incomplete. Cannot send OTP.")
        return False
    try:
        message = MIMEText(f'Your OTP for password reset is: {otp}\nThis OTP is valid for 5 minutes.')
        message['Subject'] = 'Password Reset OTP'
        message['From'] = MAIL_DEFAULT_SENDER
        message['To'] = email

        mail_port_int = int(MAIL_PORT)

        if mail_port_int == 465: # SSL
             with smtplib.SMTP_SSL(MAIL_SERVER, mail_port_int) as server:
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.send_message(message)
        elif mail_port_int == 587: # TLS
             with smtplib.SMTP(MAIL_SERVER, mail_port_int) as server:
                server.starttls()
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.send_message(message)
        else:
            logger.error(f"Unsupported MAIL_PORT: {MAIL_PORT}. Use 465 (SSL) or 587 (TLS).")
            return False

        logger.info(f"OTP email sent successfully to {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP Authentication Error for user {MAIL_USERNAME}. Check credentials/app password settings.")
        return False
    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {e}", exc_info=True)
        return False

# --- Notification Creation Functions ---
# NOTE: These functions rely on Notification, User, Hackathon, Job, Internship models being defined/imported
def create_notification(db: Session, user_id: int, message: str, type: str, related_id: Optional[int] = None):
    """Adds a notification to the session (does not commit)."""
    # Assumes 'Notification' model is imported/defined
    notification = Notification(user_id=user_id, message=message, type=type, related_id=related_id)
    db.add(notification)

def create_new_hackathon_notifications(db: Session, hackathon: 'Hackathon'): # Use forward reference if needed
    """Adds notifications for all non-admin users about a new hackathon (does not commit)."""
    # Assumes 'User' and 'Hackathon' models are imported/defined
    users = db.query(User).filter(User.is_admin == False).all()
    for user in users:
        create_notification(db, user.id, f"New Hackathon Alert: '{hackathon.name}' is now available!", "new_hackathon", hackathon.id)
    logger.info(f"Prepared notifications for new hackathon '{hackathon.name}'.")

def create_new_job_notifications(db: Session, job: 'Job'): # Use forward reference if needed
    """Adds notifications for all non-admin users about a new job (does not commit)."""
    # Assumes 'User' and 'Job' models are imported/defined
    users = db.query(User).filter(User.is_admin == False).all()
    for user in users:
        create_notification(db, user.id, f"New Job Alert: '{job.title}' at {job.company or 'Unknown Company'}!", "new_job", job.id)
    logger.info(f"Prepared notifications for new job '{job.title}'.")

def create_new_internship_notifications(db: Session, internship: 'Internship'): # Use forward reference if needed
    """Adds notifications for all non-admin users about a new internship (does not commit)."""
    # Assumes 'User' and 'Internship' models are imported/defined
    users = db.query(User).filter(User.is_admin == False).all()
    for user in users:
        create_notification(db, user.id, f"New Internship Opportunity: '{internship.title}' at {internship.company or 'Unknown Company'}!", "new_internship", internship.id)
    logger.info(f"Prepared notifications for new internship '{internship.title}'.")


# --- Core API Routes ---

# --- Authentication and Static Pages ---
@app.get("/", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def serve_login_html(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Serves the main login page."""
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "message": message})

@app.post("/login", response_class=HTMLResponse, tags=["Auth"])
async def login(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    """Handles login via HTML form submission."""
    logger.info(f"Login attempt for username/email: '{username}'")
    # Assumes 'User' model is imported/defined
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    login_error = None
    if not user or not verify_password(password, user.hashed_password):
        login_error = "Incorrect username or password."
        logger.warning(f"Login failed for '{username}'.")

    if login_error:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": login_error},
            status_code=401
        )

    logger.info(f"User '{user.username}' logged in successfully (ID: {user.id}).")
    session_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=1800
    )
    query_params = urlencode({"username": user.username})
    return RedirectResponse(url=f"/home?{query_params}", status_code=303)


@app.get("/home", response_class=HTMLResponse, tags=["Pages"])
async def home(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
    current_user: 'User' = Depends(get_current_user) # Assumes 'User' is imported/defined
    ):
    """Serves the home page for the logged-in user."""
    if current_user.username != username:
         logger.warning(f"Auth mismatch: User '{current_user.username}' tried to access home for '{username}'. Redirecting.")
         query_params = urlencode({"username": current_user.username})
         return RedirectResponse(url=f"/home?{query_params}", status_code=303)

    logger.info(f"Serving home page for user '{username}' (ID: {current_user.id})")
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": current_user.id,
        "username": current_user.username,
        "user_name": current_user.username
    })

@app.get("/register", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def register_page(request: Request, error: Optional[str] = None):
    """Serves the registration page."""
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register", response_class=HTMLResponse, tags=["Auth"])
async def register(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()], # Assuming EmailStr is imported from Pydantic
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    """Handles new user registration via HTML form."""
    logger.info(f"Registration attempt for username: {username}, email: {email}")
    # Assumes 'User' model is imported/defined
    db_user_username = db.query(User).filter(User.username == username).first()
    db_user_email = db.query(User).filter(User.email == email).first()

    error = None
    if db_user_username:
        error = "Username already registered"
    elif db_user_email:
        error = "Email already registered"
    elif len(password) < 8:
         error = "Password must be at least 8 characters long"

    if error:
        logger.warning(f"Registration failed for '{username}': {error}")
        return templates.TemplateResponse("register.html", {"request": request, "error": error}, status_code=400)

    try:
        hashed_password = hash_password(password) # Secure hash
        new_user = User(
        username=username, email=email,
        hashed_password=hashed_password, # Storing hash
        created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User '{username}' (ID: {new_user.id}) registered successfully.")
        query_params = urlencode({"message": "Registration successful. Please log in."})
        return RedirectResponse(url=f"/?{query_params}", status_code=303)
    except Exception as e:
        db.rollback()
        logger.error(f"Registration DB error for user '{username}': {e}", exc_info=True)
        return templates.TemplateResponse("register.html", {"request": request, "error": "Registration failed due to a server error."}, status_code=500)


# --- Password Reset Flow ---
@app.get("/forgot-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def forgot_password_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Serves the forgot password page."""
    return templates.TemplateResponse("forgetpass.html", {"request": request, "error": error, "message": message})

@app.post("/forgot-password", response_class=HTMLResponse, tags=["Auth"])
async def forgot_password(request: Request, email: Annotated[str, Form()], db: Session = Depends(get_db)): # Assuming EmailStr is imported
    """Handles the initial forgot password request."""
    logger.info(f"Forgot password request received for email: {email}")
    # Assumes 'User' model is imported/defined
    user = db.query(User).filter(User.email == email).first()
    message_to_show = "If an account exists for this email, an OTP has been sent."

    if user:
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.now() + timedelta(minutes=5)
        otp_storage[email] = {"otp": otp, "expiry": otp_expiry}
        logger.info(f"Generated OTP {otp} for email {email}, valid until {otp_expiry}")

        if await send_otp_email(email, otp):
            logger.info(f"OTP email initiated successfully for {email}.")
            query_params = urlencode({"email": email})
            return RedirectResponse(url=f"/verify-otp?{query_params}", status_code=303)
        else:
            logger.error(f"Failed to send OTP email to {email}. User will see generic message.")
            if email in otp_storage: del otp_storage[email]
            message_to_show = "Error sending OTP. Please try again later."
    else:
         logger.warning(f"Forgot password request for non-existent email: {email}")

    return templates.TemplateResponse("forgetpass.html", {"request": request, "message": message_to_show})


@app.get("/verify-otp", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def verify_otp_page(request: Request, email: str, error: Optional[str] = None):
    """Serves the OTP verification page."""
    if not email:
        raise HTTPException(status_code=400, detail="Email parameter is missing.")
    return templates.TemplateResponse("otp.html", {"request": request, "email": email, "error": error})

@app.post("/verify-otp", response_class=HTMLResponse, tags=["Auth"])
async def verify_otp(request: Request, email: Annotated[str, Form(...)], otp_attempt: Annotated[str, Form(...)]):
    """Verifies the submitted OTP."""
    logger.info(f"OTP verification attempt for email: {email} with OTP: '{otp_attempt}'")
    stored_otp_data = otp_storage.get(email)
    error_message = None

    if not stored_otp_data:
        error_message = "Invalid or expired OTP. Please request a new one."
    elif datetime.now() > stored_otp_data["expiry"]:
        error_message = "OTP has expired. Please request a new one."
        del otp_storage[email]
    elif otp_attempt != stored_otp_data["otp"]:
        error_message = "Invalid OTP entered."

    if error_message:
        logger.warning(f"OTP verification failed for {email}: {error_message}")
        return templates.TemplateResponse("otp.html", {"request": request, "email": email, "error": error_message})
    else:
        logger.info(f"OTP verification successful for email {email}.")
        del otp_storage[email]
        query_params = urlencode({"email": email})
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=303)


@app.get("/reset-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def reset_password_page(request: Request, email: str, error: Optional[str] = None):
    """Serves the final password reset page."""
    if not email:
        raise HTTPException(status_code=400, detail="Email parameter is missing.")
    return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": error})

@app.post("/reset-password", response_class=HTMLResponse, tags=["Auth"])
async def reset_password(
    request: Request,
    email: Annotated[str, Form(...)], # Assuming EmailStr is imported
    new_password: Annotated[str, Form(...)],
    db: Session = Depends(get_db)
):
    """Handles the final password reset submission."""
    logger.info(f"Password reset submission received for email: {email}")
    if len(new_password) < 8:
         logger.warning(f"Password reset failed for {email}: Password too short.")
         return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": "Password must be at least 8 characters long."})

    # Assumes 'User' model is imported/defined
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.error(f"Password reset failed: User with email {email} not found during final reset step.")
        return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": "User not found. Please start the password reset process again."})

    try:
        hashed_password = hash_password(new_password) # Secure hash
        user.hashed_password = hashed_password
        user.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Password successfully reset for user '{user.username}' (Email: {email}).")
        query_params = urlencode({"message": "Password reset successfully. Please log in with your new password."})
        return RedirectResponse(url=f"/?{query_params}", status_code=303)
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset DB error for {email}: {e}", exc_info=True)
        return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": "Failed to reset password due to a server error."})


# --- Other HTML Page Serving Routes ---
@app.get("/dailyspark.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_daily_spark(request: Request): return templates.TemplateResponse("dailyspark.html", {"request": request})
@app.get("/explore.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_explore(request: Request): return templates.TemplateResponse("explore.html", {"request": request})
@app.get("/career-fairs.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_career_fairs_html(request: Request): return templates.TemplateResponse("career-fairs.html", {"request": request})
@app.get("/expertqa.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_expertqa_html(request: Request): return templates.TemplateResponse("expertqa.html", {"request": request})
@app.get("/explore-hackathons.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_explore_hackathon_html(request: Request): return templates.TemplateResponse("explore-hackathons.html", {"request": request})
@app.get("/intership.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_internship_html(request: Request): return templates.TemplateResponse("intership.html", {"request": request})
@app.get("/leader-profile.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_leader_profile_html(request: Request): return templates.TemplateResponse("leader-profile.html", {"request": request})
@app.get("/leaderboard.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_leaderboard_html(request: Request): return templates.TemplateResponse("leaderboard.html", {"request": request})
@app.get("/alumni-roadmaps.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_alumni_roadmap_html(request: Request): return templates.TemplateResponse("alumni-roadmaps.html", {"request": request})
@app.get("/chat.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_chat_html(request: Request): return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/profile.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_profile(request: Request, username: str, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Serves the profile page for a given username, requires authentication."""
    # Assumes 'User' model is imported/defined
    user_to_view = db.query(User).filter(User.username == username).first()
    if not user_to_view:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Serving profile page for user '{username}' (ID: {user_to_view.id}) requested by '{current_user.username}'")
    # Assumes 'UserResponse' schema is imported/defined
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile_user_id": user_to_view.id,
        "profile_username": user_to_view.username,
        "profile_user_name": user_to_view.username,
        "is_own_profile": current_user.id == user_to_view.id,
        "profile_data": UserResponse.model_validate(user_to_view)
    })

@app.get("/connections.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_connections(request: Request): return templates.TemplateResponse("connections.html", {"request": request})
@app.get("/notifications.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_notifications_html(request: Request): return templates.TemplateResponse("notifications.html", {"request": request})
@app.get("/help.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_help_html(request: Request): return templates.TemplateResponse("help.html", {"request": request})

# --- API Endpoints ---
BASE_API_PATH = "/api"

# --- User API ---
# Assumes 'UserResponse' schema is imported/defined
@app.get(f"{BASE_API_PATH}/users/me", response_model='UserResponse', tags=["Users"]) # Use forward reference if needed
async def read_users_me(current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Gets the profile data for the currently authenticated user (via API Auth)."""
    logger.info(f"API request for /users/me by user '{current_user.username}'")
    return current_user

# Assumes 'UserResponse' schema is imported/defined
@app.get(f"{BASE_API_PATH}/users/{{username}}", response_model='UserResponse', tags=["Users"]) # Use forward reference if needed
async def read_user_profile(username: str, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Gets the public profile of a specific user by username (requires API auth)."""
    logger.info(f"API request for profile of '{username}' by user '{current_user.username}'")
    # Assumes 'User' model is imported/defined
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Assumes 'UserUpdate' schema and 'UserResponse' schema are imported/defined
@app.put(f"{BASE_API_PATH}/users/me", response_model='UserResponse', tags=["Users"]) # Use forward reference if needed
async def update_user_profile(user_update: 'UserUpdate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'UserUpdate' and 'User' are imported
    """Updates the profile of the currently authenticated user (via API Auth)."""
    logger.info(f"API request to update profile for user '{current_user.username}'")
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated_fields_count = 0
    for key, value in update_data.items():
        if hasattr(current_user, key):
            setattr(current_user, key, value)
            updated_fields_count += 1
        else:
            logger.warning(f"Attempted to update non-existent attribute '{key}' for user '{current_user.username}'")

    if updated_fields_count == 0:
         raise HTTPException(status_code=400, detail="No valid fields provided for update")

    try:
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        logger.info(f"Profile updated successfully for user '{current_user.username}'")
        return current_user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile DB error for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update profile")
    
# Add this route definition with others in exp.py
@app.get(f"{BASE_API_PATH}/contacts", response_model=List[ChatContactOut], tags=["Chat"])
async def get_chat_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # NOTE: Fetches ALL contacts. Add filtering if needed.
    logger.info(f"API request by '{current_user.username}' for chat contacts.")
    contacts = db.query(ChatContact).all() # Assumes ChatContact model exists
    return contacts

# Assumes 'AlumniResponse' schema is imported/defined
@app.get(f"{BASE_API_PATH}/leaderboard", response_model=List['AlumniResponse'], tags=["Users", "Alumni"]) # Use forward reference if needed
async def get_leaderboard(db: Session = Depends(get_db)):
    """Retrieves the user leaderboard based on activity score and gems."""
    # Assumes 'User' model is imported/defined
    users = db.query(User)\
        .filter(User.is_alumni == True)\
        .order_by(User.activity_score.desc(), User.alumni_gems.desc())\
        .limit(100) \
        .all()
    # Assumes 'AlumniResponse' schema is imported/defined
    leaderboard_data = [AlumniResponse.model_validate(user) for user in users]
    return leaderboard_data

# --- Alumni API ---
# Assumes 'AlumniResponse' schema is imported/defined
@app.get(f"{BASE_API_PATH}/alumni/top-liked", response_model=Dict[str, List['AlumniResponse']], tags=["Alumni"]) # Use forward reference if needed
async def get_top_liked_alumni(limit: int = 5, db: Session = Depends(get_db)):
    """Gets the top N liked alumni, grouped by department."""
    try:
        # Assumes 'User' model is imported/defined
        top_alumni = db.query(User)\
            .filter(User.is_alumni == True)\
            .order_by(desc(User.likes))\
            .limit(limit)\
            .all()

        grouped_alumni: Dict[str, List['AlumniResponse']] = {} # Use forward reference if needed
        for alumni in top_alumni:
            department_key = alumni.department or "Unknown Department"
            if department_key not in grouped_alumni:
                grouped_alumni[department_key] = []
            # Assumes 'AlumniResponse' schema is imported/defined
            alumni_response = AlumniResponse.model_validate(alumni)
            grouped_alumni[department_key].append(alumni_response)

        return grouped_alumni
    except Exception as e:
        logger.error(f"Error fetching top liked alumni: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching alumni data")

# Add near other Alumni API endpoints in exp.py
# --- Alumni API --- (Add these two endpoints)

# Assumes BASE_API_PATH, AlumniResponse, User, Session, Depends, get_db,
# get_current_user, logger, HTTPException are defined/imported elsewhere

@app.get(f"{BASE_API_PATH}/alumni/{{alumni_id}}", response_model=AlumniResponse, tags=["Alumni"])
async def get_alumni_by_id(
    alumni_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gets details for a specific alumnus by their user ID."""
    logger.info(f"API request for alumni details ID: {alumni_id}")
    alumnus = db.query(User).filter(
        User.id == alumni_id,
        User.is_alumni == True
    ).first()

    if not alumnus:
        raise HTTPException(status_code=404, detail="Alumnus not found")

    # Pydantic's response_model will automatically convert the User object
    # to the AlumniResponse schema if fields match.
    return alumnus

@app.post(f"{BASE_API_PATH}/alumni/{{alumni_id}}/like", status_code=200, tags=["Alumni"])
async def like_alumnus(
    alumni_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Increments the like count for a specific alumnus."""
    logger.info(f"API request by '{current_user.username}' to like alumnus ID {alumni_id}.")
    alumnus = db.query(User).filter(
        User.id == alumni_id,
        User.is_alumni == True
    ).first()

    if not alumnus:
        raise HTTPException(status_code=404, detail="Alumnus not found")

    # Optional checks (e.g., prevent self-like if applicable) could go here

    alumnus.likes += 1
    try:
        db.commit()
        db.refresh(alumnus)
        logger.info(f"User '{current_user.username}' liked alumnus ID {alumni_id}. New count: {alumnus.likes}")
        # Return the new like count
        return {"likes": alumnus.likes}
    except Exception as e:
        db.rollback()
        logger.error(f"Like alumnus DB error for ID {alumni_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update like count")
# --- Expert Q&A API ---
# Assumes 'QuestionOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/questions/popular", response_model=List['QuestionOut'], tags=["Expert Q&A"]) # Use forward reference if needed
async def get_popular_questions(limit: int = 10, db: Session = Depends(get_db)):
    """Gets the most popular (highest liked) questions."""
    # Assumes 'Question' model is imported/defined
    questions = db.query(Question).order_by(Question.likes.desc(), Question.created_at.desc()).limit(limit).all()
    return questions

# Assumes 'QuestionCreate' schema and 'QuestionOut' schema are imported/defined
@app.post(f"{BASE_API_PATH}/questions", response_model='QuestionOut', status_code=201, tags=["Expert Q&A"]) # Use forward reference if needed
async def create_question(question: 'QuestionCreate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Creates a new question (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' to create question.")
    # Assumes 'Question' model is imported/defined
    db_question = Question(question_text=question.question_text, user_id=current_user.id)
    try:
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        logger.info(f"User '{current_user.username}' created question ID {db_question.id}")
        return db_question
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create question DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save question")

# Assumes 'QuestionOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/users/{{username}}/questions", response_model=List['QuestionOut'], tags=["Expert Q&A", "Users"]) # Use forward reference if needed
async def get_user_questions(username: str, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes models are imported
    """Gets all questions asked by a specific user (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' for questions by '{username}'.")
    # Assumes 'User' model is imported/defined
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User whose questions were requested not found")
    # Assumes 'Question' model is imported/defined
    questions = db.query(Question).filter(Question.user_id == user.id).order_by(Question.created_at.desc()).all()
    return questions

@app.post(f"{BASE_API_PATH}/questions/{{question_id}}/like", status_code=200, tags=["Expert Q&A"])
async def like_question(question_id: int, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Increments the like count for a question (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' to like question ID {question_id}.")
    # Assumes 'Question' model is imported/defined
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    db_question.likes += 1
    try:
        db.commit()
        db.refresh(db_question)
        logger.info(f"User '{current_user.username}' liked question ID {question_id}. New count: {db_question.likes}")
        return {"message": f"Question {question_id} liked!", "likes": db_question.likes}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to like question ID {question_id} DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update like count")

# --- Career Fairs API ---
# Assumes 'CareerFairOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/career_fairs", response_model=List['CareerFairOut'], tags=["Career Fairs"]) # Use forward reference if needed
async def get_career_fairs(upcoming_only: bool = False, db: Session = Depends(get_db)):
    """Gets a list of career fairs."""
    # Assumes 'CareerFair' model is imported/defined
    query = db.query(CareerFair)
    if upcoming_only:
        query = query.filter(CareerFair.date >= date.today())
    career_fairs = query.order_by(CareerFair.date).all()
    return career_fairs

# Assumes 'CareerFairCreate' and 'CareerFairOut' schemas are imported/defined
@app.post(f"{BASE_API_PATH}/career_fairs", response_model='CareerFairOut', status_code=201, tags=["Career Fairs"]) # Use forward reference if needed
async def create_career_fair(career_fair: 'CareerFairCreate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Creates a new career fair (requires API auth, ideally admin)."""
    logger.info(f"API request by '{current_user.username}' to create career fair.")
    # Assumes 'CareerFair' model is imported/defined
    db_career_fair = CareerFair(**career_fair.model_dump())
    try:
        db.add(db_career_fair)
        db.commit()
        db.refresh(db_career_fair)
        logger.info(f"Career fair '{db_career_fair.name}' (ID: {db_career_fair.id}) created by '{current_user.username}'.")
        return db_career_fair
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create career fair '{career_fair.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save career fair")

# --- Jobs API ---
# Assumes 'JobOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/jobs", response_model=List['JobOut'], tags=["Jobs"]) # Use forward reference if needed
async def get_jobs(db: Session = Depends(get_db)):
    """Gets a list of job postings."""
    # Assumes 'Job' model is imported/defined
    jobs = db.query(Job).order_by(desc(Job.date_posted)).all()
    return jobs

# Assumes 'JobCreate' and 'JobOut' schemas are imported/defined
@app.post(f"{BASE_API_PATH}/jobs", response_model='JobOut', status_code=201, tags=["Jobs"]) # Use forward reference if needed
async def create_job(job: 'JobCreate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Creates a new job posting (requires API auth, ideally admin)."""
    logger.info(f"API request by '{current_user.username}' to create job.")
    # Assumes 'Job' model is imported/defined
    db_job = Job(**job.model_dump())
    try:
        db.add(db_job)
        db.flush()
        create_new_job_notifications(db, db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Job '{db_job.title}' (ID: {db_job.id}) created by '{current_user.username}'. Notifications prepared/sent.")
        return db_job
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create job '{job.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save job listing")

# --- Internships API ---
# Assumes 'InternshipOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/internships", response_model=List['InternshipOut'], tags=["Internships"]) # Use forward reference if needed
async def get_internships(upcoming_only: bool = True, db: Session = Depends(get_db)):
    """Gets a list of internships."""
    # Assumes 'Internship' model is imported/defined
    query = db.query(Internship)
    if upcoming_only:
        query = query.filter(
            (Internship.start_date >= date.today()) |
            (Internship.end_date == None) |
            (Internship.end_date >= date.today())
        )
    internships = query.order_by(Internship.start_date).all()
    return internships

# Assumes 'InternshipCreate' and 'InternshipOut' schemas are imported/defined
@app.post(f"{BASE_API_PATH}/internships", response_model='InternshipOut', status_code=201, tags=["Internships"]) # Use forward reference if needed
async def create_internship(internship: 'InternshipCreate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Creates a new internship (requires API auth, ideally admin)."""
    logger.info(f"API request by '{current_user.username}' to create internship.")
    # Assumes 'Internship' model is imported/defined
    db_internship = Internship(**internship.model_dump())
    try:
        db.add(db_internship)
        db.flush()
        create_new_internship_notifications(db, db_internship)
        db.commit()
        db.refresh(db_internship)
        logger.info(f"Internship '{db_internship.title}' (ID: {db_internship.id}) created by '{current_user.username}'. Notifications prepared/sent.")
        return db_internship
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create internship '{internship.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save internship")

# --- Hackathons API ---
# Assumes 'HackathonOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/hackathons", response_model=List['HackathonOut'], tags=["Hackathons"]) # Use forward reference if needed
async def get_hackathons(upcoming_only: bool = True, db: Session = Depends(get_db)):
    """Gets a list of hackathons."""
    # Assumes 'Hackathon' model is imported/defined
    query = db.query(Hackathon)
    if upcoming_only:
        query = query.filter(Hackathon.date >= date.today())
    hackathons = query.order_by(Hackathon.date).all()
    return hackathons

# Assumes 'HackathonCreate' and 'HackathonOut' schemas are imported/defined
@app.post(f"{BASE_API_PATH}/hackathons", response_model='HackathonOut', status_code=201, tags=["Hackathons"]) # Use forward reference if needed
async def create_hackathon(hackathon: 'HackathonCreate', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Creates a new hackathon (requires API auth, ideally admin)."""
    logger.info(f"API request by '{current_user.username}' to create hackathon.")
    hackathon_data = hackathon.model_dump(exclude_unset=True)
    # Assumes 'Hackathon' model is imported/defined
    db_hackathon = Hackathon(**hackathon_data)
    try:
        db.add(db_hackathon)
        db.flush()
        create_new_hackathon_notifications(db, db_hackathon)
        db.commit()
        db.refresh(db_hackathon)
        logger.info(f"Hackathon '{db_hackathon.name}' (ID: {db_hackathon.id}) created by '{current_user.username}'. Notifications prepared/sent.")
        return db_hackathon
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create hackathon '{hackathon.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save hackathon")

# --- Daily Spark API ---
# Assumes 'DailySparkQuestionOut' schema is imported/defined
@app.get(f"{BASE_API_PATH}/daily-spark/today", response_model='DailySparkQuestionOut', tags=["Daily Spark"]) # Use forward reference if needed
async def get_todays_question(db: Session = Depends(get_db)):
    """Gets the most recent Daily Spark question."""
    # Assumes 'DailySparkQuestion' model is imported/defined
    today_question = db.query(DailySparkQuestion).order_by(desc(DailySparkQuestion.created_at)).first()
    if not today_question:
        raise HTTPException(status_code=404, detail="Today's Daily Spark question not found")
    return today_question

# Assumes 'DailySparkQuestionOut' schema and 'DailySparkAnswer' model are imported/defined
@app.get(f"{BASE_API_PATH}/daily-spark/top-liked", response_model=List['DailySparkQuestionOut'], tags=["Daily Spark"]) # Use forward reference if needed
async def get_top_liked_questions(limit: int = 5, db: Session = Depends(get_db)):
    """Gets Daily Spark questions ordered by the total votes on their answers."""
    questions_with_votes = db.query(
            DailySparkQuestion,
            func.sum(DailySparkAnswer.votes).label('total_votes')
        )\
        .outerjoin(DailySparkAnswer, DailySparkQuestion.id == DailySparkAnswer.question_id)\
        .group_by(DailySparkQuestion.id)\
        .order_by(desc('total_votes'))\
        .limit(limit)\
        .all()

    top_questions = [q for q, votes in questions_with_votes]
    return top_questions

# Assumes 'DailySparkSubmit' schema and 'DailySparkAnswerOut' schema are imported/defined
@app.post(f"{BASE_API_PATH}/daily-spark/submit", response_model='DailySparkAnswerOut', status_code=201, tags=["Daily Spark"]) # Use forward reference if needed
async def submit_daily_spark_answer(data: 'DailySparkSubmit', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Submits an answer to the most recent Daily Spark question (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' to submit Daily Spark answer.")
    user_identifier = current_user.username

    # Assumes 'DailySparkQuestion' model is imported/defined
    today_question = db.query(DailySparkQuestion).order_by(desc(DailySparkQuestion.created_at)).first()
    if not today_question:
        raise HTTPException(status_code=404, detail="Cannot submit answer: Today's question not found")

    # Assumes 'DailySparkAnswer' model is imported/defined
    new_answer = DailySparkAnswer(
        question_id=today_question.id,
        text=data.text,
        user=user_identifier
    )
    try:
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        logger.info(f"User '{current_user.username}' submitted answer ID {new_answer.id} for Daily Spark question ID {today_question.id}")
        return new_answer
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit Daily Spark answer DB error by '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save submission")

@app.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/upvote", tags=["Daily Spark"])
async def upvote_answer(answer_id: int, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Upvotes a specific Daily Spark answer (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' to upvote Daily Spark answer ID {answer_id}.")
    # Assumes 'DailySparkAnswer' model is imported/defined
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    answer.votes += 1
    try:
        db.commit()
        db.refresh(answer)
        logger.info(f"User '{current_user.username}' upvoted Daily Spark answer ID {answer_id}. New votes: {answer.votes}")
        return {"votes": answer.votes}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upvote answer ID {answer_id} DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not record vote")

@app.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/downvote", tags=["Daily Spark"])
async def downvote_answer(answer_id: int, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes 'User' is imported
    """Downvotes a specific Daily Spark answer (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' to downvote Daily Spark answer ID {answer_id}.")
    # Assumes 'DailySparkAnswer' model is imported/defined
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    answer.votes -= 1
    try:
        db.commit()
        db.refresh(answer)
        logger.info(f"User '{current_user.username}' downvoted Daily Spark answer ID {answer_id}. New votes: {answer.votes}")
        return {"votes": answer.votes}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to downvote answer ID {answer_id} DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not record vote")

# --- Feed and General Features API ---
# Assumes 'Event' schema and models (Job, Internship, Hackathon) are imported/defined
@app.get(f"{BASE_API_PATH}/feed/events", response_model=List['Event'], tags=["Feed"]) # Use forward reference if needed
async def get_feed_events(limit_per_type: int = 3, db: Session = Depends(get_db)):
    """Compiles a feed of recent events (jobs, internships, hackathons)."""
    today = date.today()
    feed_items: List['Event'] = [] # Use forward reference if needed

    try:
        jobs = db.query(Job).order_by(desc(Job.date_posted)).limit(limit_per_type).all()
        feed_items.extend([Event.model_validate(j, from_attributes=True, context={'type':'job'}) for j in jobs])

        internships = db.query(Internship).filter((Internship.start_date <= today) | (Internship.start_date == None)).order_by(desc(Internship.start_date)).limit(limit_per_type).all()
        feed_items.extend([Event.model_validate(i, from_attributes=True, context={'type':'internship'}) for i in internships])

        hackathons = db.query(Hackathon).filter((Hackathon.date <= today) | (Hackathon.date == None)).order_by(desc(Hackathon.date)).limit(limit_per_type).all()
        feed_items.extend([Event.model_validate(h, from_attributes=True, context={'type':'hackathon'}) for h in hackathons])

        feed_items.sort(key=lambda item: item.date if item.date else date.min, reverse=True)
        return feed_items
    except Exception as e:
        logger.error(f"Error fetching feed events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating feed")

# Assumes 'FeatureOut' schema and 'Feature' model are imported/defined
@app.get(f"{BASE_API_PATH}/features", response_model=List['FeatureOut'], tags=["General"]) # Use forward reference if needed
async def get_features_list(db: Session = Depends(get_db)):
    """Retrieves a list of available platform features (if stored in DB)."""
    features = db.query(Feature).all()
    return features

# --- Search API ---
# Assumes 'SearchResult' schema and various models (User, CareerFair, etc.) are imported/defined
@app.get(f"{BASE_API_PATH}/search", response_model=List['SearchResult'], tags=["Search"]) # Use forward reference if needed
async def search_resources(
    term: str,
    db: Session = Depends(get_db),
    current_user: Optional['User'] = Depends(get_optional_current_user) # Assumes 'User' is imported
    ):
    """Searches across different resource types based on a query term."""
    results: List['SearchResult'] = [] # Use forward reference if needed

    if not term or len(term.strip()) < 2: return []

    term_stripped = term.strip()
    search_term_like = f"%{term_stripped}%"
    logger.info(f"Search requested for term: '{term_stripped}'")

    try:
        users = db.query(User).filter(User.username.ilike(search_term_like)).limit(5).all()
        results.extend([SearchResult(type='user', id=u.id, name=u.username, url=f"/profile.html?username={u.username}") for u in users])

        fairs = db.query(CareerFair).filter(CareerFair.name.ilike(search_term_like)).limit(5).all()
        results.extend([SearchResult(type='career_fair', id=f.id, name=f.name, url=f"/career-fairs.html#fair-{f.id}") for f in fairs])

        hackathons = db.query(Hackathon).filter(Hackathon.name.ilike(search_term_like)).limit(5).all()
        results.extend([SearchResult(type='hackathon', id=h.id, name=h.name, url=f"/explore-hackathons.html#hackathon-{h.id}") for h in hackathons])

        jobs = db.query(Job).filter(Job.title.ilike(search_term_like)).limit(5).all()
        results.extend([SearchResult(type='job', id=j.id, name=f"{j.title} at {j.company or 'N/A'}", url=j.url or f"/jobs.html#job-{j.id}") for j in jobs])

        # Assumes 'SearchHistory' model is imported/defined
        if term_stripped and current_user:
            try:
                db_search_history = SearchHistory(user_id=current_user.id, search_term=term_stripped)
                db.add(db_search_history)
                db.commit()
                logger.info(f"Saved search term '{term_stripped}' for user '{current_user.username}'.")
            except Exception as e_hist:
                db.rollback()
                logger.error(f"Failed to save search history for user '{current_user.username}': {e_hist}", exc_info=True)

        logger.info(f"Search for '{term_stripped}' yielded {len(results)} results.")
        return results

    except Exception as e_search:
        logger.error(f"Error during search for '{term_stripped}': {e_search}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error performing search")


# --- Notifications API ---
# Assumes 'NotificationOut' schema and 'Notification' model are imported/defined
@app.get(f"{BASE_API_PATH}/notifications", response_model=List['NotificationOut'], tags=["Notifications", "Users"]) # Use forward reference if needed
async def get_user_notifications(only_unread: bool = False, db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes models are imported
    """Gets notifications for the current user (requires API auth)."""
    logger.info(f"API request by '{current_user.username}' for notifications (unread={only_unread}).")
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id)\
        .filter(Notification.is_read == (False if only_unread else Notification.is_read))\
        .order_by(desc(Notification.created_at)).limit(50).all()
    return notifications

# Assumes 'NotificationMarkRead' schema and 'Notification' model are imported/defined
@app.post(f"{BASE_API_PATH}/notifications/mark-read", status_code=200, tags=["Notifications", "Users"])
async def mark_notifications_as_read(notification_data: 'NotificationMarkRead', db: Session = Depends(get_db), current_user: 'User' = Depends(get_current_user)): # Assumes schemas/models are imported
    """Marks specified notifications as read for the current user (requires API auth)."""
    if not notification_data.notification_ids:
        return {"message": "No notification IDs provided"}

    logger.info(f"API request by '{current_user.username}' to mark notifications read: {notification_data.notification_ids}")

    try:
        updated_count = db.query(Notification)\
            .filter(Notification.user_id == current_user.id, Notification.id.in_(notification_data.notification_ids))\
            .update({"is_read": True, "updated_at": datetime.utcnow()}, synchronize_session=False)

        db.commit()
        logger.info(f"User '{current_user.username}' marked {updated_count} notifications as read.")
        return {"message": f"{updated_count} notifications marked as read"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark notifications read DB error for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update notifications")

# --- Help/Issues API ---
# Assumes 'UserIssueCreate' schema, 'UserIssueResponse' schema, and 'UserIssue' model are imported/defined
@app.post(f"{BASE_API_PATH}/help/submit-issue", response_model='UserIssueResponse', status_code=201, tags=["Help"]) # Use forward reference if needed
async def submit_user_issue_report(
    issue_data: 'UserIssueCreate', # Assumes schema is imported
    db: Session = Depends(get_db),
    current_user: Optional['User'] = Depends(get_optional_current_user) # Assumes model is imported
    ):
    """Submits a user issue or feedback. Allows anonymous submission."""
    user_id = current_user.id if current_user else None
    submitter_log_name = f"User ID {user_id}" if user_id else f"Anonymous ({issue_data.email})"
    logger.info(f"Issue report submission received from {submitter_log_name}.")

    # Assumes 'UserIssue' model is imported/defined
    db_issue = UserIssue(
        user_id=user_id,
        name=issue_data.name,
        email=issue_data.email,
        message=issue_data.message,
        submitted_at=datetime.utcnow()
    )
    try:
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        logger.info(f"Issue report ID {db_issue.id} saved successfully from {submitter_log_name}.")
        return db_issue
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit issue report DB error from {submitter_log_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not submit issue report")


# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Utility Function for Admin Password Resets (Keep Definition) ---
# Assumes 'User' model is imported/defined
def update_user_password(username_or_email: str, new_password: str):
    """
    Helper function to update a user's password directly via code. USE WITH CAUTION.
    """
    if len(new_password) < 8:
        print(f"[ERROR] Password for '{username_or_email}' is too short. Not updated.")
        return

    db: Session = SessionLocal()
    user = None
    try:
        user = db.query(User).filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user:
            hashed = hash_password(new_password) # Use secure hash
            user.hashed_password = hashed
            user.updated_at = datetime.utcnow()
            db.commit()
            print(f"[ADMIN UTIL] Hashed password updated for '{user.username}'.") 
        else:
            print(f"[ADMIN UTIL] User '{username_or_email}' not found.")
    except Exception as e:
        db.rollback()
        print(f"[ADMIN UTIL ERROR] Error updating password for '{username_or_email}': {e}")
    finally:
        db.close()


# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"Starting Uvicorn server...")
    APP_HOST = os.environ.get("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.environ.get("APP_PORT", 8001))
    print(f" -> Listening on http://{APP_HOST}:{APP_PORT}")

    db_path = os.path.join(BASE_DIR, 'explore.db')
    print(f" -> Database file: {db_path}")
    print(f" -> Frontend directory: {FRONTEND_DIR}")
    print(f" -> Static directory: {STATIC_DIR}")

    if not os.path.exists(db_path):
        print(f" [WARNING] Database file not found at {db_path}.")

    if not MAIL_USERNAME or not MAIL_PASSWORD:
         print("\n [WARNING] MAIL_USERNAME or MAIL_PASSWORD environment variables not set.")
         print("           Password reset email functionality WILL FAIL.\n")

    uvicorn.run(
        "exp:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level="info"
        )