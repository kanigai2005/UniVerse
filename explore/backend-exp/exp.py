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
from typing import Any, List, Dict, Optional, Annotated, Tuple, Union # Added Tuple

from fastapi import FastAPI, HTTPException, Depends, Header, Body, Request, Form, Response, Cookie # Added Cookie
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base, selectinload
from sqlalchemy.exc import OperationalError # Import for specific exception handling
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.sqlite import DATE as SQLiteDATE # Keep if specific SQLite date handling needed

from pydantic import BaseModel, EmailStr, Field, ValidationError, ValidationInfo, computed_field, field_validator, ConfigDict, TypeAdapter

from passlib.context import CryptContext
from passlib.exc import UnknownHashError
import sys

from sqlalchemy import (
    create_engine, Column, Integer, Boolean, String, Date, Text, DateTime,
    func, ForeignKey, desc, Table, CheckConstraint, UniqueConstraint,
    and_, or_, not_  # <<< ADD THESE HERE
)

from .auth_utils import (
    require_user_from_cookie,
    get_current_user_from_cookie,
    session_storage, # <--- IMPORT session_storage
    otp_storage,     # <--- IMPORT otp_storage
    templates,
    logger
)
from .models import (
    # Database setup and SQLAlchemy Base
    ExpertQAAnswerOut,
    engine,
    Base,
    get_db,
    SessionLocal, 
    User,
    UserConnection,
    CareerFair,
    Internship,
    Hackathon,
    Question,
    ChatContact,
    ChatMessage,
    DailySparkQuestion,
    DailySparkAnswer,
    Job,
    SearchHistory,
    Feature,
    Notification,
    AppliedHackathon,
    UserIssue,
    AlumniLike,
    ExpertQAAnswer,
    UnverifiedJob,
    UnverifiedInternship,
    UnverifiedCareerFair,
    UnverifiedHackathon,
    QuestionLike,

    # --- Pydantic Schemas/Models ---
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    AlumniResponse,
    DailySparkAnswerOut,
    DailySparkQuestionOut,
    DailySparkSubmit,
    DailySparkQuestionCreate,
    JobBase,
    JobCreate,
    JobOut,
    HackathonBase,
    HackathonCreate,
    HackathonOut,
    InternshipBase,
    InternshipCreate,
    InternshipOut,
    CareerFairBase,
    CareerFairCreate,
    CareerFairOut,
    ConnectionUser,
    PendingRequestOut,
    ChatMessageCreate,
    ChatContactInfo,
    SendMessageRequest,
    ChatMessageOut,
    ChatContactOut,
    SearchResult,
    SearchHistoryCreate,
    SearchHistoryItem,
    FeatureOut,
    NotificationOut,
    NotificationMarkRead,
    UserIssueCreate,
    UserIssueResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Event, # Your Pydantic Event model
    QuestionCreate,
    QuestionOut,
    ExpertQAAnswerCreate, # If it's different from ExpertQAAnswerOut for creation
    # ExpertQAAnswerOut is already listed for SQLAlchemy models, ensure it's the Pydantic one here if distinct
    UnverifiedItemOut,
    UnverifiedJobOut,
    UnverifiedInternshipOut,
    UnverifiedCareerFairOut,
    UnverifiedHackathonOut,
    UserProfileUpdate,
    ChatSessionResponse,
    OrmConfig # If you defined this helper class in models.py
)

from .admin import admin_api_router, admin_html_router # Relative import

# ...

# --- Configure logging ---
logging.basicConfig(level=logging.INFO)
# Consistent logger name

# --- FastAPI App ---
app = FastAPI(title="Explore App")
app.include_router(admin_html_router)
app.include_router(admin_api_router)
# --- Configuration ---
# Use __file__ to get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'explore.db')}"
# Assuming frontend-exp is a sibling directory to the one containing this script
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend-exp")
# If frontend-exp is INSIDE the same directory as this script:
# FRONTEND_DIR = os.path.join(BASE_DIR, "frontend-exp")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

logger.info(f"Database URL: {DATABASE_URL}")
logger.info(f"Frontend Directory: {FRONTEND_DIR}")
logger.info(f"Static Directory: {STATIC_DIR}")

# --- Email Configuration ---
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 465)) # Default to 465 for SSL
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
BASE_API_PATH='api'
# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Create Tables ---
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables checked/created.")
except Exception as e:
    logger.error(f"Error creating database tables: {e}", exc_info=True)
    # Decide if you want to exit if tables can't be created
    # exit(1)

# --- Database Dependency ---
def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    logger.info("Running startup event: Creating database tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error creating database tables during startup: {e}", exc_info=True)

# --- Session Storage ---
#session_storage: Dict[str, int] = {}
#otp_storage: Dict[str, Dict[str, Any]] = {}

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
        # Check if the hash format is recognized before attempting verification
        if not pwd_context.identify(hashed_password):
            logger.warning(f"Attempted to verify password with unrecognized hash format: {hashed_password[:10]}...")
            return False
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # This specific exception occurs if the hash format is known but invalid/corrupted
        logger.warning(f"Verification failed due to UnknownHashError for hash: {hashed_password[:10]}...")
        return False
    except Exception as e:
        # Catch other potential errors during verification
        logger.error(f"Error verifying password: {e}", exc_info=True)
        return False

# --- OTP Storage (Simple In-Memory) ---
# --- Additional Models for Daily Spark and Expert Q&A Enhancements ---

from sqlalchemy import UniqueConstraint



# Track Daily Spark questions posted by alumni per day to enforce limits

# Expert Q&A models (assuming existing Question and Answer models)
# Add a flag to mark answers as alumni-only if needed (or separate table)
# For simplicity, we will add an 'is_alumni_answer' flag to answers


# --- Frontend Serving Setup ---
# Check if frontend directory exists
if not os.path.exists(FRONTEND_DIR):
    logger.error(f"Frontend directory not found: {FRONTEND_DIR}")
    raise RuntimeError(f"Frontend directory not found: {FRONTEND_DIR}")

try:
    abs_frontend_dir = os.path.abspath(FRONTEND_DIR)
    logger.info(f"Templates directory set to (absolute path): {abs_frontend_dir}")
except Exception as e:
    logger.error(f"Failed to initialize Jinja2Templates at {FRONTEND_DIR}: {e}")
    raise RuntimeError(f"Failed to initialize Jinja2Templates at {FRONTEND_DIR}: {e}")

# Mount static files only if the directory exists
if os.path.exists(STATIC_DIR):
    try:
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    except Exception as e:
        logger.error(f"Failed to mount static directory {STATIC_DIR}: {e}")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}. Static files will not be served.")

# --- Authentication Dependencies (Define BEFORE Routes use them) ---
security = HTTPBasic()
security_optional = HTTPBasic(auto_error=False) # Doesn't raise 401 if credentials missing

# --- Basic Auth Dependencies (for API clients) ---
def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> User:
    """Authenticates user based on HTTP Basic Auth. Raises 401 if invalid."""
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    # Check user exists before verifying password
    if not user:
        logger.debug(f"API Auth failed: User '{credentials.username}' not found.")
        raise HTTPException(
            status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"}
        )

    if not verify_password(credentials.password, user.hashed_password):
        logger.debug(f"API Auth failed: Incorrect password for user '{credentials.username}'.")
        raise HTTPException(
            status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"}
        )

    logger.info(f"API Auth successful for user '{user.username}'.")
    return user

async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPBasicCredentials], Depends(security_optional)],
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Tries Basic Auth if provided, returns None if missing/invalid."""
    if credentials is None:
        return None

    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        return None # Don't raise error, just return None

    logger.info(f"(Optional API Auth) User '{user.username}' authenticated via Basic.")
    return user

# --- Cookie Auth Dependencies (for Browser Sessions) ---

# --- Utility Functions ---
async def send_otp_email(email: str, otp: str) -> bool:
    """Sends OTP email using configured settings. Returns True on success, False on failure."""
    if not all([MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER]):
        logger.error("Email configuration incomplete. Cannot send OTP.")
        return False
    try:
        message = MIMEText(f'Your OTP for password reset is: {otp}\nThis OTP is valid for 5 minutes.')
        message['Subject'] = 'Password Reset OTP'
        message['From'] = MAIL_DEFAULT_SENDER
        message['To'] = email
        mail_port_int = int(MAIL_PORT) # Ensure port is integer

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
# These functions add notifications to the session but DO NOT COMMIT.
# Commit should happen after the related action (e.g., creating job) succeeds.

def create_notification(db: Session, user_id: int, message: str, type: str, related_id: Optional[int] = None):
    """Adds a notification object to the database session (does not commit)."""
    try:
        notification = Notification(
            user_id=user_id,
            message=message,
            type=type,
            related_id=related_id
        )
        db.add(notification)
    except Exception as e:
        # Log error but don't raise, as notification failure might not be critical
        logger.error(f"Error creating notification object for user {user_id}: {e}", exc_info=True)

def create_new_hackathon_notifications(db: Session, hackathon: Hackathon):
    """Adds notifications for all non-admin users about a new hackathon (does not commit)."""
    try:
        users = db.query(User).filter(User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Hackathon Alert: '{hackathon.name}' is now available!",
                type="new_hackathon",
                related_id=hackathon.id
            )
        logger.info(f"Prepared notifications for new hackathon '{hackathon.name}'.")
    except Exception as e:
        logger.error(f"Error preparing hackathon notifications: {e}", exc_info=True)

def create_new_job_notifications(db: Session, job: Job):
    """Adds notifications for all non-admin users about a new job (does not commit)."""
    try:
        users = db.query(User).filter(User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Job Alert: '{job.title}' at {job.company or 'Unknown Company'}!",
                type="new_job",
                related_id=job.id
            )
        logger.info(f"Prepared notifications for new job '{job.title}'.")
    except Exception as e:
        logger.error(f"Error preparing job notifications: {e}", exc_info=True)

def create_new_internship_notifications(db: Session, internship: Internship):
    """Adds notifications for all non-admin users about a new internship (does not commit)."""
    try:
        users = db.query(User).filter(User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Internship Opportunity: '{internship.title}' at {internship.company or 'Unknown Company'}!",
                type="new_internship",
                related_id=internship.id
            )
        logger.info(f"Prepared notifications for new internship '{internship.title}'.")
    except Exception as e:
        logger.error(f"Error preparing internship notifications: {e}", exc_info=True)


@app.put(f"{BASE_API_PATH}/users/{{username}}", response_model=UserResponse, tags=["Users", "API"])
async def update_user_profile_by_username(
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Updates the profile of the specified user by username. Only allowed if current_user matches username."""
    logger.info(f"API request to update profile for user '{username}' by '{current_user.username}'")

    if username != current_user.username:
        logger.warning(f"User '{current_user.username}' attempted to update profile of '{username}' - forbidden")
        raise HTTPException(status_code=403, detail="You can only update your own profile")

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



@app.get("/", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def serve_login_html(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Serves the main login page (login.html)."""
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "message": message})

@app.post("/login", response_class=RedirectResponse, tags=["Auth"])
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db) # get_db from models.py
):
    logger.info(f"Login attempt for username/email: '{username}'")
    user = db.query(User).filter( # User from models.py
        (User.username == username) | (User.email == username)
    ).first()

    login_error = None
    if not user or not verify_password(password, user.hashed_password):
        login_error = "Incorrect username or password."
        logger.warning(f"Login failed for '{username}'. Reason: {login_error}")
        query_params = urlencode({"error": login_error})
        # Redirect back to login page with error message
        # We create the RedirectResponse object and return it directly.
        # FastAPI will handle setting cookies if we set them on this response object.
        return RedirectResponse(url=f"/?{query_params}", status_code=303)

    # Login successful
    logger.info(f"User '{user.username}' (ID: {user.id}) logged in successfully.")
    session_token = secrets.token_urlsafe(32) # Ensure secrets is import

    # Store session token mapped to user ID (IN-MEMORY EXAMPLE)
    session_storage[session_token] = user.id 
    logger.debug(f"Stored session token {session_token[:8]}... for user ID {user.id} in SHARED session_storage.")

    # Determine redirect URL based on user role
    redirect_url = "/home"  # Default redirect
    if user.is_admin:
        redirect_url = "/admin-home.html" # Redirect admins here
        logger.info(f"User '{user.username}' is an admin, redirecting to {redirect_url}")
    else:
        logger.info(f"User '{user.username}' is not an admin, redirecting to {redirect_url}")

    # Create RedirectResponse first, then set the cookie on it
    # This response object will be returned by the function.
    redirect_response_obj = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    redirect_response_obj.set_cookie(
        key="session_token", value=session_token, httponly=True,
        secure=request.url.scheme == "https", samesite="lax", max_age=1800 
    )
    return redirect_response_obj
# --- Logout ---
@app.get("/logout", response_class=RedirectResponse, tags=["Auth"])
async def logout(response: Response, session_token: Annotated[str | None, Cookie()] = None):
    logger.info(f"Logout requested. Session token: {session_token[:8] if session_token else 'None'}")
    redirect_url = "/?message=Logged+out+successfully."
    
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    if session_token and session_token in session_storage: # !!! USE IMPORTED session_storage !!!
        try:
            del session_storage[session_token]
            logger.info(f"Removed session token {session_token[:8]}... from SHARED session_storage.")
        except KeyError:
            logger.warning(f"Session token {session_token[:8]}... was already removed during logout.")
    
    response.delete_cookie(key="session_token", httponly=True, samesite="lax") # Removed secure=False, let browser defaults work or match set_cookie
    logger.info("Logout cookie cleared.")
    return response


@app.get("/home", response_class=HTMLResponse, tags=["Pages"])
async def home(
    request: Request,
    # Use the cookie dependency to ensure user is logged in for this page
    current_user: User = Depends(require_user_from_cookie)
):
    """Serves the home page (home.html) for the logged-in user (requires cookie auth)."""
    logger.info(f"Serving home page for user '{current_user.username}' (ID: {current_user.id}) via cookie auth")
    # Pass necessary data to the template
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": current_user.id,
        "username": current_user.username,
        # Add other data needed by home.html template here, e.g.,
        # "is_admin": current_user.is_admin,
    })

# Place this near your other HTML serving routes (like the one for /home)
@app.get("/admin-home.html", response_class=HTMLResponse, tags=["Pages", "Admin"])
async def admin_home(
    request: Request,
    current_user: User = Depends(require_user_from_cookie) # Require login
):
    """Serves the admin home page (admin-home.html) for logged-in admins."""
    # Add an explicit check to ensure only admins can access this page directly
    if not current_user.is_admin:
        logger.warning(f"Non-admin user '{current_user.username}' attempted to access /admin-home.html. Redirecting to /home.")
        # Redirect non-admins to the regular home page or show an error
        return RedirectResponse(url="/home", status_code=303)

    logger.info(f"Serving admin home page for admin user '{current_user.username}' (ID: {current_user.id})")
    return templates.TemplateResponse("admin-home.html", {
        "request": request,
        "username": current_user.username,
        # Add any other data needed by admin-home.html
    })

@app.get("/register", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def register_page(
    request: Request,
    error: Optional[str] = None,
    username: Optional[str] = None, # For pre-filling form on error
    email: Optional[str] = None,    # For pre-filling form on error
    role: Optional[str] = None      # For pre-filling role on error
):
    """Serves the registration page (register.html)."""
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error": error,
            "username_val": username,
            "email_val": email,
            "role_val": role
        }
    )

@app.post("/register", response_class=RedirectResponse, tags=["Auth"])
async def register(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    role: Annotated[str, Form()], # Added role field
    db: Session = Depends(get_db)
):
    """Handles new user registration via HTML form submission."""
    logger.info(f"Registration attempt for username: {username}, email: {email}, role: {role}")

    # Prepare query parameters for potential redirect with error
    # This will also help repopulate the form
    error_redirect_params = {"username": username, "email": email}
    if role.lower() in ["student", "alumni", "admin"]:
        error_redirect_params["role"] = role


    db_user_username = db.query(User).filter(User.username == username).first()
    db_user_email = db.query(User).filter(User.email == email).first()

    error = None
    if db_user_username:
        error = "Username already registered"
    elif db_user_email:
        error = "Email already registered"
    elif len(password) < 8: # Assuming password length check is done on client, but good to have backend too
        error = "Password must be at least 8 characters long"
    elif role.lower() not in ["student", "alumni", "admin"]:
        error = "Invalid role selected."
        # Don't pass back invalid role for pre-selection
        if "role" in error_redirect_params:
            del error_redirect_params["role"]


    if error:
        logger.warning(f"Registration failed for '{username}': {error}")
        error_redirect_params["error"] = error
        query_params = urlencode(error_redirect_params)
        return RedirectResponse(url=f"/register?{query_params}", status_code=303)

    try:
        hashed_password_val = hash_password(password)

        is_student_val = (role.lower() == "student")
        is_alumni_val = (role.lower() == "alumni")
        is_admin_val = (role.lower() == "admin")

        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password_val,
            is_student=is_student_val,
            is_alumni=is_alumni_val,
            is_admin=is_admin_val
            # Other fields will use defaults from your User model
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User '{username}' (ID: {new_user.id}) registered successfully as {role}.")

        success_message = f"Registration as {role} successful. Welcome!"
        
        # Redirect based on role
        if role.lower() in ["student", "admin"]:
            # Redirect students and admins to the home page
            query_params = urlencode({"message": success_message})
            return RedirectResponse(url=f"/home?{query_params}", status_code=303)
        else: # Alumni (or any other valid role not explicitly redirected to home)
            # Redirect alumni to the login page with a success message
            query_params = urlencode({"message": "Registration successful. Please log in."})
            return RedirectResponse(url=f"/?{query_params}", status_code=303)

    except Exception as e:
        db.rollback()
        logger.error(f"Registration DB error for user '{username}': {e}", exc_info=True)
        error_redirect_params["error"] = "Registration failed due to a server error."
        query_params = urlencode(error_redirect_params)
        return RedirectResponse(url=f"/register?{query_params}", status_code=303)
# --- Password Reset Flow ---

@app.get("/forgot-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def forgot_password_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Serves the forgot password page (forgetpass.html)."""
    return templates.TemplateResponse("forgetpass.html", {"request": request, "error": error, "message": message})

@app.post("/forgot-password", tags=["Auth"]) # Response type depends on outcome
async def forgot_password(
    request: Request,
    email: Annotated[EmailStr, Form()], # Validate email format
    db: Session = Depends(get_db)
):
    """Handles the initial forgot password request (sends OTP email)."""
    logger.info(f"Forgot password request received for email: {email}")
    user = db.query(User).filter(User.email == email).first()
    # Generic message to prevent email enumeration attacks
    message_to_show = "If an account exists for this email, an OTP has been sent."

    if user:
        # Generate OTP and expiry
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=5) # Use UTC for consistency
        otp_storage[email] = {"otp": otp, "expiry": otp_expiry}
        logger.info(f"Generated OTP {otp} for email {email}, valid until {otp_expiry} UTC")

        # Attempt to send email
        email_sent = await send_otp_email(email, otp)
        if email_sent:
            logger.info(f"OTP email initiated successfully for {email}.")
            # Redirect to OTP verification page on successful email send
            query_params = urlencode({"email": email}) # Pass email to next step
            return RedirectResponse(url=f"/verify-otp?{query_params}", status_code=303)
        else:
            logger.error(f"Failed to send OTP email to {email}. User will see generic message.")
            # Clean up OTP if email failed to send
            if email in otp_storage:
                 del otp_storage[email]
            # Show an error message on the forgot password page itself
            return templates.TemplateResponse("forgetpass.html", {
                "request": request,
                "error": "Error sending OTP. Please try again later or contact support."
            })
    else:
        logger.warning(f"Forgot password request for non-existent email: {email}")
        # User doesn't exist, but show the generic message anyway
        return templates.TemplateResponse("forgetpass.html", {
            "request": request,
            "message": message_to_show
        })

@app.get("/verify-otp", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def verify_otp_page(request: Request, email: str, error: Optional[str] = None):
    """Serves the OTP verification page (otp.html)."""
    if not email:
         raise HTTPException(status_code=400, detail="Email parameter is missing.")
    return templates.TemplateResponse("otp.html", {"request": request, "email": email, "error": error})

@app.post("/verify-otp", response_class=RedirectResponse, tags=["Auth"])
async def verify_otp(
    request: Request,
    email: Annotated[EmailStr, Form()],
    otp_attempt: Annotated[str, Form()]
):
    """Verifies the submitted OTP."""
    logger.info(f"OTP verification attempt for email: {email} with OTP: '{otp_attempt}'")
    stored_otp_data = otp_storage.get(email)
    error_message = None

    if not stored_otp_data:
        error_message = "Invalid or expired OTP request. Please start again."
    elif datetime.utcnow() > stored_otp_data["expiry"]: # Use UTC for comparison
        error_message = "OTP has expired. Please request a new one."
        if email in otp_storage:
            del otp_storage[email] # Clean up expired entry
    elif otp_attempt != stored_otp_data["otp"]:
        error_message = "Invalid OTP entered."

    if error_message:
        logger.warning(f"OTP verification failed for {email}: {error_message}")
        query_params = urlencode({"email": email, "error": error_message})
        # Redirect back to OTP page with error
        return RedirectResponse(url=f"/verify-otp?{query_params}", status_code=303)
    else:
        # OTP is valid!
        logger.info(f"OTP verification successful for email {email}.")
        # Keep email in storage briefly to authorize reset page access? Or use signed token?
        # Simple approach: just redirect. Reset page must trust the email param.
        # Optionally delete immediately: del otp_storage[email]
        # Keep the OTP entry for now, reset password endpoint will clear it upon success.
        query_params = urlencode({"email": email}) # Pass email to reset page
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=303)

@app.get("/reset-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def reset_password_page(request: Request, email: str, error: Optional[str] = None):
    """Serves the final password reset page (reset.html)."""
    if not email:
         raise HTTPException(status_code=400, detail="Email parameter is missing.")
    # Optional: Add a check here if the email came from a valid OTP verification step
    # e.g., check if email is still in otp_storage and not expired.
    # if email not in otp_storage or datetime.utcnow() > otp_storage[email]["expiry"]:
    #     logger.warning(f"Unauthorized access attempt to reset password page for {email}")
    #     raise HTTPException(status_code=403, detail="Invalid reset request. Please verify OTP again.")
    return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": error})

@app.post("/reset-password", response_class=RedirectResponse, tags=["Auth"])
async def reset_password(
    request: Request,
    email: Annotated[EmailStr, Form()],
    new_password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    """Handles the final password reset submission."""
    logger.info(f"Password reset submission received for email: {email}")

    # Re-validate that this email is allowed to reset password
    # Check if a valid, non-expired OTP exists for this email.
    stored_otp_data = otp_storage.get(email)
    if not stored_otp_data or datetime.utcnow() > stored_otp_data["expiry"]:
        logger.warning(f"Attempt to reset password for {email} without a valid/recent OTP verification.")
        query_params = urlencode({"error": "Invalid or expired reset session. Please start the password reset process again."})
        # Redirect to the initial forgot password page or login page
        return RedirectResponse(url=f"/forgot-password?{query_params}", status_code=303)

    # Validate new password length
    if len(new_password) < 8:
        logger.warning(f"Password reset failed for {email}: Password too short.")
        query_params = urlencode({"email": email, "error": "Password must be at least 8 characters long."})
        # Redirect back to the reset page with the error
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=303)

    # Find the user again
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # This case should ideally not happen if OTP was verified, but handle defensively
        logger.error(f"Password reset failed: User with email {email} not found during final reset step, despite OTP verification.")
        # Clear OTP storage just in case
        if email in otp_storage:
            del otp_storage[email]
        query_params = urlencode({"error": "User not found. Please start the password reset process again."})
        return RedirectResponse(url=f"/forgot-password?{query_params}", status_code=303)

    try:
        # Hash the new password and update the user record
        hashed_password_val = hash_password(new_password)
        user.hashed_password = hashed_password_val
        user.updated_at = datetime.utcnow()
        db.commit()

        # Clean up OTP storage AFTER successful reset
        if email in otp_storage:
            del otp_storage[email]

        logger.info(f"Password successfully reset for user '{user.username}' (Email: {email}).")
        query_params = urlencode({"message": "Password reset successfully. Please log in with your new password."})
        # Redirect to the login page with a success message
        return RedirectResponse(url=f"/?{query_params}", status_code=303)
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset DB error for {email}: {e}", exc_info=True)
        query_params = urlencode({"email": email, "error": "Failed to reset password due to a server error."})
        # Redirect back to the reset page with error
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=303)

# --- Other HTML Page Serving Routes ---
# Add `Depends(require_user_from_cookie)` to pages that should only be accessed when logged in.

@app.get("/dailyspark.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_daily_spark(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("dailyspark.html", {"request": request, "username": user.username})

@app.get("/explore.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_explore(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("explore.html", {"request": request, "username": user.username})

@app.get("/career-fairs.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_career_fairs_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("career-fairs.html", {"request": request, "username": user.username})

@app.get("/expertqa.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_expertqa_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("expertqa.html", {"request": request, "username": user.username})

@app.get("/explore-hackathons.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_explore_hackathon_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("explore-hackathons.html", {"request": request, "username": user.username})

@app.get("/intership.html", response_class=HTMLResponse, tags=["Pages"]) # Assuming typo, should be internship.html?
async def serve_internship_html(request: Request, user: User = Depends(require_user_from_cookie)):
     # Make sure "intership.html" exists or change to "internship.html"
     return templates.TemplateResponse("intership.html", {"request": request, "username": user.username})

@app.get("/leader-profile.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_leader_profile_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("leader-profile.html", {"request": request, "username": user.username})

@app.get("/leaderboard.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_leaderboard_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("leaderboard.html", {"request": request, "username": user.username})

@app.get("/alumni-roadmaps.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_alumni_roadmap_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("alumni-roadmaps.html", {"request": request, "username": user.username})

@app.get("/chat.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_chat_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("chat.html", {"request": request, "username": user.username})

# Add these imports at the top of exp.py if not already present
import json
from datetime import date, datetime
from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
# Import your User model, UserResponse pydantic model, get_db, require_user_from_cookie, logger, templates
# e.g., from .models_sqlalchemy import User
# e.g., from .models_pydantic import UserResponse
# e.g., from .dependencies import get_db, require_user_from_cookie
# e.g., from .main import logger, templates # Adjust based on your project structure

# --- Define the JSON serializer helper function ---
# Place this somewhere accessible, e.g., near the top or just before serve_profile
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code, like datetime"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # Convert datetime/date to ISO 8601 string format
    raise TypeError(f"Type {type(obj)} not serializable")

# --- Modified serve_profile function ---
# --- Necessary Imports for Profile Functionality ---
import json
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import (
    Request,
    Depends,
    HTTPException,
    status,
    Body,
    FastAPI # Assuming 'app' instance is defined where this code is used
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field # Import pydantic components

# --- Project-Specific Imports (Ensure these paths are correct) ---
# Example: Adjust '.database', '.models_sqlalchemy', etc., to your structure

# --- Assume logger and templates are initialized (replace with your setup) ---
# Or your specific logger
# Configure logging if not done elsewhere
# logging.basicConfig(level=logging.INFO)

# Ensure the templates directory path is correct
templates = Jinja2Templates(directory="frontend-exp")

# --- Pydantic Models for Profile Data ---

# Assumed Pydantic model for returning user data (used by both GET and PUT)
# Make sure this is defined or imported correctly


# --- Helper Function for JSON Serialization ---
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code, like datetime"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable by json_serial helper")

# --- FastAPI Application Instance (ensure this is defined) ---
# Example: app = FastAPI()

# --- Profile Page Route (GET Request) ---
@app.get("/profile.html", response_class=HTMLResponse, tags=["Pages"], include_in_schema=False)
async def serve_profile(
    request: Request,
    username: Optional[str] = None, # Username from query param (e.g., /profile.html?username=testuser)
    db: Session = Depends(get_db),
    viewer_user: User = Depends(require_user_from_cookie) # Ensures viewer is logged in
):
    """
    Serves the profile page HTML. Determines which profile to show based on the
    optional 'username' query parameter or defaults to the logged-in user.
    """
    target_username: str
    user_to_view: User | None = None

    if username is None:
        user_to_view = viewer_user
        target_username = viewer_user.username
        logger.info(f"Viewer '{viewer_user.username}' requesting their own profile page.")
    else:
        target_username = username
        logger.info(f"Viewer '{viewer_user.username}' requesting profile page for user '{target_username}'.")
        user_to_view = db.query(User).filter(User.username == target_username).first()
        if not user_to_view:
            logger.warning(f"Profile requested for non-existent user: '{target_username}'")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{target_username}' not found")

    profile_data_json_str: str | None = None
    try:
        # Validate data structure using Pydantic model before sending to template
        profile_data_validated = UserResponse.model_validate(user_to_view)
        profile_data_dict = profile_data_validated.model_dump()

        # Serialize the dictionary to a JSON string, handling dates
        profile_data_json_str = json.dumps(profile_data_dict, default=json_serial)
        logger.debug(f"Successfully serialized profile data for {target_username}")

    except Exception as e:
        logger.error(f"Error preparing/serializing profile data for user '{target_username}' (ID: {user_to_view.id}): {e}", exc_info=True)
        # Optionally render a generic error template instead of raising 500 for HTML page
        # return templates.TemplateResponse("error.html", {"request": request, "detail": "Could not load profile data."}, status_code=500)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error preparing profile data.")

    is_own_profile = (viewer_user.id == user_to_view.id)
    logger.info(f"Profile view check: is_own_profile={is_own_profile} for user '{target_username}' viewed by '{viewer_user.username}'")

    context = {
        "request": request,
        "profile_user_id": user_to_view.id,
        "profile_username": user_to_view.username,
        "profile_data_json": profile_data_json_str, # Pre-serialized JSON string
        "is_own_profile": is_own_profile,
        "viewer_username": viewer_user.username
    }

    return templates.TemplateResponse("profile.html", context)


# --- Profile Update API Route (PUT Request) ---
@app.put(
    "/api/users/me", # Endpoint for the logged-in user to update their own profile
    response_model=UserResponse, # Return the updated user data structure
    tags=["Users", "API"]
)
async def update_user_profile(
    *, # Enforce keyword-only arguments after this
    db: Session = Depends(get_db),
    updated_data: UserProfileUpdate = Body(...), # Data from request body, validated
    current_user: User = Depends(require_user_from_cookie) # Get the logged-in user model instance
):
    """
    Updates profile fields for the currently authenticated user based on provided data.
    """
    logger.info(f"User '{current_user.username}' (ID: {current_user.id}) attempting profile update.")

    # Get dictionary of fields actually provided in the request
    update_data_dict = updated_data.model_dump(exclude_unset=True)

    if not update_data_dict:
         logger.warning(f"User '{current_user.username}' submitted an empty profile update request.")
         # Return current data without changes if nothing was submitted
         return current_user

    logger.debug(f"Updating fields for user '{current_user.username}': {list(update_data_dict.keys())}")

    updated_fields_count = 0
    # Apply updates to the SQLAlchemy model instance
    for key, value in update_data_dict.items():
        if hasattr(current_user, key):
            # Only update if the attribute exists on the User model
            setattr(current_user, key, value)
            updated_fields_count += 1
        else:
            logger.warning(f"Attempted to update non-existent or non-allowed field '{key}' for user '{current_user.username}'")

    if updated_fields_count == 0:
         logger.info(f"No valid fields provided to update for user '{current_user.username}'.")
         return current_user # Return current state

    try:
        # Explicitly set updated_at timestamp (if model doesn't auto-update)
        current_user.updated_at = datetime.utcnow()

        db.add(current_user) # Stage changes (often tracked automatically, but safe to add)
        db.commit() # Save changes to the database
        db.refresh(current_user) # Load any DB-generated changes back into the object
        logger.info(f"Successfully updated profile for user '{current_user.username}'.")

        # Return the updated user data, automatically validated against UserResponse
        return current_user
    except Exception as e:
        db.rollback() # Roll back transaction on error
        logger.error(f"Database error updating profile for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile due to a server error."
        )

# --- End of Profile Specific Backend Code ---

# Find this route in your exp.py
# @app.get("/connection.html", response_class=HTMLResponse, tags=["Pages"]) # OLD
# async def serve_connections(request: Request, user: User = Depends(require_user_from_cookie)):
#      return templates.TemplateResponse("connection.html", {"request": request, "username": user.username})

# Change it to:
@app.get("/connection.html", response_class=HTMLResponse, tags=["Pages"]) # <<< RENAMED ROUTE
async def serve_connections_html( # Optional: Rename function for clarity
    request: Request,
    user: User = Depends(require_user_from_cookie)
):
     # Ensure the template file is also named "connections.html"
     return templates.TemplateResponse("connection.html", {"request": request, "username": user.username})
@app.get("/notifications.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_notifications_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("notifications.html", {"request": request, "username": user.username})

@app.get("/help.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_help_html(request: Request): # Help page might be accessible without login
     # If login is required: user: User = Depends(require_user_from_cookie)
     return templates.TemplateResponse("help.html", {"request": request})


# --- API Endpoints ---
BASE_API_PATH = "/api"

# --- User API ---

@app.get(f"{BASE_API_PATH}/users/me", response_model=UserResponse, tags=["Users", "API"])
async def read_users_me_cookie(
    current_user: User = Depends(require_user_from_cookie) # Use cookie auth for browser JS calls
):
    """Gets the profile data for the currently authenticated user (identified via session cookie)."""
    logger.info(f"API request for /users/me by user '{current_user.username}' (cookie auth)")
    # Pydantic automatically validates the returned current_user against UserResponse
    return current_user

# New public endpoint to get current user profile without Basic Auth for frontend use
@app.get(f"{BASE_API_PATH}/users/current", response_model=UserResponse, tags=["Users", "API"])
async def read_current_user_profile(
    current_user: User = Depends(require_user_from_cookie)
):
    """Gets the profile data for the currently authenticated user (cookie auth), public for frontend."""
    logger.info(f"API request for /users/current by user '{current_user.username}' (cookie auth)")
    return current_user

@app.get(f"{BASE_API_PATH}/users/{{username}}", response_model=UserResponse, tags=["Users", "API"])
async def read_user_profile(
    username: str,
    db: Session = Depends(get_db),
    # Use Basic Auth for this, assuming it might be called by other services/scripts
    # Or could use cookie auth if it's only called by the frontend for other profiles
    requesting_user: User = Depends(get_current_user) # Requires Basic Auth header
):
    """Gets the public profile of a specific user by username (requires Basic API auth)."""
    logger.info(f"API request for profile of '{username}' by user '{requesting_user.username}' (Basic auth)")
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Pydantic validates the returned db_user against UserResponse
    return db_user

@app.get(f"{BASE_API_PATH}/public/users/{{username}}", response_model=UserResponse, tags=["Users", "API"])
async def read_user_profile_public(
    username: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_from_cookie) # Optional cookie auth
):
    """Gets the public profile of a specific user by username without requiring Basic Auth."""
    logger.info(f"Public API request for profile of '{username}' by user '{current_user.username if current_user else 'anonymous'}'")
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Return user data, possibly filter sensitive info if needed
    return db_user

@app.put(f"{BASE_API_PATH}/users/me", response_model=UserResponse, tags=["Users", "API"])
async def update_user_profile(
    user_update: UserUpdate, # Request body validated against UserUpdate model
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Use cookie auth to identify user
):
    """Updates the profile of the currently authenticated user (identified via session cookie)."""
    logger.info(f"API request to update profile for user '{current_user.username}' (cookie auth)")

    # Get update data, excluding fields that were not sent in the request
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated_fields_count = 0
    for key, value in update_data.items():
        # Check if the attribute exists on the User model to prevent errors
        if hasattr(current_user, key):
            setattr(current_user, key, value)
            updated_fields_count += 1
        else:
            # Log a warning if the request tries to update a field not in the model
            logger.warning(f"Attempted to update non-existent attribute '{key}' for user '{current_user.username}'")

    if updated_fields_count == 0:
        # This might happen if only non-existent fields were provided
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    try:
        # Update the 'updated_at' timestamp
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user) # Refresh to get updated data from DB if needed
        logger.info(f"Profile updated successfully for user '{current_user.username}'")
        return current_user # Return updated user data, validated by UserResponse
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile DB error for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update profile")

# --- Chat API ---

@app.get(f"{BASE_API_PATH}/contacts", response_model=List[ChatContactOut], tags=["Chat", "API"])
async def get_chat_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login via cookie
):
    """Gets chat contacts (requires cookie auth). Needs logic for user-specific contacts."""
    logger.info(f"API request by '{current_user.username}' for chat contacts.")
    # TODO: Implement logic to get contacts relevant ONLY to the current_user
    # This example fetches first 50 global contacts, which is likely not correct.
    # You might need a linking table (e.g., UserChatAccess) or specific logic.
    contacts = db.query(ChatContact).limit(50).all() # EXAMPLE - REPLACE WITH REAL LOGIC
    return contacts # Pydantic validates against List[ChatContactOut]

# Add near other Chat API endpoints
from fastapi import UploadFile, File

@app.post(f"{BASE_API_PATH}/upload-file", tags=["Chat"])
async def upload_chat_file(
    # contact_id: Annotated[int, Form()], # Get contact ID from form data if needed
    file: UploadFile = File(...),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"File upload request received from {current_user.username}: {file.filename}")
    # VERY IMPORTANT: Add security checks here!
    # - Check file type (e.g., only allow images/PDFs)
    # - Check file size
    # - Sanitize filename to prevent path traversal attacks
    # - Save the file securely to a designated uploads directory (NOT static)
    # - Record the file path in the ChatMessage database entry

    # Example (Simplified - NEEDS PROPER SECURITY):
    upload_dir = os.path.join(BASE_DIR, "uploads") # Create this directory
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = secrets.token_hex(8) + "_" + file.filename # Basic sanitization
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        logger.info(f"File saved: {file_path}")
        # You would typically return the path or related message ID
        return {"filename": safe_filename, "detail": "File uploaded successfully"}
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed.")

# --- Add these new endpoints ---

@app.post(f"{BASE_API_PATH}/connections/request/{{target_username}}", status_code=status.HTTP_201_CREATED, tags=["Connections"])
async def send_connection_request(
    target_username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    # ... (Implementation from previous detailed backend response) ...
    logger.info(f"User '{current_user.username}' sending request to '{target_username}'.")
    if current_user.username == target_username: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot request yourself.")
    target_user_db = db.query(User).filter(User.username == target_username).first()
    if not target_user_db: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")
    existing = db.query(UserConnection).filter(or_(and_(UserConnection.requester_id == current_user.id, UserConnection.receiver_id == target_user_db.id), and_(UserConnection.requester_id == target_user_db.id, UserConnection.receiver_id == current_user.id))).first()
    if existing:
        if existing.status == 'accepted': raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already connected.")
        if existing.status == 'pending':
            if existing.requester_id == current_user.id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already sent.")
            else: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user sent you a request. Check pending.")
    req = UserConnection(requester_id=current_user.id, receiver_id=target_user_db.id, status='pending')
    try:
        db.add(req); create_notification(db, target_user_db.id, f"{current_user.username} sent you a connection request.", "connection_request", current_user.id); db.commit()
        return {"message": "Connection request sent."}
    except Exception as e: db.rollback(); logger.error(f"Err send conn req: {e}", exc_info=True); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not send request.")
@app.get(f"{BASE_API_PATH}/connections/requests/pending", response_model=List[PendingRequestOut], tags=["Connections"])
async def get_my_pending_requests(db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous detailed backend response) ...
    logger.info(f"User '{current_user.username}' fetching pending requests.")
    reqs_orm = db.query(UserConnection).filter(UserConnection.receiver_id == current_user.id, UserConnection.status == 'pending').options(selectinload(UserConnection.requester)).order_by(desc(UserConnection.created_at)).all()
    data = []
    for r in reqs_orm:
        if r.requester: data.append(PendingRequestOut(requester_id=r.requester.id, requester_username=r.requester.username, requester_profession=r.requester.profession, requested_at=r.created_at))
    return data

@app.post(f"{BASE_API_PATH}/connections/requests/accept/{{requester_id}}", tags=["Connections"])
async def accept_connection_request(requester_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous detailed backend response, including Almagems logic) ...
    logger.info(f"User '{current_user.username}' accepting request from user ID {requester_id}.")
    req = db.query(UserConnection).filter(UserConnection.requester_id == requester_id, UserConnection.receiver_id == current_user.id, UserConnection.status == 'pending').first()
    if not req: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    req_user = db.query(User).filter(User.id == requester_id).first()
    if not req_user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requesting user not found.")
    req.status = 'accepted'; req.updated_at = datetime.utcnow()
    current_user.alumni_gems = (current_user.alumni_gems or 0) + 5
    req_user.alumni_gems = (req_user.alumni_gems or 0) + 5
    try:
        db.add_all([current_user, req_user, req]); create_notification(db, requester_id, f"{current_user.username} accepted your request.", "connection_accepted", current_user.id); db.commit()
        return {"message": "Request accepted. Almagems awarded!"}
    except Exception as e: db.rollback(); logger.error(f"Err accept req: {e}", exc_info=True); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not accept request.")

@app.post(f"{BASE_API_PATH}/connections/requests/ignore/{{requester_id}}", tags=["Connections"])
async def ignore_connection_request(requester_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous detailed backend response) ...
    logger.info(f"User '{current_user.username}' ignoring request from user ID {requester_id}.")
    req = db.query(UserConnection).filter(UserConnection.requester_id == requester_id, UserConnection.receiver_id == current_user.id, UserConnection.status == 'pending').first()
    if not req: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    req.status = 'ignored'; req.updated_at = datetime.utcnow()
    try: db.commit(); return {"message": "Request ignored."}
    except Exception as e: db.rollback(); logger.error(f"Err ignore req: {e}", exc_info=True); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not ignore request.")


@app.delete(f"{BASE_API_PATH}/connections/{{connected_username_to_remove}}", status_code=status.HTTP_200_OK, tags=["Connections"])
async def remove_connection(connected_username_to_remove: str, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous detailed backend response) ...
    logger.info(f"User '{current_user.username}' removing connection with '{connected_username_to_remove}'.")
    user_to_remove = db.query(User).filter(User.username == connected_username_to_remove).first()
    if not user_to_remove: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to remove not found.")
    conn_rec = db.query(UserConnection).filter(UserConnection.status == 'accepted', or_(and_(UserConnection.requester_id == current_user.id, UserConnection.receiver_id == user_to_remove.id), and_(UserConnection.requester_id == user_to_remove.id, UserConnection.receiver_id == current_user.id))).first()
    if not conn_rec: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")
    try: db.delete(conn_rec); db.commit(); return {"message": "Connection removed."}
    except Exception as e: db.rollback(); logger.error(f"Err remove conn: {e}", exc_info=True); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not remove connection.")


@app.get(f"{BASE_API_PATH}/users/{{username}}/connections", response_model=List[ConnectionUser], tags=["Users", "Connections"])
async def get_user_connections_api(username: str, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie) ):
    # ... (Implementation from previous response, ensuring it returns List[ConnectionUser]) ...
    logger.info(f"API request for ACCEPTED connections of user '{username}' by '{current_user.username}'.")
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    try:
        # Get IDs of connected users first
        # Users who sent a request TO target_user (target_user is receiver)
        requester_user_ids_tuples = db.query(UserConnection.requester_id).filter(
            UserConnection.receiver_id == target_user.id,
            UserConnection.status == 'accepted'
        ).all() # Returns list of tuples: [(id1,), (id2,)]

        # Users to whom target_user sent a request (target_user is requester)
        receiver_user_ids_tuples = db.query(UserConnection.receiver_id).filter(
            UserConnection.requester_id == target_user.id,
            UserConnection.status == 'accepted'
        ).all() # Returns list of tuples: [(id3,), (id4,)]

        # Flatten the list of IDs from tuples
        all_connected_ids = [id_val for id_tuple in requester_user_ids_tuples for id_val in id_tuple] + \
                            [id_val for id_tuple in receiver_user_ids_tuples for id_val in id_tuple]
        
        unique_connected_ids = list(set(all_connected_ids)) # Get unique IDs

        if not unique_connected_ids:
            logger.info(f"No connected user IDs found for {username}.")
            return [] # Return empty list if no connections

        logger.info(f"Fetching User objects for IDs: {unique_connected_ids} for target user {username}")
        # Now fetch the User ORM objects for these unique IDs
        unique_users_orm = db.query(User).filter(User.id.in_(unique_connected_ids)).all()
        
        logger.info(f"Found {len(unique_users_orm)} unique User ORM objects for {username}.")
        for u_idx, u_val in enumerate(unique_users_orm):
            logger.debug(f"  Final User {u_idx}: ID={u_val.id}, Username={u_val.username if hasattr(u_val, 'username') else 'NO_USERNAME_ATTR'}, Profession={u_val.profession if hasattr(u_val, 'profession') else 'NO_PROFESSION_ATTR'}")

        connection_user_adapter = TypeAdapter(List[ConnectionUser])
        return connection_user_adapter.validate_python(unique_users_orm)

    except Exception as e:
        logger.error(f"Error fetching accepted connections for user '{username}' (using simplified query): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve connections.")
@app.get(f"{BASE_API_PATH}/users/{{username}}/suggestions", response_model=List[ConnectionUser], tags=["Users", "Connections"])
async def get_connection_suggestions_api(username: str, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous response, ensuring it returns List[ConnectionUser] and excludes correctly) ...
    logger.info(f"API request for connection suggestions for user '{username}' by '{current_user.username}'.")
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")
    try:
        related_ids_as_requester = db.query(UserConnection.receiver_id).filter(UserConnection.requester_id == target_user.id)
        related_ids_as_receiver = db.query(UserConnection.requester_id).filter(UserConnection.receiver_id == target_user.id)
        exclude_ids = {target_user.id}
        for id_val, in related_ids_as_requester.all(): exclude_ids.add(id_val)
        for id_val, in related_ids_as_receiver.all(): exclude_ids.add(id_val)
        
        suggestions_orm = db.query(User).filter(not_(User.id.in_(list(exclude_ids)))).order_by(func.random()).limit(limit).all()
        connection_user_adapter = TypeAdapter(List[ConnectionUser])
        return connection_user_adapter.validate_python(suggestions_orm)
    except Exception as e: # ... error handling ...
        logger.error(f"Error fetching suggestions for '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve suggestions.")
    

@app.get(f"{BASE_API_PATH}/users/searchable", response_model=List[ConnectionUser], tags=["Users", "Connections"])
async def search_connectable_users(term: str, db: Session = Depends(get_db), current_user: User = Depends(require_user_from_cookie)):
    # ... (Implementation from previous response, ensuring it returns List[ConnectionUser] and excludes correctly) ...
    logger.info(f"User '{current_user.username}' searching for connectable users with term: '{term}'.")
    if not term or len(term.strip()) < 2: return []
    search_term_like = f"%{term.strip().lower()}%"
    
    related_ids_as_requester = db.query(UserConnection.receiver_id).filter(UserConnection.requester_id == current_user.id)
    related_ids_as_receiver = db.query(UserConnection.requester_id).filter(UserConnection.receiver_id == current_user.id)
    exclude_ids = {current_user.id}
    for id_val, in related_ids_as_requester.all(): exclude_ids.add(id_val)
    for id_val, in related_ids_as_receiver.all(): exclude_ids.add(id_val)

    search_results_orm = db.query(User).filter(User.username.ilike(search_term_like)).filter(not_(User.id.in_(list(exclude_ids)))).limit(10).all()
    connection_user_adapter = TypeAdapter(List[ConnectionUser])
    return connection_user_adapter.validate_python(search_results_orm)

# Optional Chat Session Endpoint
# exp.py
# ... (all other imports, models, Pydantic schemas, etc.) ...

BASE_API_PATH = "/api" # Ensure this is defined

# --- Chat API Endpoints ---

# ***** ROUTE ORDER IS CRITICAL *****
# 1. Most specific static routes first
@app.get(f"{BASE_API_PATH}/chat/my-contacts", response_model=List[ChatContactInfo], tags=["Chat", "API"])
async def get_my_chat_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    # ... (your existing implementation for get_my_chat_contacts - THIS IS FINE)
    logger.info(f"[API_MY_CONTACTS] User '{current_user.username}' (ID: {current_user.id}) fetching their chat contacts.")
    all_user_pair_contacts = db.query(ChatContact)\
                               .filter(ChatContact.name.like(f"chat_users_%"))\
                               .order_by(desc(ChatContact.updated_at)).all()
    my_contacts_info: List[ChatContactInfo] = []
    processed_contact_ids = set()
    for contact in all_user_pair_contacts:
        if contact.id in processed_contact_ids: continue
        if contact.name and contact.name.startswith("chat_users_"):
            try:
                parts = contact.name.split('_')
                if len(parts) == 4:
                    user_id1 = int(parts[2]); user_id2 = int(parts[3])
                    other_user_id = user_id2 if current_user.id == user_id1 else (user_id1 if current_user.id == user_id2 else None)
                    if other_user_id is None: continue
                    other_user = db.query(User).filter(User.id == other_user_id).first()
                    if other_user:
                        my_contacts_info.append(ChatContactInfo(
                            contact_id=contact.id,
                            other_user_username=other_user.username,
                            other_user_id=other_user.id
                        ))
                        processed_contact_ids.add(contact.id)
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse contact name '{contact.name}' for my-contacts list: {e}")
                continue
    logger.info(f"[API_MY_CONTACTS] Returning {len(my_contacts_info)} contacts for user '{current_user.username}'.")
    return my_contacts_info

# 2. Routes with specific path structures but still somewhat static parts
@app.get(
    f"{BASE_API_PATH}/chat/session/with/{{target_username:str}}", # Explicitly type target_username as string
    response_model=ChatSessionResponse,
    tags=["Chat", "API"],
    summary="Get or create a 1-on-1 chat session ID"
)
async def get_or_create_chat_session(
    target_username: str, # FastAPI will use the :str from path
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    # ... (your existing implementation - THIS IS FINE) ...
    logger.info(f"[API_CHAT_SESSION] User '{current_user.username}' (ID: {current_user.id}) requesting chat session with '{target_username}'.")
    if target_username == current_user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot start a chat session with yourself.")
    target_user = db.query(User).filter(User.username == target_username).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{target_username}' not found.")
    user_ids = sorted([current_user.id, target_user.id])
    chat_contact_name = f"chat_users_{user_ids[0]}_{user_ids[1]}"
    logger.debug(f"[API_CHAT_SESSION] Calculated chat contact name: {chat_contact_name}")
    try:
        chat_contact = db.query(ChatContact).filter(ChatContact.name == chat_contact_name).first()
        if chat_contact:
            return ChatSessionResponse(chat_id=chat_contact.id)
        else:
            new_chat_contact = ChatContact(name=chat_contact_name)
            db.add(new_chat_contact)
            db.commit(); db.refresh(new_chat_contact)
            return ChatSessionResponse(chat_id=new_chat_contact.id)
    except Exception as e:
        db.rollback()
        logger.error(f"[API_CHAT_SESSION] DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error creating chat session.")


# 3. More general routes with path parameters, especially integer ones, LAST among GETs with same prefix
@app.get(f"{BASE_API_PATH}/chat/{{contact_id:int}}", response_model=List[ChatMessageOut], tags=["Chat", "API"]) # Explicitly type contact_id as int
async def get_chat_messages(
    contact_id: int, # FastAPI will use the :int from path and validate
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    # ... (your existing implementation with security check - THIS IS FINE)
    logger.info(f"[API_GET_MESSAGES] User '{current_user.username}' requesting messages for contact_id: {contact_id}")
    contact = db.query(ChatContact).filter(ChatContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat contact not found")
    # --- SECURITY CHECK ---
    if contact.name and contact.name.startswith("chat_users_"):
        try:
            parts = contact.name.split('_');
            if len(parts) == 4:
                user_id1 = int(parts[2]); user_id2 = int(parts[3])
                if current_user.id not in [user_id1, user_id2]:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not have access to this chat.")
            else: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Chat participation unclear (name format).")
        except: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Chat participation error (parsing).")
    else: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Cannot determine participation in this chat type.")
    # --- END SECURITY CHECK ---
    messages = db.query(ChatMessage).filter(ChatMessage.contact_id == contact_id).order_by(ChatMessage.timestamp.asc()).limit(200).all()
    return messages


@app.post(f"{BASE_API_PATH}/send-message", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED, tags=["Chat", "API"])
async def send_message_api(
    message_data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    # ... (your existing implementation with security check - THIS IS FINE)
    logger.info(f"[API_SEND_MESSAGE] User '{current_user.username}' sending to contact_id: {message_data.contact_id}")
    if not message_data.text or not message_data.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message text cannot be empty")
    contact = db.query(ChatContact).filter(ChatContact.id == message_data.contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat contact not found")
    # --- SECURITY CHECK ---
    if contact.name and contact.name.startswith("chat_users_"):
        try:
            parts = contact.name.split('_');
            if len(parts) == 4:
                user_id1 = int(parts[2]); user_id2 = int(parts[3])
                if current_user.id not in [user_id1, user_id2]:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot send messages to this chat.")
            else: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Chat participation unclear (name format for send).")
        except: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Chat participation error (parsing for send).")
    else: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Cannot determine participation for sending.")
    # --- END SECURITY CHECK ---
    db_message = ChatMessage(contact_id=message_data.contact_id, sender=current_user.username, text=message_data.text.strip(), timestamp=datetime.utcnow())
    try:
        db.add(db_message); db.commit(); db.refresh(db_message)
        return db_message
    except Exception as e:
        db.rollback(); logger.error(f"[API_SEND_MESSAGE] DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not send message.")

# ... (rest of your FastAPI app routes and main execution block)

# --- Leaderboard/Alumni API ---



@app.get(f"{BASE_API_PATH}/alumni", response_model=List[AlumniResponse], tags=["Alumni", "API"])
async def get_all_alumni(db: Session = Depends(get_db)):
    """
    Gets a list of all users marked as alumni, ordered by username.
    This is used specifically for the Alumni Roadmaps page initial load.
    """
    logger.info("API request for ALL alumni list (for Roadmaps page).")
    try:
        # Fetch all users where is_alumni is true
        alumni_list = db.query(User)\
            .filter(User.is_alumni == True)\
            .order_by(User.username.asc()).all() # Order alphabetically by default

        # Pydantic automatically validates the list against List[AlumniResponse]
        # Ensure AlumniResponse includes needed fields (id, username, profession, likes, department)
        return alumni_list
    except Exception as e:
        logger.error(f"Error fetching all alumni data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching alumni list")



@app.get(f"{BASE_API_PATH}/leaderboard", tags=["Users", "Alumni", "API"])
async def get_leaderboard(db: Session = Depends(get_db)):
    """Retrieves the user leaderboard (top alumni based on score/gems). Public endpoint."""
    logger.info("API request for leaderboard.")
    try:
        users = db.query(User)\
            .filter(User.is_alumni == True)\
            .order_by(User.activity_score.desc(), User.alumni_gems.desc())\
            .limit(100).all() # Limit leaderboard size
        # Pydantic validates each user against AlumniResponse
        return users
    except Exception as e:
        logger.error(f"Error fetching leaderboard data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching leaderboard")


@app.get(f"{BASE_API_PATH}/alumni/top-liked", tags=["Alumni", "API"])
async def get_top_liked_alumni(limit: int = 5, db: Session = Depends(get_db)):
    """Gets the top N liked alumni, grouped by department. Public endpoint."""
    logger.info(f"API request for top {limit} liked alumni, grouped by department.")
    try:
        # Fetch top N liked alumni overall
        top_alumni_db = db.query(User)\
            .filter(User.is_alumni == True)\
            .order_by(desc(User.likes))\
            .limit(limit * 5).all()

        # Group using validated AlumniResponse objects
        grouped_alumni_dict: Dict[str, List[AlumniResponse]] = {}
        count = 0
        processed_ids = set()

        for alumni_db in top_alumni_db:
            if count >= limit: # Limit the total number returned
                 break
            if alumni_db.id in processed_ids: # Avoid duplicates if fetched more
                 continue

            try:
                # Validate each alumni object individually
                alumni_resp = AlumniResponse.model_validate(alumni_db)
                department_key = alumni_resp.department if alumni_resp.department else "Other" # Group None departments

                if department_key not in grouped_alumni_dict:
                    grouped_alumni_dict[department_key] = []

                # Add to group if limit per group not reached (optional) or just add to overall list
                # Here we just add, relying on the overall limit 'limit'
                grouped_alumni_dict[department_key].append(alumni_resp)
                processed_ids.add(alumni_db.id)
                count += 1

            except Exception as inner_e:
                # Log validation error for a specific alumni but continue processing others
                logger.error(f"Pydantic validation error on individual AlumniResponse ID {alumni_db.id} during top-liked grouping: {inner_e}", exc_info=False) # Reduce noise?
                # Optionally skip the invalid record or handle differently

        # Pydantic/FastAPI validates the final Dict[str, List[AlumniResponse]] structure
        return grouped_alumni_dict

    except Exception as e:
        logger.error(f"Error fetching/grouping top liked alumni: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching alumni data")


@app.get(f"{BASE_API_PATH}/alumni/{{alumni_id}}", response_model=AlumniResponse, tags=["Alumni", "API"])
async def get_alumni_by_id(
    alumni_id: int,
    db: Session = Depends(get_db),
    # Requires authentication (via cookie) to view specific alumni profile via API
    current_user: User = Depends(require_user_from_cookie)
):
    """Gets details for a specific alumnus by ID (requires cookie auth)."""
    logger.info(f"API request by {current_user.username} for alumni details ID: {alumni_id}")
    alumnus = db.query(User).filter(
        User.id == alumni_id,
        User.is_alumni == True # Ensure the user is actually an alumnus
    ).first()

    if not alumnus:
        raise HTTPException(status_code=404, detail="Alumnus not found")

    # Pydantic validates the result against AlumniResponse
    return alumnus

# --- Find and replace the existing like_alumnus function ---

@app.post(f"{BASE_API_PATH}/alumni/{{alumni_id}}/like", status_code=200, tags=["Alumni", "API"])
async def like_alumnus(
    alumni_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie) to like
):
    """
    Adds a like from the current user to a specific alumnus, if not already liked.
    Increments the like count on the User model.
    """
    logger.info(f"API request by '{current_user.username}' (ID: {current_user.id}) to like alumnus ID {alumni_id}.")

    # --- Validation ---
    if alumni_id == current_user.id:
        logger.warning(f"User '{current_user.username}' attempted to like their own profile (ID: {alumni_id}).")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot like your own profile.")

    # Find the alumnus profile being liked
    alumnus = db.query(User).filter(User.id == alumni_id, User.is_alumni == True).first()
    if not alumnus:
        logger.warning(f"Like attempt failed: Alumnus with ID {alumni_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumnus profile not found.")

    # --- Check if already liked ---
    existing_like = db.query(AlumniLike).filter(
        AlumniLike.liker_user_id == current_user.id,
        AlumniLike.liked_alumni_id == alumni_id
    ).first()

    if existing_like:
        logger.info(f"User '{current_user.username}' has already liked alumnus ID {alumni_id}. No action taken.")
        # Return current like count, indicate no change
        return {"likes": alumnus.likes, "message": "Already liked.", "liked": True}

    # --- Process New Like ---
    try:
        # 1. Create the tracking record
        new_like = AlumniLike(
            liker_user_id=current_user.id,
            liked_alumni_id=alumni_id
        )
        db.add(new_like)

        # 2. Increment the counter on the User model
        alumnus.likes = (alumnus.likes or 0) + 1
        # No need to db.add(alumnus) if it's already tracked by the session

        # 3. Commit transaction
        db.commit()
        db.refresh(alumnus) # Refresh to get the final like count

        logger.info(f"User '{current_user.username}' successfully liked alumnus ID {alumni_id}. New count: {alumnus.likes}")
        # Return the new like count and success status
        return {"likes": alumnus.likes, "message": "Like recorded.", "liked": True}

    except Exception as e:
        db.rollback() # Rollback BOTH the like increment and the tracking record attempt
        logger.error(f"Like alumnus DB error for ID {alumni_id} by user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update like count due to server error.")
    
# --- Add this new endpoint in exp.py ---

@app.get(f"{BASE_API_PATH}/alumni/me/liked", response_model=List[int], tags=["Alumni", "API"])
async def get_my_liked_alumni_ids(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login
):
    """Gets a list of Alumni IDs that the current user has liked."""
    logger.info(f"API request by {current_user.username} for their liked alumni IDs.")
    try:
        liked_ids = db.query(AlumniLike.liked_alumni_id)\
                      .filter(AlumniLike.liker_user_id == current_user.id)\
                      .all()
        # The query returns tuples like [(1,), (5,), (12,)], extract the integers
        return [item[0] for item in liked_ids]
    except Exception as e:
        logger.error(f"Error fetching liked alumni IDs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve liked alumni.")
# --- Expert Q&A API ---

@app.get("/api/questions/popular", response_model=List[QuestionOut], tags=["Questions", "API"])
async def get_popular_questions(db: Session = Depends(get_db)):
    popular_questions = db.query(Question)\
        .options(
            selectinload(Question.user),  # For asker's username
            selectinload(Question.expert_answers).selectinload(ExpertQAAnswer.user) # FOR EXPERT ANSWERER'S USERNAME
        )\
        .order_by(desc(Question.likes)) .limit(10).all() # Assuming Question model is imported

    if not popular_questions:
        return []
    return popular_questions


@app.post(f"{BASE_API_PATH}/questions", response_model=QuestionOut, status_code=201, tags=["Expert Q&A", "API"])
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Require login to post
):
    """Creates a new question in the Expert Q&A section."""
    logger.info(f"API POST /questions by '{current_user.username}'")
    db_question = Question(question_text=question.question_text, user_id=current_user.id)
    try:
        db.add(db_question); db.commit(); db.refresh(db_question)
        # Eagerly load answers (empty list) for the response model
        db_question.expert_answers = []
        return db_question
    except Exception as e: db.rollback(); logger.error(f"Create question DB error: {e}", exc_info=True); raise HTTPException(status_code=500, detail="DB error")

@app.get(f"{BASE_API_PATH}/users/{{username}}/questions", response_model=List[QuestionOut], tags=["Expert Q&A", "Users", "API"])
async def get_user_questions(
    username: str,
    db: Session = Depends(get_db),
    # Authentication depends on whether questions are public or private
    # Assuming public for now, no auth dependency needed.
    # If private: current_user: User = Depends(require_user_from_cookie) and add access check
):
    """Gets all questions asked by a specific user. Public endpoint."""
    logger.info(f"API request for questions asked by user '{username}'.")
    # Find the user first
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch questions linked to this user
    try:
        questions = db.query(Question)\
            .filter(Question.user_id == user.id)\
            .order_by(desc(Question.created_at)).all()
        # Pydantic validates against List[QuestionOut]
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions for user '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching user questions")


@app.get(f"{BASE_API_PATH}/questions/{{question_id}}", response_model=QuestionOut, tags=["Expert Q&A", "API"])
async def get_single_question(question_id: int, db: Session = Depends(get_db)):
    """Gets a single question by ID, including its answers. Public endpoint."""
    logger.info(f"API request for question ID {question_id}")
    try:
        question = db.query(Question)\
            .options(
                selectinload(Question.user), # Eager load asker user
                selectinload(Question.expert_answers).selectinload(ExpertQAAnswer.user) # Eager load answer users
            )\
            .filter(Question.id == question_id).first()

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # FastAPI serializes using the reverted QuestionOut and ExpertQAAnswerOut models
        return question
    except Exception as e:
        logger.error(f"Error fetching question {question_id}: {e}", exc_info=True)
        if isinstance(e, ValidationError):
             logger.error(f"Pydantic ResponseValidationError fetching single question: {e.errors()}", exc_info=False)
             raise HTTPException(status_code=500, detail="Server error: Could not process single question data.")
        raise HTTPException(status_code=500, detail="Internal server error fetching question details")


# --- Replace the existing like_question function ---

# --- Add this new endpoint in exp.py ---

# --- Add this endpoint (if you haven't already) ---
@app.get(f"{BASE_API_PATH}/questions/me/liked", response_model=List[int], tags=["Expert Q&A", "API"])
async def get_my_liked_question_ids(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Gets a list of Question IDs that the current user has liked."""
    # ... (keep implementation from previous response) ...
    logger.info(f"API request by {current_user.username} for their liked question IDs.")
    try:
        liked_ids_query = db.query(QuestionLike.question_id)\
                      .filter(QuestionLike.user_id == current_user.id)
        liked_ids = [item[0] for item in liked_ids_query.all()]
        return liked_ids
    except Exception as e:
        logger.error(f"Error fetching liked question IDs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve liked questions.")

# --- Replace the existing like_question function ---
@app.post(f"{BASE_API_PATH}/questions/{{question_id}}/like", status_code=status.HTTP_200_OK, tags=["Expert Q&A", "API"])
async def toggle_like_question( # Renamed for clarity
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Adds or removes a like from the current user for a specific question."""
    logger.info(f"API request by '{current_user.username}' (ID: {current_user.id}) to toggle like for question ID {question_id}.")

    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    # Prevent liking own question (optional)
    # if db_question.user_id == current_user.id:
    #    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot like your own question.")

    # Check if the user has already liked this question
    existing_like = db.query(QuestionLike).filter(
        QuestionLike.user_id == current_user.id,
        QuestionLike.question_id == question_id
    ).first()

    try:
        if existing_like:
            # --- Unlike ---
            logger.info(f"User '{current_user.username}' unliking question ID {question_id}.")
            db.delete(existing_like)
            db_question.likes = max(0, (db_question.likes or 0) - 1)
            db.commit()
            db.refresh(db_question)
            return {"message": "Like removed.", "likes": db_question.likes, "liked": False} # Indicate unlike occurred
        else:
            # --- Like ---
            logger.info(f"User '{current_user.username}' liking question ID {question_id}.")
            new_like = QuestionLike(user_id=current_user.id, question_id=question_id)
            db.add(new_like)
            db_question.likes = (db_question.likes or 0) + 1
            db.commit()
            db.refresh(db_question)
            return {"message": "Like added.", "likes": db_question.likes, "liked": True} # Indicate like occurred

    except Exception as e:
        db.rollback()
        logger.error(f"Toggle like DB error for question {question_id} by user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update like status.")

# Assume necessary imports: FastAPI, Depends, HTTPException, Session, date, logger
# Assume SQLAlchemy models: Question, ExpertQAAnswer, User
# Assume Pydantic models: ExpertQAAnswerOut, ExpertQAAnswerCreate
# Assume BASE_API_PATH is defined

@app.post(f"{BASE_API_PATH}/expertqa/answers/{{question_id}}", response_model=ExpertQAAnswerOut, status_code=201, tags=["Expert Q&A", "API"])
async def submit_expertqa_answer(
    question_id: int,
    answer_data: ExpertQAAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """
    Submits an answer to a specific Expert Q&A question (Alumni only).
    (Modified: Removed check against SelectedExpertQuestion table)
    """
    logger.info(f"API POST /expertqa/answers/{question_id} by '{current_user.username}'")

    # Check 1: User must be alumni
    if not current_user.is_alumni:
        raise HTTPException(status_code=403, detail="Only alumni can answer expert questions.")

    # Check 2: The question must exist
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # --- REMOVED Check if this question is selected ---
    # today = date.today()
    # is_selected = db.query(SelectedExpertQuestion).filter(
    #     SelectedExpertQuestion.question_id == question_id,
    #     SelectedExpertQuestion.selected_date == today
    # ).first()
    #
    # if not is_selected:
    #     logger.warning(f"Alumnus {current_user.username} tried to answer non-selected question {question_id}")
    #     raise HTTPException(status_code=403, detail="This question is not currently selected for alumni answers.")
    # --- End REMOVED check ---

    # Create the answer object
    db_answer = ExpertQAAnswer(
        question_id=question_id,
        user_id=current_user.id,
        answer_text=answer_data.answer_text,
        is_alumni_answer=True  # Mark it as an alumni answer
    )
    try:
        # Add and commit the new answer
        db.add(db_answer)
        db.commit()
        db.refresh(db_answer) # Refresh to get the assigned ID, etc.
        logger.info(f"Alumnus '{current_user.username}' submitted answer ID {db_answer.id} for question ID {question_id}")

        # Return the created answer (FastAPI/Pydantic handles serialization)
        return db_answer
    except Exception as e:
        db.rollback() # Rollback in case of error
        logger.error(f"Submit EQA answer DB error for question {question_id} by user {current_user.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error submitting answer.")
@app.get(f"{BASE_API_PATH}/expertqa/selected-questions", response_model=List[QuestionOut], tags=["Expert Q&A", "API"])
async def get_selected_questions_for_alumni(db: Session = Depends(get_db)):
    """
    Gets the Top 5 most liked questions from the main questions table.
    These are considered the "selected" questions for alumni to answer.
    (Modified: No longer uses SelectedExpertQuestion table)
    """
    logger.info("API request for top 5 liked Expert Q&A questions (for alumni selection).")
    try:
        # Fetch the top 5 questions with the highest number of likes directly
        top_liked_questions = db.query(Question)\
            .options(
                selectinload(Question.user), # <<< THIS IS CORRECT for QuestionOut's username
                selectinload(Question.expert_answers).selectinload(ExpertQAAnswer.user)  # Eager load answers and their users
            )\
            .order_by(desc(Question.likes), desc(Question.created_at))\
            .limit(5).all()

        if not top_liked_questions:
            logger.info("No questions found in the database.")
            return []

        logger.info(f"Returning {len(top_liked_questions)} top liked questions for alumni selection.")
        # FastAPI serializes using QuestionOut and ExpertQAAnswerOut models
        return top_liked_questions

    except Exception as e:
        logger.error(f"Error fetching top liked questions for alumni: {e}", exc_info=True)
        if isinstance(e, ValidationError): # Catch Pydantic validation errors
             logger.error(f"Pydantic ResponseValidationError fetching top liked questions: {e.errors()}", exc_info=False)
             raise HTTPException(status_code=500, detail="Server error: Could not process top liked question data.")
        raise HTTPException(status_code=500, detail="Server error fetching top liked questions for alumni.")
        
@app.post(f"{BASE_API_PATH}/expertqa/answers/{{answer_id}}/like", status_code=200, tags=["Expert Q&A", "API"])
async def like_expertqa_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login
):
    """Increments the like count for an Expert Q&A answer."""
    logger.info(f"API POST /expertqa/answers/{answer_id}/like by '{current_user.username}'")
    answer = db.query(ExpertQAAnswer).filter(ExpertQAAnswer.id == answer_id).first()
    if not answer: raise HTTPException(status_code=404, detail="Answer not found")
    # Optional: Prevent liking own answer
    if answer.user_id == current_user.id: raise HTTPException(status_code=400, detail="Cannot like own answer")

    answer.likes = (answer.likes or 0) + 1
    try: db.commit(); db.refresh(answer); return {"likes": answer.likes}
    except Exception as e: db.rollback(); logger.error(f"Like EQA answer DB error: {e}", exc_info=True); raise HTTPException(status_code=500, detail="DB error")



# --- Career Fairs API ---

@app.get(f"{BASE_API_PATH}/career_fairs", response_model=List[CareerFairOut], tags=["Career Fairs", "API"])
async def get_career_fairs(upcoming_only: bool = False, db: Session = Depends(get_db)):
    """Gets a list of career fairs. Public endpoint."""
    logger.info(f"API request for career fairs (upcoming_only={upcoming_only}).")
    try:
        query = db.query(CareerFair)
        if upcoming_only:
            # Filter for fairs where the date is today or later
            query = query.filter(CareerFair.start_date >= date.today())
        # Order by date (ascending, soonest first)
        career_fairs = query.order_by(CareerFair.start_date.asc()).all()
        # Pydantic validates against List[CareerFairOut]
        return career_fairs
    except Exception as e:
        logger.error(f"Error fetching career fairs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching career fairs")

@app.post(f"{BASE_API_PATH}/career_fairs", response_model=UnverifiedCareerFairOut, status_code=status.HTTP_201_CREATED, tags=["Career Fairs", "Submissions"])
async def submit_career_fair_for_verification(
    career_fair_data: CareerFairCreate, # Input data structure
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires *any* logged-in user
):
    """Submits a new career fair for admin verification."""
    logger.info(f"User '{current_user.username}' submitting career fair '{career_fair_data.name}' for verification.")

    # Create UnverifiedCareerFair object
    db_unverified_fair = UnverifiedCareerFair(
        **career_fair_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )

    try:
        db.add(db_unverified_fair)
        db.commit()
        db.refresh(db_unverified_fair)
        logger.info(f"Career fair '{db_unverified_fair.name}' (Unverified ID: {db_unverified_fair.id}) submitted successfully by '{current_user.username}'.")
        # Return data about the unverified submission
        return db_unverified_fair
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit career fair '{career_fair_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save career fair submission.")
# --- Jobs API ---

@app.get(f"{BASE_API_PATH}/jobs", response_model=List[JobOut], tags=["Jobs", "API"])
async def get_jobs(db: Session = Depends(get_db)):
    """Gets a list of job postings, ordered by date posted. Public endpoint."""
    logger.info("API request for jobs.")
    try:
        # Fetch jobs, order by date posted (most recent first)
        jobs = db.query(Job).order_by(desc(Job.date_posted), desc(Job.created_at)).all()
        # Pydantic validates against List[JobOut]
        return jobs
    except OperationalError as e:
        # Specifically catch potential schema mismatch errors (e.g., missing column)
        logger.error(f"Database schema mismatch fetching jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching jobs. Schema might be outdated (e.g., missing 'image_url' column?). Please check server logs.")
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching job listings")

@app.post(f"{BASE_API_PATH}/jobs", response_model=UnverifiedJobOut, status_code=status.HTTP_201_CREATED, tags=["Jobs", "Submissions"])
async def submit_job_for_verification(
    job_data: JobCreate, # Input data structure
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires *any* logged-in user
):
    """Submits a new job posting for admin verification."""
    logger.info(f"User '{current_user.username}' submitting job '{job_data.title}' for verification.")

    # Create UnverifiedJob object
    db_unverified_job = UnverifiedJob(
        # Unpack fields from the input Pydantic model that match the UnverifiedJob model
        **job_data.model_dump(),
        # Set submission-specific fields
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )

    try:
        db.add(db_unverified_job)
        db.commit()
        db.refresh(db_unverified_job)
        logger.info(f"Job '{db_unverified_job.title}' (Unverified ID: {db_unverified_job.id}) submitted successfully by '{current_user.username}'.")
        # Return data about the unverified submission, validated by UnverifiedJobOut
        return db_unverified_job
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database schema error submitting job '{job_data.title}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error submitting job.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit job '{job_data.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save job submission.")
# --- Internships API ---

@app.get(f"{BASE_API_PATH}/internships", response_model=List[InternshipOut], tags=["Internships", "API"])
async def get_internships(upcoming_only: bool = True, db: Session = Depends(get_db)):
    """Gets a list of internships. Public endpoint."""
    logger.info(f"API request for internships (upcoming_only={upcoming_only}).")
    try:
        query = db.query(Internship)
        if upcoming_only:
            today = date.today()
            # Filter for internships starting today or later, OR those with no end date, OR ending today or later
            query = query.filter(
                (Internship.start_date >= today) |
                (Internship.end_date == None) |
                (Internship.end_date >= today)
            )
        # Order by start date (ascending, soonest first)
        internships = query.order_by(Internship.start_date.asc()).all()
        # Pydantic validates against List[InternshipOut]
        return internships
    except Exception as e:
        logger.error(f"Error fetching internships: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching internships")


@app.post(f"{BASE_API_PATH}/internships", response_model=UnverifiedInternshipOut, status_code=status.HTTP_201_CREATED, tags=["Internships", "Submissions"])
async def submit_internship_for_verification(
    internship_data: InternshipCreate, # Input data structure
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires *any* logged-in user
):
    """Submits a new internship posting for admin verification."""
    logger.info(f"User '{current_user.username}' submitting internship '{internship_data.title}' for verification.")

    # Create UnverifiedInternship object
    db_unverified_internship = UnverifiedInternship(
        **internship_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )

    try:
        db.add(db_unverified_internship)
        db.commit()
        db.refresh(db_unverified_internship)
        logger.info(f"Internship '{db_unverified_internship.title}' (Unverified ID: {db_unverified_internship.id}) submitted successfully by '{current_user.username}'.")
        # Return data about the unverified submission
        return db_unverified_internship
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit internship '{internship_data.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save internship submission.")
# --- Hackathons API ---
# REMOVE response_model from the decorator to prevent startup/schema issues
@app.get(f"{BASE_API_PATH}/hackathons", tags=["Hackathons", "API"])
async def get_hackathons(upcoming_only: bool = True, db: Session = Depends(get_db)):
    """Gets a list of hackathons. Public endpoint."""
    logger.info(f"API GET /hackathons (upcoming={upcoming_only})")
    hackathons_data = [] # Build a list of dictionaries manually
    try:
        query = db.query(Hackathon)
        if upcoming_only:
            today = date.today()
            query = query.filter(Hackathon.start_date != None, Hackathon.start_date >= today)
        hackathons_db = query.order_by(Hackathon.start_date.asc()).all()

        # Manually create dictionaries with desired fields
        # This bypasses complex Pydantic validation on the list itself
        for h in hackathons_db:
            hackathons_data.append({
                "id": h.id,
                "name": h.name,
                "date": h.start_date, # Include the date object or None
                "location": h.location,
                "description": h.description,
                "theme": h.theme,
                "prize_pool": h.prize_pool,
                "url": h.url,
                "created_at": h.created_at,
                "updated_at": h.updated_at
            })
        return hackathons_data # Return the list of dictionaries

    except Exception as e:
         logger.error(f"Error fetching hackathons: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Internal server error preparing hackathon data")
    
@app.post(f"{BASE_API_PATH}/hackathons", response_model=UnverifiedHackathonOut, status_code=status.HTTP_201_CREATED, tags=["Hackathons", "Submissions"])
async def submit_hackathon_for_verification(
    hackathon_data: HackathonCreate, # Input data structure
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires *any* logged-in user
):
    """Submits a new hackathon for admin verification."""
    logger.info(f"User '{current_user.username}' submitting hackathon '{hackathon_data.name}' for verification.")

    # Create UnverifiedHackathon object
    db_unverified_hackathon = UnverifiedHackathon(
        # Use exclude_unset=True if you want to allow partial submissions based on HackathonCreate
        **hackathon_data.model_dump(exclude_unset=True),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )

    try:
        db.add(db_unverified_hackathon)
        db.commit()
        db.refresh(db_unverified_hackathon)
        logger.info(f"Hackathon '{db_unverified_hackathon.name}' (Unverified ID: {db_unverified_hackathon.id}) submitted successfully by '{current_user.username}'.")
        # Return data about the unverified submission
        return db_unverified_hackathon
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit hackathon '{hackathon_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save hackathon submission.")
    
# --- Daily Spark API ---

@app.post(f"{BASE_API_PATH}/daily-spark/questions", response_model=DailySparkQuestionOut, status_code=201, tags=["Daily Spark", "API", "Alumni Only"])
async def create_daily_spark_question(
    question_data: DailySparkQuestionCreate, # Contains question_text, company, role
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Allows an alumnus to post a Daily Spark question (subject to limits)."""
    logger.info(f"API POST /daily-spark/questions by '{current_user.username}'")

    if not current_user.is_alumni:
        raise HTTPException(status_code=403, detail="Only alumni can post Daily Spark questions.")

    today = date.today()
    DAILY_SPARK_OVERALL_LIMIT = 5 # Overall limit for all alumni for the day

    # Check overall daily limit first (how many questions already posted today by ANY alumnus)
    questions_posted_today_overall_count = db.query(DailySparkQuestion).filter(
        DailySparkQuestion.posted_date == today
    ).count()

    if questions_posted_today_overall_count >= DAILY_SPARK_OVERALL_LIMIT:
        logger.warning(f"Overall daily limit of {DAILY_SPARK_OVERALL_LIMIT} Daily Spark questions reached for today.")
        raise HTTPException(status_code=400, detail=f"The maximum number of {DAILY_SPARK_OVERALL_LIMIT} Daily Spark questions for today has already been posted by all alumni.")

    # Create the DailySparkQuestion instance with user_id and posted_date
    # The 'question' field in DailySparkQuestion model stores the text.
    db_spark_question_instance = DailySparkQuestion(
        question=question_data.question_text,
        company=question_data.company,
        role=question_data.role,
        user_id=current_user.id, # Assign current user as the poster
        posted_date=today       # Set the posted date
        # created_at and updated_at will be set by default by the model
    )

    try:
        db.add(db_spark_question_instance)
        db.commit()
        db.refresh(db_spark_question_instance)

        # To ensure 'posted_by_username' is populated in the response,
        # assign the current_user to the relationship attribute if it wasn't auto-loaded.
        # SQLAlchemy often handles this if the session is still active and relationships are defined.
        if not hasattr(db_spark_question_instance, 'posted_by_alumnus') or \
           not db_spark_question_instance.posted_by_alumnus:
            db_spark_question_instance.posted_by_alumnus = current_user

        # For DailySparkQuestionOut response model, it expects an 'answers' list.
        if not hasattr(db_spark_question_instance, 'answers') or db_spark_question_instance.answers is None:
             db_spark_question_instance.answers = []

        logger.info(f"Alumnus '{current_user.username}' (ID: {current_user.id}) posted Daily Spark question ID {db_spark_question_instance.id}")
        return db_spark_question_instance

    except sqlite3.IntegrityError as ie: # Catches UniqueConstraint violation
        db.rollback()
        # Check if it's our specific unique constraint for (user_id, posted_date)
        if "uq_alumni_spark_once_per_day" in str(ie.orig).lower():
            logger.warning(f"Alumnus '{current_user.username}' (ID: {current_user.id}) attempted to post Daily Spark again today (UniqueConstraint violated).")
            raise HTTPException(status_code=400, detail="You have already posted a Daily Spark question today.")
        else:
            # Some other integrity error
            logger.error(f"Database integrity error creating Daily Spark question for user '{current_user.username}': {ie}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not save Daily Spark question due to a database conflict.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Daily Spark question for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save Daily Spark question due to a server error.")


# exp.py (Corrected Daily Spark endpoint)

# Assuming imports: logger, date, desc, func, Session, Depends, get_db,
# HTTPException, selectinload, DailySparkQuestion, DailySparkAnswer, DailySparkQuestionOut

@app.get(f"{BASE_API_PATH}/daily-spark/today", response_model=DailySparkQuestionOut, tags=["Daily Spark", "API"])
async def get_todays_question(db: Session = Depends(get_db)):
    """Gets the most recent Daily Spark question posted *today*."""
    logger.info("API request for today's daily spark question.")
    today = date.today()
    try:
        latest_question = db.query(DailySparkQuestion)\
                            .options(
                                selectinload(DailySparkQuestion.answers),
                                selectinload(DailySparkQuestion.posted_by_alumnus) # Eager load for username
                            )\
                            .filter(DailySparkQuestion.posted_date == today)\
                            .order_by(desc(DailySparkQuestion.created_at))\
                            .first()

        if not latest_question:
            logger.warning("No Daily Spark question posted today, attempting to return latest overall.")
            latest_question = db.query(DailySparkQuestion)\
                                .options(
                                    selectinload(DailySparkQuestion.answers),
                                    selectinload(DailySparkQuestion.posted_by_alumnus)
                                )\
                                .order_by(desc(DailySparkQuestion.posted_date), desc(DailySparkQuestion.created_at))\
                                .first()
            if not latest_question:
                logger.warning("No Daily Spark questions found in the database at all.")
                raise HTTPException(status_code=404, detail="No Daily Spark question found.")
        return latest_question
    except Exception as e:
        logger.error(f"Error fetching today's daily spark question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching daily spark")    
# (Keep existing POST /daily-spark/submit, POST /daily-spark/answers/{id}/upvote, POST /daily-spark/answers/{id}/downvote as they allow *any* user to answer/vote)


@app.get(f"{BASE_API_PATH}/daily-spark/top-liked", response_model=List[DailySparkQuestionOut], tags=["Daily Spark", "API"])
async def get_top_liked_questions(limit: int = 5, db: Session = Depends(get_db)):
    """Gets Daily Spark questions ordered by the sum of votes on their answers. Public endpoint."""
    logger.info(f"API request for top {limit} liked daily spark questions.")
    try:
        # Query questions, join with answers, sum votes, group by question, order by total votes
        questions_with_votes = db.query(
                DailySparkQuestion,
                func.sum(DailySparkAnswer.votes).label('total_votes') # Sum votes per question
            )\
            .outerjoin(DailySparkAnswer, DailySparkQuestion.id == DailySparkAnswer.question_id)\
            .group_by(DailySparkQuestion.id)\
            .order_by(desc('total_votes'))\
            .limit(limit).all()

        # Extract only the Question objects from the (Question, total_votes) tuples
        top_questions = [q for q, votes in questions_with_votes]
        # Pydantic validates against List[DailySparkQuestionOut]
        return top_questions
    except Exception as e:
        logger.error(f"Error fetching top liked daily spark questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching top questions")


@app.post(f"{BASE_API_PATH}/daily-spark/submit", response_model=DailySparkAnswerOut, status_code=201, tags=["Daily Spark", "API"])
async def submit_daily_spark_answer(
    data: DailySparkSubmit, # Body validated by Pydantic
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Submits an answer to the *most recent* Daily Spark question (requires cookie auth)."""
    logger.info(f"API request by '{current_user.username}' to submit Daily Spark answer.")

    # Find the most recent question first
    today_question = db.query(DailySparkQuestion).order_by(desc(DailySparkQuestion.created_at)).first()
    if not today_question:
        raise HTTPException(status_code=404, detail="Cannot submit answer: Today's Daily Spark question not found")

    # Create the answer object
    new_answer = DailySparkAnswer(
        question_id=today_question.id,
        text=data.text,
        user=current_user.username # Store username associated with the answer
    )
    try:
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        logger.info(f"User '{current_user.username}' submitted answer ID {new_answer.id} for Daily Spark question ID {today_question.id}")
        # Pydantic validates against DailySparkAnswerOut
        return new_answer
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit Daily Spark answer DB error by '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save submission")

@app.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/upvote", status_code=200, tags=["Daily Spark", "API"])
async def upvote_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Upvotes a specific Daily Spark answer (requires cookie auth)."""
    logger.info(f"API request by '{current_user.username}' to upvote Daily Spark answer ID {answer_id}.")

    # Find the answer
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Optional: Prevent users from voting on their own answers
    if answer.user == current_user.username:
        raise HTTPException(status_code=400, detail="You cannot vote on your own answer")

    # Optional: Implement logic to prevent double-voting (e.g., using a separate Votes table)

    # Increment votes
    answer.votes = (answer.votes or 0) + 1

    try:
        db.commit()
        db.refresh(answer)
        logger.info(f"User '{current_user.username}' upvoted Daily Spark answer ID {answer_id}. New votes: {answer.votes}")
        # Return the new vote count
        return {"votes": answer.votes}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upvote answer ID {answer_id} DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not record vote")

@app.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/downvote", status_code=200, tags=["Daily Spark", "API"])
async def downvote_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Downvotes a specific Daily Spark answer (requires cookie auth)."""
    logger.info(f"API request by '{current_user.username}' to downvote Daily Spark answer ID {answer_id}.")

    # Find the answer
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Optional: Prevent users from voting on their own answers
    if answer.user == current_user.username:
        raise HTTPException(status_code=400, detail="You cannot vote on your own answer")

    # Optional: Implement logic to prevent double-voting

    # Decrement votes (ensure it doesn't go below a certain threshold if needed, e.g., 0)
    answer.votes = (answer.votes or 0) - 1

    try:
        db.commit()
        db.refresh(answer)
        logger.info(f"User '{current_user.username}' downvoted Daily Spark answer ID {answer_id}. New votes: {answer.votes}")
        # Return the new vote count
        return {"votes": answer.votes}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to downvote answer ID {answer_id} DB error by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not record vote")


# --- Career Fairs API ---

@app.get(f"{BASE_API_PATH}/career_fairs", response_model=List[CareerFairOut], tags=["Career Fairs", "API"])
async def get_career_fairs(upcoming_only: bool = False, db: Session = Depends(get_db)):
    """Gets a list of career fairs. Public endpoint."""
    logger.info(f"API request for career fairs (upcoming_only={upcoming_only}).")
    try:
        query = db.query(CareerFair)
        if upcoming_only:
            today = date.today()
            # Filter using the RENAMED column
            query = query.filter(CareerFair.start_date >= today)
        # Order using the RENAMED column
        career_fairs = query.order_by(CareerFair.start_date.asc()).all()
        return career_fairs
    except Exception as e:
        # ... error handling ...
        logger.error(f"Error fetching career fairs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching career fairs")


@app.post(f"{BASE_API_PATH}/career_fairs", response_model=UnverifiedCareerFairOut, status_code=status.HTTP_201_CREATED, tags=["Career Fairs", "Submissions"])
async def submit_career_fair_for_verification(
    career_fair_data: CareerFairCreate, # Input uses 'start_date' via CareerFairBase
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Submits a new career fair for admin verification."""
    logger.info(f"User '{current_user.username}' submitting career fair '{career_fair_data.name}' for verification.")
    # Unpacking works because Pydantic model uses start_date and SQLAlchemy model uses start_date
    db_unverified_fair = UnverifiedCareerFair(
        **career_fair_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )
    try:
        # ... add, commit, refresh ...
         db.add(db_unverified_fair)
         db.commit()
         db.refresh(db_unverified_fair)
         logger.info(f"Career fair '{db_unverified_fair.name}' (Unverified ID: {db_unverified_fair.id}) submitted successfully by '{current_user.username}'.")
         return db_unverified_fair
    except Exception as e:
        # ... error handling ...
        db.rollback()
        logger.error(f"Failed to submit career fair '{career_fair_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save career fair submission.")


# --- Hackathons API ---

@app.get(f"{BASE_API_PATH}/hackathons", tags=["Hackathons", "API"])
async def get_hackathons(upcoming_only: bool = True, db: Session = Depends(get_db)):
    """Gets a list of hackathons. Public endpoint."""
    logger.info(f"API GET /hackathons (upcoming={upcoming_only})")
    hackathons_data = []
    try:
        query = db.query(Hackathon)
        if upcoming_only:
            today = date.today()
            # Filter using RENAMED column
            query = query.filter(Hackathon.start_date != None, Hackathon.start_date >= today)
        # Order using RENAMED column
        hackathons_db = query.order_by(Hackathon.start_date.asc()).all()

        for h in hackathons_db:
            hackathons_data.append({
                "id": h.id,
                "name": h.name,
                "start_date": h.start_date, # RENAMED field in output dict
                "location": h.location,
                "description": h.description,
                "theme": h.theme,
                "prize_pool": h.prize_pool,
                "url": h.url,
                "created_at": h.created_at,
                "updated_at": h.updated_at
            })
        return hackathons_data
    except Exception as e:
         # ... error handling ...
         logger.error(f"Error fetching hackathons: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Internal server error preparing hackathon data")


@app.post(f"{BASE_API_PATH}/hackathons", response_model=UnverifiedHackathonOut, status_code=status.HTTP_201_CREATED, tags=["Hackathons", "Submissions"])
async def submit_hackathon_for_verification(
    hackathon_data: HackathonCreate, # Input uses 'start_date' via HackathonBase
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    """Submits a new hackathon for admin verification."""
    logger.info(f"User '{current_user.username}' submitting hackathon '{hackathon_data.name}' for verification.")
    # Unpacking works because Pydantic model uses start_date and SQLAlchemy model uses start_date
    db_unverified_hackathon = UnverifiedHackathon(
        **hackathon_data.model_dump(exclude_unset=True),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.utcnow(),
        status='pending'
    )
    try:
        # ... add, commit, refresh ...
        db.add(db_unverified_hackathon)
        db.commit()
        db.refresh(db_unverified_hackathon)
        logger.info(f"Hackathon '{db_unverified_hackathon.name}' (Unverified ID: {db_unverified_hackathon.id}) submitted successfully by '{current_user.username}'.")
        return db_unverified_hackathon
    except Exception as e:
        # ... error handling ...
        db.rollback()
        logger.error(f"Failed to submit hackathon '{hackathon_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save hackathon submission.")


# --- Feed API ---

@app.get(f"{BASE_API_PATH}/feed/events", response_model=List[Event], tags=["Feed", "API"])
async def get_feed_events(limit_per_type: int = 3, db: Session = Depends(get_db)):
    """
    Compiles a feed of recent events (verified jobs, internships, hackathons).
    Public endpoint. Uses 'start_date' as the common date field for sorting and output.
    """
    logger.info(f"API request for feed events (limit per type: {limit_per_type}).")
    today = date.today()
    feed_items_dicts: List[Dict] = [] # Intermediate list of dictionaries

    try:
        # === Fetch Recent Verified Jobs ===
        try:
            jobs_db = db.query(Job)\
                .order_by(desc(Job.date_posted), desc(Job.created_at))\
                .limit(limit_per_type).all()
            for j in jobs_db:
                # Jobs use 'date_posted' as their primary date indicator
                job_relevant_date = None
                if j.date_posted:
                    if isinstance(j.date_posted, datetime): job_relevant_date = j.date_posted.date()
                    elif isinstance(j.date_posted, date): job_relevant_date = j.date_posted
                feed_items_dicts.append({
                    'id': j.id,
                    'name': j.title,
                    'description': j.description,
                    'start_date': job_relevant_date, # <<< CHANGED KEY: Map Job.date_posted -> Event.start_date
                    'location': j.location,
                    'url': j.url,
                    'type': 'job',
                    'company': j.company
                })
        except Exception as e_job:
             logger.error(f"Error fetching jobs for feed: {e_job}", exc_info=True)
             logger.warning("Skipping jobs in feed due to error.")


        # === Fetch Upcoming/Ongoing Verified Internships ===
        try:
            internships_db = db.query(Internship)\
                .filter(
                    (Internship.start_date >= today) |
                    (Internship.end_date == None) |
                    (Internship.end_date >= today)
                )\
                .order_by(Internship.start_date.asc().nulls_last(), desc(Internship.created_at))\
                .limit(limit_per_type).all()
            for i in internships_db:
                # Internships already use 'start_date'
                internship_relevant_date = None
                if i.start_date:
                    if isinstance(i.start_date, datetime): internship_relevant_date = i.start_date.date()
                    elif isinstance(i.start_date, date): internship_relevant_date = i.start_date
                feed_items_dicts.append({
                    'id': i.id,
                    'name': i.title,
                    'description': i.description,
                    'start_date': internship_relevant_date, # <<< CHANGED KEY: Map Internship.start_date -> Event.start_date
                    'location': None,
                    'url': i.url,
                    'type': 'internship',
                    'company': i.company
                })
        except Exception as e_internship:
            logger.error(f"Error fetching internships for feed: {e_internship}", exc_info=True)
            logger.warning("Skipping internships in feed due to error.")


        # === Fetch Upcoming Verified Hackathons ===
        try:
            # Ensure Hackathon model and DB use start_date column
            hackathons_db = db.query(Hackathon)\
                .filter(Hackathon.start_date != None, Hackathon.start_date >= today)\
                .order_by(Hackathon.start_date.asc(), desc(Hackathon.created_at))\
                .limit(limit_per_type).all()
            for h in hackathons_db:
                # Hackathons now use 'start_date'
                hackathon_relevant_date = None
                if h.start_date:
                    if isinstance(h.start_date, datetime): hackathon_relevant_date = h.start_date.date()
                    elif isinstance(h.start_date, date): hackathon_relevant_date = h.start_date
                feed_items_dicts.append({
                    'id': h.id,
                    'name': h.name,
                    'description': h.description,
                    'start_date': hackathon_relevant_date, # <<< CHANGED KEY: Map Hackathon.start_date -> Event.start_date
                    'location': h.location,
                    'url': h.url,
                    'type': 'hackathon',
                    'company': None
                })
        except OperationalError as e_hackathon:
            db.rollback()
            logger.error(f"Database schema error fetching hackathons for feed (Check 'start_date' column): {e_hackathon}", exc_info=False)
            logger.warning("Skipping hackathons in feed due to database schema error.")
        except Exception as e_hackathon_other:
            logger.error(f"Unexpected error fetching hackathons for feed: {e_hackathon_other}", exc_info=True)
            logger.warning("Skipping hackathons in feed due to unexpected error.")


        # === Sort the combined list by the 'start_date' key ===
        # Handles None dates by placing them at the beginning/end depending on reverse
        feed_items_dicts.sort(key=lambda item: item.get('start_date') if item.get('start_date') is not None else date.min, reverse=True) # <<< CHANGED KEY for sorting

        # Optional: Limit the total number of items
        # feed_items_dicts = feed_items_dicts[:15]

        # === Convert dictionaries to Event model instances and validate ===
        feed_events = []
        try:
            # This conversion now expects 'start_date' in the item dictionaries
            feed_events = [Event(**item) for item in feed_items_dicts]
            logger.info(f"Successfully generated feed with {len(feed_events)} items.")
            return feed_events

        except ValidationError as e_val:
            # Log detailed Pydantic validation error (will now check for 'start_date')
            logger.error(f"Pydantic validation error creating Event models for feed: {e_val}", exc_info=True)
            problematic_items = []
            for item_index, item_dict in enumerate(feed_items_dicts):
                 try: Event(**item_dict)
                 except ValidationError: problematic_items.append({"index": item_index, "item": {k: type(v).__name__ for k, v in item_dict.items()}})
            logger.error(f"Problematic dictionary item structures causing validation error (max 5 shown): {problematic_items[:5]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error processing feed data. Validation failed for 'Event' model (using 'start_date'). Check server logs. Error: {e_val.errors()}"
            )

    # --- General Error Handling ---
    except Exception as e_general:
        logger.error(f"Unexpected error generating feed events: {e_general}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generating feed events.")
    
@app.get(f"{BASE_API_PATH}/features", response_model=List[FeatureOut], tags=["General", "API"])
async def get_features_list(db: Session = Depends(get_db)):
    """Retrieves a list of available platform features (from the 'features' table). Public endpoint."""
    logger.info("API request for features list.")
    try:
        features = db.query(Feature).order_by(Feature.id.asc()).all()
        # Pydantic validates against List[FeatureOut]
        return features
    except Exception as e:
        logger.error(f"Error fetching features list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching features list")

# --- Search API ---

@app.get(f"{BASE_API_PATH}/search", response_model=List[SearchResult], tags=["Search", "API"])
async def search_resources(
    term: str, # Search term from query parameter (e.g., /api/search?term=python)
    db: Session = Depends(get_db),
    # Search is public, but check for optional user for potential personalization later
    current_user: Optional[User] = Depends(get_current_user_from_cookie) # Use cookie if available, but don't require
):
    """Searches across different resource types based on a query term. Public endpoint."""
    results: List[SearchResult] = []
    # Basic validation on search term length
    if not term or len(term.strip()) < 2:
         # Return empty list if term is too short or empty
         return []

    term_stripped = term.strip()
    search_term_like = f"%{term_stripped.lower()}%" # Use lowercase for case-insensitive search
    log_user = f"user '{current_user.username}'" if current_user else "anonymous user"
    logger.info(f"Search requested for term: '{term_stripped}' by {log_user}")

    try:
        # Search Users (by username)
        users = db.query(User).filter(User.username.ilike(search_term_like)).limit(5).all()
        results.extend([
            SearchResult(
                type='user',
                id=u.id,
                name=u.username,
                url=f"/profile.html?username={u.username}" # Link to profile page
             ) for u in users
        ])

        # Search Career Fairs (by name)
        fairs = db.query(CareerFair).filter(CareerFair.name.ilike(search_term_like)).limit(5).all()
        results.extend([
            SearchResult(
                type='career_fair',
                id=f.id,
                name=f.name,
                url=f"/career-fairs.html#fair-{f.id}" # Link to fairs page with fragment
            ) for f in fairs
        ])

        # Search Hackathons (by name)
        hackathons = db.query(Hackathon).filter(Hackathon.name.ilike(search_term_like)).limit(5).all()
        results.extend([
            SearchResult(
                type='hackathon',
                id=h.id,
                name=h.name,
                url=f"/explore-hackathons.html#hackathon-{h.id}" # Link to hackathons page
            ) for h in hackathons
        ])

        # Search Jobs (by title)
        jobs = db.query(Job).filter(Job.title.ilike(search_term_like)).limit(5).all()
        results.extend([
            SearchResult(
                type='job',
                id=j.id,
                name=f"{j.title} at {j.company or 'N/A'}",
                # Prefer external URL if available, otherwise link to explore page fragment
                url=j.url if j.url else f"/explore.html#job-{j.id}"
            ) for j in jobs
        ])

        # Search Internships (by title)
        internships = db.query(Internship).filter(Internship.title.ilike(search_term_like)).limit(5).all()
        results.extend([
            SearchResult(
                type='internship',
                id=i.id,
                name=f"{i.title} at {i.company or 'N/A'}",
                url=i.url if i.url else f"/intership.html#internship-{i.id}" # Link to internship page
            ) for i in internships
        ])

        # Note: Saving search history is moved to a separate POST endpoint `/api/search-history`
        # This keeps the GET request idempotent.

        logger.info(f"Search for '{term_stripped}' yielded {len(results)} results.")
        # Pydantic validates against List[SearchResult]
        return results

    except OperationalError as e:
        logger.error(f"Database schema mismatch during search for '{term_stripped}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during search. Schema might be outdated.")
    except Exception as e_search:
        logger.error(f"Error during search for '{term_stripped}': {e_search}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error performing search")

# --- Search History API ---

@app.post(f"{BASE_API_PATH}/search-history", response_model=SearchHistoryItem, status_code=201, tags=["Search", "API"])
async def add_search_history(
    data: SearchHistoryCreate, # Expects JSON body: {"searchTerm": "..."}
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Adds a term to the current user's search history (requires cookie auth)."""
    search_term = data.searchTerm.strip() # Get term from validated Pydantic model
    if not search_term:
        raise HTTPException(status_code=400, detail="Search term cannot be empty")

    logger.info(f"API request by '{current_user.username}' to add search term '{search_term}' to history.")

    # Create SearchHistory object
    db_history = SearchHistory(
        user_id=current_user.id,
        search_term=search_term
    )
    try:
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        # Pydantic validates against SearchHistoryItem
        return db_history
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save search history DB error for user '{current_user.username}', term '{search_term}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save search history")

@app.get(f"{BASE_API_PATH}/search-history", response_model=List[SearchHistoryItem], tags=["Search", "API"])
async def get_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Gets the current user's search history (requires cookie auth)."""
    logger.info(f"API request by '{current_user.username}' for their search history.")
    try:
        # Fetch history for the current user, most recent first
        history = db.query(SearchHistory)\
            .filter(SearchHistory.user_id == current_user.id)\
            .order_by(desc(SearchHistory.timestamp))\
            .limit(50).all() # Limit history results returned
        # Pydantic validates against List[SearchHistoryItem]
        return history
    except Exception as e:
        logger.error(f"Error fetching search history for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve search history")


# --- Notifications API ---

@app.get(f"{BASE_API_PATH}/notifications", response_model=List[NotificationOut], tags=["Notifications", "API"])
async def get_user_notifications(
    only_unread: bool = False, # Query param to filter, e.g., /api/notifications?only_unread=true
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Gets notifications for the current user (requires cookie auth)."""
    logger.info(f"API request by '{current_user.username}' for notifications (unread={only_unread}).")
    try:
        query = db.query(Notification).filter(Notification.user_id == current_user.id)
        if only_unread:
            query = query.filter(Notification.is_read == False)

        # Fetch notifications, most recent first, limit count
        notifications = query.order_by(desc(Notification.created_at)).limit(50).all()
        # Pydantic validates against List[NotificationOut]
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve notifications")

@app.post(f"{BASE_API_PATH}/notifications/mark-read", status_code=200, tags=["Notifications", "API"])
async def mark_notifications_as_read(
    notification_data: NotificationMarkRead, # Expects JSON body: {"notification_ids": [1, 2, 3]}
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie) # Requires login (cookie)
):
    """Marks specified notifications as read for the current user (requires cookie auth)."""
    if not notification_data.notification_ids:
        # Nothing to do if list is empty
        return {"message": "No notification IDs provided", "updated_count": 0}

    logger.info(f"API request by '{current_user.username}' to mark notifications read: {notification_data.notification_ids}")
    try:
        # Perform bulk update for efficiency
        update_query = db.query(Notification)\
            .filter(
                Notification.user_id == current_user.id,
                Notification.id.in_(notification_data.notification_ids),
                Notification.is_read == False # Only update unread ones
            )

        # Get count before update (optional, update returns count in some dialects)
        # count_to_update = update_query.count()

        # Execute update
        updated_count = update_query.update(
            {"is_read": True, "updated_at": datetime.utcnow()},
            synchronize_session=False # Important for bulk updates
        )
        db.commit()
        logger.info(f"User '{current_user.username}' marked {updated_count} notifications as read.")
        # Return the number of notifications actually updated
        return {"message": f"{updated_count} notifications marked as read", "updated_count": updated_count}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark notifications read DB error for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update notifications")

# --- Help/Issues API ---

@app.post(f"{BASE_API_PATH}/help/submit-issue", response_model=UserIssueResponse, status_code=201, tags=["Help", "API"])
async def submit_user_issue_report(
    issue_data: UserIssueCreate, # Body validated by Pydantic (name, email, message)
    db: Session = Depends(get_db),
    # Optional cookie auth: Try to associate issue with user if logged in, but allow anonymous
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """Submits a user issue or feedback. Allows anonymous submission."""
    user_id = current_user.id if current_user else None
    submitter_log_name = f"User ID {user_id}" if user_id else f"Anonymous ({issue_data.email})"
    logger.info(f"Issue report submission received from {submitter_log_name} with email {issue_data.email}.")

    # Create UserIssue object
    db_issue = UserIssue(
        user_id=user_id, # Link to user if logged in, otherwise None
        name=issue_data.name,
        email=issue_data.email, # Already validated by Pydantic EmailStr
        message=issue_data.message,
        submitted_at=datetime.utcnow(),
        status='pending' # Initial status
    )
    try:
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        logger.info(f"Issue report ID {db_issue.id} saved successfully from {submitter_log_name}.")
        # Pydantic validates output via UserIssueResponse
        return db_issue
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit issue report DB error from {submitter_log_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not submit issue report")

# --- CORS Middleware (Place towards the end, after all routes) ---
# Configure allowed origins, methods, etc. for Cross-Origin Resource Sharing
# Use "*" for development only. Be specific in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"], # Replace with your frontend origin(s)
    allow_credentials=True, # Allows cookies to be sent cross-origin
    allow_methods=["*"], # Or specify methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"], # Or specify headers
)

# --- Utility Function for Admin Password Resets (Run manually if needed) ---
# This is NOT an API endpoint. It's a helper function you can call from a separate script
# or a dedicated admin interface IF you build one.
def update_user_password(username_or_email: str, new_password: str):
    """Helper function to update a user's password directly via code. USE WITH EXTREME CAUTION."""
    if len(new_password) < 8:
        print(f"[ADMIN UTIL ERROR] New password for '{username_or_email}' is too short. Not updated.")
        return

    # Create a new DB session specifically for this utility function
    db: Session = SessionLocal()
    user: Optional[User] = None
    try:
        # Find the user by username or email
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            # Hash the new password and update the user
            hashed = hash_password(new_password)
            user.hashed_password = hashed
            user.updated_at = datetime.utcnow()
            db.commit()
            print(f"[ADMIN UTIL] Hashed password updated successfully for user '{user.username}' (ID: {user.id}).")
        else:
            print(f"[ADMIN UTIL] User '{username_or_email}' not found. No password updated.")
    except Exception as e:
        db.rollback()
        print(f"[ADMIN UTIL ERROR] Error updating password for '{username_or_email}': {e}")
    finally:
        # Always close the session
        db.close()

# --- Main Execution Block ---
# This runs only when the script is executed directly (e.g., `python exp.py`)
if __name__ == "__main__":
    print("--- Starting Explore FastAPI Server ---")
    APP_HOST = os.environ.get("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.environ.get("APP_PORT", 8001)) # Using 8001 as the default port
    print(f" -> Listening on http://{APP_HOST}:{APP_PORT}")

    # Log configured paths
    db_path = os.path.join(BASE_DIR, 'explore.db')
    print(f" -> Base Directory:   {BASE_DIR}")
    print(f" -> Database File:    {db_path}")
    print(f" -> Frontend Source:  {FRONTEND_DIR}")
    print(f" -> Static Files:     {STATIC_DIR}")

    # Check existence of critical components and warn if missing
    if not os.path.exists(db_path):
        print(f" [WARNING] Database file not found at: {db_path}")
        print("           Attempting to create tables in new database...")
        try:
            # Ensure tables are created if db doesn't exist
            Base.metadata.create_all(bind=engine)
            print("           Database tables created successfully.")
        except Exception as e:
            print(f" [ERROR] Could not create initial database tables: {e}")
            # Consider exiting if DB is essential and cannot be created: exit(1)

    if not os.path.exists(FRONTEND_DIR):
        print(f" [ERROR] Frontend directory not found: {FRONTEND_DIR}")
        print("         HTML pages (login, home, etc.) will likely fail to load.")
    elif not os.path.exists(STATIC_DIR):
         print(f" [WARNING] Static directory not found: {STATIC_DIR}")
         print("           CSS, JavaScript, and images may be missing.")

    # Check email configuration and warn if incomplete
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("\n [WARNING] MAIL_USERNAME or MAIL_PASSWORD environment variables not set.")
        print("           Password reset email functionality WILL NOT WORK.\n")
    else:
        print(f" -> Email configured for sender: {MAIL_DEFAULT_SENDER} via {MAIL_SERVER}:{MAIL_PORT}")

    # Run the Uvicorn server
    print("---------------------------------------")
    uvicorn.run(
        "exp:app", # Points to the FastAPI app instance named 'app' in the file 'exp.py'
        host=APP_HOST,
        port=APP_PORT,
        reload=True, # Enable auto-reload during development (watches for file changes)
        log_level="info" # Set desired log level
    )
