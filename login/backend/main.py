from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Annotated
from passlib.context import CryptContext
from urllib.parse import urlencode
import os
import secrets
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
import ssl
import smtplib
import asyncio

# Load environment variables (consider using a .env file for sensitive data)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///universe.db")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", 465)
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create tables
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp = Column(String)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

# FastAPI app setup
app = FastAPI()

# CORS middleware (adjust origins as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update the directory path if needed
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../../frontend/assets")), name="static")
# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    otp: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility function to send OTP email (requires SMTP server details in environment variables)
def send_otp_email(email: str, otp: str):
    print(f"Attempting to send OTP to: {email}, OTP: {otp}")
    print(f"SMTP Server: {SMTP_SERVER}")
    print(f"SMTP Port: {SMTP_PORT}")
    print(f"SMTP Username: {SMTP_USERNAME}")
    print(f"Email From: {EMAIL_FROM}")
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM]):
        print("SMTP configuration not found in environment variables.")
        return

    port = int(SMTP_PORT)
    sender_email = EMAIL_FROM
    receiver_email = email
    password = SMTP_PASSWORD

    message = MIMEText(f"Your OTP for password reset is: {otp}")
    message['Subject'] = "Password Reset OTP"
    message['From'] = sender_email
    message['To'] = receiver_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"OTP sent successfully to {email}")
    except Exception as e:
        print(f"Error sending OTP email: {e}")

# Background task to delete expired OTPs
def delete_expired_otps(db: Session):
    expiration_time = datetime.utcnow()
    expired_otps = db.query(OTP).filter(OTP.expires_at < expiration_time).delete()
    db.commit()
    print(f"Deleted {expired_otps} expired OTPs.")

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, error: str = None, message: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "message": message})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter((User.username == username) | (User.email == username)).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        params = {"error": "Invalid username or password"}
        return RedirectResponse(url=f"/?{urlencode(params)}", status_code=302)

    # In a real application, you would typically set a session cookie here
    return RedirectResponse(url="/home", status_code=302)

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    # In a real application, you would check if the user is authenticated
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    db_user_username = db.query(User).filter(User.username == username).first()
    if db_user_username:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already registered"})

    db_user_email = db.query(User).filter(User.email == email).first()
    if db_user_email:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})

    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/", status_code=302)

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request, error: str = None, message: str = None):
    return templates.TemplateResponse("forgetpass.html", {"request": request, "error": error, "message": message})

@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    email: Annotated[EmailStr, Form()],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # ... function body ...
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return templates.TemplateResponse("forgetpass.html", {"request": request, "error": "There is no account associated with this email."})

    # Generate OTP
    otp = secrets.token_hex(3).upper()  # Generate a 6-character OTP
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Save OTP to the database
    db_otp = db.query(OTP).filter(OTP.email == email).first()
    if db_otp:
        db_otp.otp = otp
        db_otp.created_at = datetime.utcnow()
        db_otp.expires_at = expires_at
    else:
        new_otp = OTP(email=email, otp=otp, expires_at=expires_at)
        db.add(new_otp)
    db.commit()

    # Send OTP email in the background
    background_tasks.add_task(send_otp_email, email, otp)
    print(f"Initiated background task to send OTP to {email}: {otp}")
    return RedirectResponse(url=f"/otp?email={email}", status_code=302)

@app.get("/otp", response_class=HTMLResponse)
async def otp_page(request: Request, email: str, error: str = None):
    return templates.TemplateResponse("otp.html", {"request": request, "email": email, "error": error})

@app.post("/otp", response_class=HTMLResponse)
async def verify_otp(
    request: Request,
    email: Annotated[str, Form()],
    otp: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    # ... function body ...
    db_otp = db.query(OTP).filter(OTP.email == email, OTP.otp == otp, OTP.expires_at > datetime.utcnow()).first()
    if not db_otp:
        params = {"email": email, "error": "Invalid or expired OTP."}
        return RedirectResponse(url=f"/otp?{urlencode(params)}", status_code=302)

    # OTP is valid, redirect to reset password page
    return RedirectResponse(url=f"/reset-password?email={email}", status_code=302)

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str, error: str = None):
    return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": error})

@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # This should ideally not happen if the flow is correct
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(new_password)
    user.hashed_password = hashed_password
    db.commit()

    # Delete the used OTP
    db.query(OTP).filter(OTP.email == email).delete()
    db.commit()

    return RedirectResponse(url="/?message=Password reset successfully. Please log in.", status_code=302)

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Run the background task to delete expired OTPs periodically (e.g., every minute)
async def scheduled_tasks():
    while True:
        await asyncio.sleep(60)
        with SessionLocal() as db:
            delete_expired_otps(db)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_tasks())