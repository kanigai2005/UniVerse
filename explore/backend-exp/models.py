
from datetime import date, datetime
import os
from typing import Optional,List
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint,
    and_, or_, not_  # <<< ADD THESE HERE
)
from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base, selectinload
from pydantic import EmailStr,BaseModel,ConfigDict,computed_field,field_validator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'explore.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models (Define ALL before Pydantic Schemas) ---

def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_student = Column(Boolean, default=False)
    is_alumni = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    activity_score = Column(Integer, default=0)
    achievements = Column(Text, nullable=True)
    alumni_gems = Column(Integer, default=0)
    department = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    alma_mater = Column(String, nullable=True)
    interviews = Column(Text, nullable=True)
    internships = Column(Text, nullable=True) # This is text description field
    startups = Column(Text, nullable=True)
    current_company = Column(String, nullable=True)
    milestones = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    likes = Column(Integer, default=0)
    badges = Column(Integer, default=0)
    solved = Column(Integer, default=0)
    links = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Use utcnow for consistency
    is_active = Column(Boolean, default=True, nullable=False, server_default='1')
    questions = relationship("Question", back_populates="user")
    issues = relationship("UserIssue", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    applied_hackathons = relationship("AppliedHackathon", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user") # Add relationship
    # In class User(Base):
    sent_connection_requests = relationship(
    "UserConnection",
    foreign_keys="[UserConnection.requester_id]", # Points to the UserConnection table's column
    back_populates="requester"                   # Name of the attribute in UserConnection model
    )
    received_connection_requests = relationship(
    "UserConnection",
    foreign_keys="[UserConnection.receiver_id]", # Points to the UserConnection table's column
    back_populates="receiver"                   # Name of the attribute in UserConnection model
    )
    expert_answers = relationship("ExpertQAAnswer", back_populates="user")
    posted_daily_sparks = relationship("DailySparkQuestion", back_populates="posted_by_alumnus", cascade="all, delete-orphan")

# In exp.py - Find the UserConnection SQLAlchemy model definition

class UserConnection(Base):
    __tablename__ = "user_connections"
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True) # Correct column name
    status = Column(String, default='pending', nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- ENSURE THESE RELATIONSHIPS MATCH User ---
    requester = relationship("User", foreign_keys=[requester_id], back_populates="sent_connection_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_connection_requests")# --- END RELATIONSHIP CHECK ---

    __table_args__ = ( UniqueConstraint('requester_id', 'receiver_id', name='uq_requester_receiver'), )
# IMPORTANT:
# 1. You WILL need to update your database schema. If you have existing data in user_connections,
#    this will be a more complex migration (drop old, create new, or carefully alter and populate status).
#    For development, deleting explore.db and letting it recreate is easiest IF YOU DON'T MIND LOSING DATA.
# 2. Update User model relationships if they were specific to the old UserConnection structure.
#    For instance, user.connections might now be more complex to define.
#    A simpler way is to query UserConnection directly.
class CareerFair(Base):
    __tablename__ = "career_fairs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Hackathon(Base):
    __tablename__ = "hackathons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True) # Made nullable to match Pydantic schema
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    theme = Column(String, nullable=True)
    prize_pool = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    applications = relationship("AppliedHackathon", back_populates="hackathon")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    question_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expert_answers = relationship("ExpertQAAnswer", back_populates="question", cascade="all, delete-orphan")
    user = relationship("User", back_populates="questions")
class ChatContact(Base):
    __tablename__ = "chat_contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = relationship("ChatMessage", back_populates="contact")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("chat_contacts.id"))
    sender = Column(String, nullable=True) # Could be 'user' or 'bot' or username
    text = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contact = relationship("ChatContact", back_populates="messages")

class DailySparkQuestion(Base):
    __tablename__ = "daily_spark_questions"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)
    question = Column(Text, nullable=False) # This is the question text itself

    # --- ADDED/MODIFIED Fields ---
    # Link to the alumnus who posted it. nullable=False means it MUST be an alumnus.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    posted_by_alumnus = relationship("User", back_populates="posted_daily_sparks") # Relationship to the User model

    # Date of posting for daily limits. index=True for faster queries.
    posted_date = Column(Date, nullable=False, default=date.today, index=True)
    # --- END ADDED/MODIFIED Fields ---

    created_at = Column(DateTime, default=datetime.utcnow) # Original creation timestamp of the row
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    answers = relationship("DailySparkAnswer", back_populates="question")

    # --- ADDED Constraint for one post per alumnus per day ---
    __table_args__ = (
        UniqueConstraint('user_id', 'posted_date', name='uq_alumni_spark_once_per_day'),
    )


class DailySparkAnswer(Base):
    __tablename__ = "daily_spark_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("daily_spark_questions.id"))
    user = Column(String) # Storing username for simplicity
    text = Column(Text, nullable=False)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    # IMPORTANT: Ensure this column EXISTS in your 'jobs' table in explore.db
    # If not, add it using: ALTER TABLE jobs ADD COLUMN image_url TEXT;
    # Or remove image_url from here and the Pydantic models below.
    imageUrl = Column(String, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_term = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="search_history") # Add back_populates

class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False) # e.g., 'new_job', 'new_hackathon', 'mention'
    related_id = Column(Integer, nullable=True) # e.g., job_id, hackathon_id, post_id
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional link to user
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending') # e.g., pending, investigating, resolved
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="issues")

# --- Add near your other SQLAlchemy model definitions ---

class AlumniLike(Base):
    __tablename__ = "alumni_likes"
    # Foreign key to the user performing the like
    liker_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    # Foreign key to the alumnus being liked
    liked_alumni_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    # Timestamp of the like action
    created_at = Column(DateTime, default=datetime.utcnow)

    # Define relationships (optional but can be useful)
    liker = relationship("User", foreign_keys=[liker_user_id])
    liked_alumnus = relationship("User", foreign_keys=[liked_alumni_id])

    # Ensure the combination is unique - one like per user per alumnus
    __table_args__ = (UniqueConstraint('liker_user_id', 'liked_alumni_id', name='uq_user_alumni_like'),)

class ExpertQAAnswer(Base):
    __tablename__ = "expert_qa_answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answer_text = Column(String, nullable=False)
    is_alumni_answer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)
    question = relationship("Question", back_populates="expert_answers")
    user = relationship("User")

class ExpertQAAnswerCreate(BaseModel):
    answer_text: str
# In your Pydantic models section (e.g., near other ExpertQA* models)

class ExpertQAAnswerOut(BaseModel):
    id: int
    question_id: int
    user_id: int
    # username: str # Removed direct field, will be provided by computed_field
    answer_text: str
    is_alumni_answer: bool
    created_at: datetime
    likes: int

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property # Important for from_attributes=True to pick this up
    def username(self) -> str:
        """
        Computes the username from the related User object.
        'self' in this context will be the Pydantic model instance being created.
        Pydantic's from_attributes magic makes the ORM instance's attributes
        accessible as if they were on the Pydantic model instance during creation.
        So, self.user here refers to the ORM ExpertQAAnswer.user relationship.
        """
        # The extensive diagnostic logging from your original validator can be re-added here
        # referencing `self` instead of `orm_instance` if needed for debugging.
        # For example: logger.critical(f"DIAGNOSTIC: Computed_field for username. ORM Answer ID: {self.id}")

        # Check if the 'user' attribute (relationship) exists on the ORM object
        # and if it's loaded (not None), and if that user has a username.
        if hasattr(self, 'user') and self.user and hasattr(self.user, 'username') and self.user.username is not None:
            return str(self.user.username)
        
        # Fallback if user or username is not available
        # Log this situation if it's unexpected
        # logger.warning(f"ExpertQAAnswerOut: Could not determine username for answer ID {self.id if hasattr(self, 'id') else 'N/A'}. User relationship: {self.user if hasattr(self, 'user') else 'NoUserAttr'}")
        return "Unknown User" # Provide a default string
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

class UserUpdate(BaseModel):
    alma_mater: Optional[str] = None
    profession: Optional[str] = None
    department: Optional[str] = None
    achievements: Optional[str] = None
    interviews: Optional[str] = None
    internships: Optional[str] = None # User description of their internship experiences
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    model_config = ConfigDict(extra='ignore') # Ignore extra fields in request

class UserResponse(UserBase):
    id: int
    is_student: bool
    is_alumni: bool
    is_active:bool
    is_admin: bool
    activity_score: int
    achievements: Optional[str] = None
    alumni_gems: int
    department: Optional[str] = None
    profession: Optional[str] = None
    alma_mater: Optional[str] = None
    interviews: Optional[str] = None
    internships: Optional[str] = None # User description field
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
    internships: Optional[str] = None # User description field
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DailySparkAnswerOut(BaseModel):
    id: int; user: str; text: str; votes: int
    model_config = ConfigDict(from_attributes=True)
class DailySparkQuestionOut(BaseModel):
    id: int
    company: Optional[str] = None
    role: Optional[str] = None
    question: str

    # --- ADDED/MODIFIED to show who posted it and when ---
    user_id: int  # Made non-optional as user_id in DB model is nullable=False
    posted_by_username: Optional[str] = None # For convenience, if loaded
    posted_date: date # Made non-optional, as DB model has default and is nullable=False
    # --- END ---

    answers: List[DailySparkAnswerOut] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator('posted_by_username', mode='before')
    @classmethod
    def populate_posted_by_username(cls, v, info):
        # This assumes that 'posted_by_alumnus' is eager-loaded on the ORM object.
        if hasattr(info.data, 'posted_by_alumnus') and info.data.posted_by_alumnus:
            return info.data.posted_by_alumnus.username
        # Fallback if relationship not loaded (should ideally be loaded in endpoint)
        # You might log a warning here if this happens often, as it means inefficient loading.
        return None 
class DailySparkSubmit(BaseModel): text: str
class DailySparkQuestionCreate(BaseModel): # For alumni posting questions
    question_text: str
    company: Optional[str] = None
    role: Optional[str] = None
class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    salary: Optional[str] = None
    date_posted: Optional[date] = None
    type: Optional[str] = None
    experience: Optional[str] = None
    imageUrl: Optional[str] = None # Make sure column exists in DB
    url: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)




class HackathonBase(BaseModel):
    name: str
    start_date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    prize_pool: Optional[str] = None
    url: Optional[str] = None

class HackathonCreate(HackathonBase):
    pass

class HackathonOut(HackathonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InternshipBase(BaseModel): # Represents an Internship posting
    title: str
    company: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    url: Optional[str] = None

class InternshipCreate(InternshipBase):
    pass

class InternshipOut(InternshipBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# In exp.py or your Pydantic models file
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, computed_field

class CareerFairBase(BaseModel):
    name: str
    start_date: Optional[date] = None # <<< MUST BE Optional[date] or date | None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

class CareerFairCreate(CareerFairBase):
    pass

class CareerFairOut(CareerFairBase): # Inherits the CORRECT 'date' definition
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
# ALSO: Ensure CareerFairOut.model_rebuild(force=True) is called after all models are defined.

class ConnectionUser(BaseModel):
    id: int
    username: str
    profession: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PendingRequestOut(BaseModel): # For displaying incoming requests
    # connection_id: int # If you add an 'id' to UserConnection
    requester_id: int
    requester_username: str
    requester_profession: Optional[str] = None
    requested_at: datetime # from UserConnection.created_at
    # Add other requester info if needed
    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(BaseModel):
    contact_id: int
    text: Optional[str] = None
    model_config = ConfigDict(from_attributes=True) 
    # file_path: Optional[str] = None # File uploads require different handling (FastAPI UploadFile)

class ChatContactInfo(BaseModel): # Pydantic model for the new endpoint's response item
    contact_id: int
    other_user_username: str
    other_user_id: int # Good to have for frontend if needed
    # last_message_preview: Optional[str] = None # Optional
    # last_message_timestamp: Optional[datetime] = None # Optional
    # unread_count: int = 0 # Optional

    model_config = ConfigDict(from_attributes=True)

class SendMessageRequest(BaseModel): # Input for send message endpoint
    contact_id: int
    text: str

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


class SearchResult(BaseModel):
    type: str # 'user', 'job', 'hackathon', etc.
    id: int
    name: str # Display name
    url: Optional[str] = None # Link to the resource page

class SearchHistoryCreate(BaseModel): # For POST request body
    searchTerm: str

class SearchHistoryItem(BaseModel):
    id: int
    user_id: int
    search_term: str
    timestamp: datetime
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
    email: EmailStr # Use EmailStr for automatic validation
    message: str

class UserIssueResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    email: str # Output as string
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
        if len(value) < 8:
             raise ValueError("Password must be at least 8 characters long")
        return value

# Inside exp.py, modify the HackathonOut Pydantic model
class HackathonOut(HackathonBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Make sure HackathonOut.model_rebuild(force=True) is called AFTER this definition

# --- Pydantic Model Rebuild Block (Place AFTER all models, BEFORE routes) ---
# This ensures forward references are resolved correctly, especially with nested models.
# --- Add/Modify Pydantic Models ---

# Base config for ORM mode
class OrmConfig: from_attributes = True

# --- Job Models ---
class JobBase(BaseModel):
    title: str; company: Optional[str] = None; location: Optional[str] = None; description: Optional[str] = None
    salary: Optional[str] = None; date_posted: Optional[date] = None; type: Optional[str] = None
    experience: Optional[str] = None; imageUrl: Optional[str] = None; url: Optional[str] = None # Use imageUrl
class JobCreate(JobBase): pass
class JobOut(JobBase):
    id: int; created_at: datetime; updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Event Model ---
# In your models.py or wherever Event is defined
from pydantic import BaseModel, Field
from typing import Optional, List, Literal # Ensure Optional and Literal are imported
from datetime import date, datetime      # Ensure date is imported

from pydantic import field_validator

class Event(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    location: Optional[str] = None
    type: Literal['job', 'internship', 'hackathon']
    company: Optional[str] = None
    start_date: Optional[date] = None # *** RENAMED from 'date' ***
    model_config = ConfigDict(from_attributes=True)

    @field_validator('start_date', mode='before') # <<< CORRECT: Validate the existing 'start_date' field
    @classmethod
    def validate_start_date(cls, v): # Renamed function
        if v is None:
            return None
        if isinstance(v, date):
            return v
        # Keep the rest of your validation logic if needed
        from datetime import datetime
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid date string format for start_date: {v}")
        raise TypeError(f"Invalid type for start_date field: {type(v)}")

# --- Daily Spark Models ---
class DailySparkAnswerOut(BaseModel):
    id: int; user: str; text: str; votes: int
    model_config = ConfigDict(from_attributes=True)
class DailySparkQuestionOut(BaseModel):
    id: int; company: Optional[str] = None; role: Optional[str] = None; question: str
    answers: List[DailySparkAnswerOut] = []
    model_config = ConfigDict(from_attributes=True)
class DailySparkSubmit(BaseModel): text: str
class DailySparkQuestionCreate(BaseModel): # For alumni posting questions
    question_text: str
    company: Optional[str] = None
    role: Optional[str] = None

# --- Expert Q&A Models ---
class ExpertQAAnswerCreate(BaseModel):
    answer_text: str

class QuestionCreate(BaseModel): question_text: str
class QuestionOut(BaseModel): # Now includes answers
    id: int; user_id: Optional[int] = None; username: Optional[str] = None # Add username
    question_text: str; created_at: datetime; likes: int
    expert_answers: List[ExpertQAAnswerOut] = [] # Include answers list
    model_config = ConfigDict(from_attributes=True)
    @field_validator('username', mode='before') # Simple way to add username if loading from ORM
    @classmethod
    def add_q_username(cls, v, info):
        if hasattr(info.data, 'user') and hasattr(info.data.user, 'username'):
            return info.data.user.username
        return "Anonymous" # Fallback



# --- Add these NEW SQLAlchemy models ---

class UnverifiedJob(Base):
    __tablename__ = "unverified_jobs"
    id = Column(Integer, primary_key=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending', index=True) # pending, approved, rejected

    # Fields mirroring the Job model
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    salary = Column(String, nullable=True)
    date_posted = Column(Date, nullable=True) # Date user suggests for posting
    type = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    imageUrl = Column(String, nullable=True)
    url = Column(String, nullable=True)

    # Relationship to the user who submitted it
    submitter = relationship("User")

class UnverifiedInternship(Base):
    __tablename__ = "unverified_internships"
    id = Column(Integer, primary_key=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending', index=True)

    # Fields mirroring the Internship model
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)

    submitter = relationship("User")

class UnverifiedCareerFair(Base):
    __tablename__ = "unverified_career_fairs"
    id = Column(Integer, primary_key=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending', index=True)

    # Fields mirroring the CareerFair model
    name = Column(String, nullable=False)
    start_date = Column(Date)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)

    submitter = relationship("User")

class UnverifiedHackathon(Base):
    __tablename__ = "unverified_hackathons"
    id = Column(Integer, primary_key=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending', index=True)

    # Fields mirroring the Hackathon model
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    theme = Column(String, nullable=True)
    prize_pool = Column(String, nullable=True)
    url = Column(String, nullable=True)

    submitter = relationship("User")

# --- Add near other SQLAlchemy model definitions ---

# --- Add near other SQLAlchemy model definitions ---
from sqlalchemy import UniqueConstraint # Make sure this is imported

class QuestionLike(Base):
    __tablename__ = "question_likes"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional relationships
    # user = relationship("User")
    # question = relationship("Question")

    # Unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'question_id', name='uq_user_question_like'),)

# --- Remember to create this table in your DB ---
# --- IMPORTANT: Ensure this table is created in your database ---
# (Run Base.metadata.create_all or use Alembic)

# --- Add these NEW Pydantic response models ---

class UnverifiedItemOut(BaseModel):
    id: int
    submitted_at: datetime
    status: str
    submitted_by_user_id: int
    # Add common fields if desired, e.g., title/name
    # name: Optional[str] = None # Example
    url:str
    model_config = ConfigDict(from_attributes=True)

# You can use the generic one, or specific ones if needed:
class UnverifiedJobOut(UnverifiedItemOut):
    title: str # Example specific field
    company: Optional[str] = None

class UnverifiedInternshipOut(UnverifiedItemOut):
    title: str # Example specific field
    company: Optional[str] = None

class UnverifiedCareerFairOut(UnverifiedItemOut):
    name: str # Example specific field
    start_date:Optional[date] = None

class UnverifiedHackathonOut(UnverifiedItemOut):
    name: str # Example specific field
    start_date:Optional[date] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str # Consider if email should always be returned
    is_student: bool
    is_alumni: bool
    is_admin: bool
    activity_score: Optional[int] = 0
    achievements: Optional[str] = None
    alumni_gems: Optional[int] = 0
    department: Optional[str] = None
    profession: Optional[str] = None
    alma_mater: Optional[str] = None
    interviews: Optional[str] = None
    internships: Optional[str] = None
    startups: Optional[str] = None
    current_company: Optional[str] = None
    milestones: Optional[str] = None
    advice: Optional[str] = None
    likes: Optional[int] = 0 # Assuming these are part of the user model
    badges: Optional[int] = 0
    solved: Optional[int] = 0
    links: Optional[int] = 0 # Assuming this maps to connections/links count
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # For Pydantic v2+ compatibility with ORM models
        # orm_mode = True # For Pydantic v1

# Pydantic model for receiving profile update data
class UserProfileUpdate(BaseModel):
    profession: Optional[str] = Field(None, description="User's professional role")
    current_company: Optional[str] = Field(None, description="User's current company")
    department: Optional[str] = Field(None, description="User's department (if applicable)")
    alma_mater: Optional[str] = Field(None, description="User's alma mater")
    achievements: Optional[str] = Field(None, description="User's achievements description")
    interviews: Optional[str] = Field(None, description="User's interview experiences")
    internships: Optional[str] = Field(None, description="User's internship experiences")
    startups: Optional[str] = Field(None, description="User's startup venture details")
    milestones: Optional[str] = Field(None, description="User's career milestones")
    advice: Optional[str] = Field(None, description="User's advice to others")
    # Add other fields from the edit form that map to the User model

class ChatSessionResponse(BaseModel):
    chat_id: int
    # other chat metadata if needed

class ConnectionUser(BaseModel):
    id: int
    username: str
    profession: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="Set user active or inactive") # REMOVED
    is_student: Optional[bool] = Field(None, description="Approve/update student status")
    is_alumni: Optional[bool] = Field(None, description="Approve/update alumni status")
    # Add any other status-like boolean fields you might manage for a User

    model_config = ConfigDict(extra='ignore')

class UserRoleUpdate(BaseModel):
    is_admin: Optional[bool] = Field(None, description="Set or remove admin privileges")
    model_config = ConfigDict(extra='ignore')


class UserActivityUpdate(BaseModel): # For activating/deactivating
    is_active: bool
    model_config = ConfigDict(extra='ignore')

# --- Don't forget to add these to the Pydantic model rebuild block ---
# UserProfileUpdate.model_rebuild(force=True); UnverifiedItemOut.model_rebuild(force=True);
# UnverifiedJobOut.model_rebuild(force=True); UnverifiedInternshipOut.model_rebuild(force=True);
# UnverifiedCareerFairOut.model_rebuild(force=True); UnverifiedHackathonOut.model_rebuild(force=True);
# ... (rest of the rebuilds) ...

# --- IMPORTANT ---
# Make sure Base.metadata.create_all(bind=engine) is called somewhere
# AFTER these definitions are processed so the tables get created in your DB.
# If you use Alembic, create migrations for these new tables.

# (Keep other Pydantic models: UserBase, UserCreate, UserUpdate, UserResponse, AlumniResponse, Hackathon*, Internship*, CareerFair*, Chat*, Search*, Feature*, Notification*, Issue*, Password*)

# --- Pydantic Model Rebuild Block (MUST be AFTER ALL Pydantic models) ---
import logging

logger = logging.getLogger(__name__)

try:
    logger.info("Attempting EXPLICIT rebuild of Pydantic models...")
    # List ALL your Pydantic models explicitly here
    UserBase.model_rebuild(force=True); UserCreate.model_rebuild(force=True); UserUpdate.model_rebuild(force=True)
    UserResponse.model_rebuild(force=True); AlumniResponse.model_rebuild(force=True); DailySparkAnswerOut.model_rebuild(force=True)
    DailySparkQuestionOut.model_rebuild(force=True); JobBase.model_rebuild(force=True); JobCreate.model_rebuild(force=True)
    JobOut.model_rebuild(force=True); HackathonBase.model_rebuild(force=True); HackathonCreate.model_rebuild(force=True)
    HackathonOut.model_rebuild(force=True); InternshipBase.model_rebuild(force=True); InternshipCreate.model_rebuild(force=True)
    InternshipOut.model_rebuild(force=True); CareerFairBase.model_rebuild(force=True); CareerFairCreate.model_rebuild(force=True)
    CareerFairOut.model_rebuild(force=True); QuestionCreate.model_rebuild(force=True); QuestionOut.model_rebuild(force=True)
    ChatMessageCreate.model_rebuild(force=True); SendMessageRequest.model_rebuild(force=True); ChatMessageOut.model_rebuild(force=True)
    ChatContactOut.model_rebuild(force=True); DailySparkSubmit.model_rebuild(force=True); SearchResult.model_rebuild(force=True)
    SearchHistoryCreate.model_rebuild(force=True); SearchHistoryItem.model_rebuild(force=True); Event.model_rebuild(force=True)
    FeatureOut.model_rebuild(force=True); NotificationOut.model_rebuild(force=True); NotificationMarkRead.model_rebuild(force=True)
    UserIssueCreate.model_rebuild(force=True); UserIssueResponse.model_rebuild(force=True)
    ForgotPasswordRequest.model_rebuild(force=True); ResetPasswordRequest.model_rebuild(force=True)
    ExpertQAAnswerCreate.model_rebuild(force=True); ExpertQAAnswerOut.model_rebuild(force=True) # Added new models
    DailySparkQuestionCreate.model_rebuild(force=True) # Added new model
    UserStatusUpdate.model_rebuild(force=True),UserRoleUpdate.model_rebuild(force=True)
    UserActivityUpdate.model_rebuild(force=True)
    # Inside the explicit model_rebuild block
# ... (add the new model) ...
    #SelectedExpertQuestion.model_rebuild(force=True) # Add if you created a Pydantic model for it (usually not needed for this tracking table)
    # Ensure QuestionOut and ExpertQAAnswerOut are rebuilt
    QuestionOut.model_rebuild(force=True)
    ExpertQAAnswerOut.model_rebuild(force=True)
    UnverifiedItemOut.model_rebuild(force=True)
    UnverifiedJobOut.model_rebuild(force=True); UnverifiedInternshipOut.model_rebuild(force=True)
    UnverifiedCareerFairOut.model_rebuild(force=True); UnverifiedHackathonOut.model_rebuild(force=True)
    ChatSessionResponse.model_rebuild(force=True); ConnectionUser.model_rebuild(force=True)
    PendingRequestOut.model_rebuild(force=True)

    # ... (rest of the rebuilds) ...

    logger.info("Explicit Pydantic models rebuild process completed.")
except Exception as e:
    logger.error(f"Error rebuilding Pydantic models: {e}", exc_info=True)
    raise RuntimeError("Failed to rebuild Pydantic models") from e
