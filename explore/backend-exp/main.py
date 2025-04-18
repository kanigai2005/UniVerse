from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import MetaData, create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Annotated, Optional
from urllib.parse import urlencode
import os
import httpx
import secrets
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging (if not already configured)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (ensure EXP_BACKEND_URL is set)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./explore.db")  # Adjusted path
EXP_BACKEND_URL = os.getenv("EXP_BACKEND_URL")
if not EXP_BACKEND_URL:
    logger.error("EXP_BACKEND_URL environment variable not set!")
    # Consider raising an exception here if the backend URL is critical

# Database setup (if main.py manages other data)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

# Define User model (if main.py still needs a local representation)
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


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True

# Read and execute schema.sql
def create_tables_from_schema(engine, schema_file):
    with open(schema_file, 'r') as f:
        sql_commands = f.read().split(';')
        with engine.connect() as connection:
            for command in sql_commands:
                command = command.strip()
                if command:
                    try:
                        connection.execute(command)
                        connection.commit()
                    except Exception as e:
                        logger.error(f"Error executing SQL command: {command}\nError: {e}")

# FastAPI app setup (assuming it's already initialized)
app = FastAPI()

# CORS middleware (assuming it's already added)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), ".././frontend-exp")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR)

# Database Dependency (assuming it's already defined)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Session Management (Basic Example) ---
sessions = {}

def create_session(user_id: int):
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = user_id
    return session_id

def get_user_id_from_session(session_id: str):
    return sessions.get(session_id)

def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]

# --- Dependency to get the current user based on session cookie ---
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    return None

# --- Login Route (Full Code) ---
@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    response: Response,
    db: Session = Depends(get_db)
):
    if not EXP_BACKEND_URL:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Backend URL not configured."})

    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.post(
                f"{EXP_BACKEND_URL}/login",  # Ensure this is the correct endpoint in exp.py
                data={"username": username, "password": password}
            )
            auth_response.raise_for_status()  # Raise an exception for bad status codes

            auth_data = auth_response.json()
            logger.info(f"Authentication response from backend: {auth_data}")

            if "user_id" in auth_data:
                user_id_from_backend = auth_data["user_id"]
                session_id = create_session(user_id_from_backend)
                response.set_cookie(key="session_id", value=session_id, httponly=True)
                return RedirectResponse(url="/home.html", status_code=302)
            else:
                error_message = auth_data.get("detail", "Login failed at backend: User ID not received.")
                logger.warning(f"Login failed: {error_message}")
                return templates.TemplateResponse("login.html", {"request": request, "error": error_message})

        except httpx.HTTPError as e:
            error_message = f"Error connecting to backend: {e}"
            logger.error(error_message)
            return templates.TemplateResponse("login.html", {"request": request, "error": error_message})
        except Exception as e:
            error_message = f"An unexpected error occurred during login: {e}"
            logger.error(error_message)
            return templates.TemplateResponse("login.html", {"request": request, "error": error_message})

# --- Other routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register.html", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    return RedirectResponse(url=f"{EXP_BACKEND_URL}/register", status_code=302)

@app.get("/forgotpass.html", response_class=HTMLResponse)
async def forgot_password_page(request: Request, error: str = None, message: str = None):
    return RedirectResponse(url=f"{EXP_BACKEND_URL}/forgot-password", status_code=302)

@app.get("/reset.html", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str, error: str = None):
    return RedirectResponse(url=f"{EXP_BACKEND_URL}/reset-password?email={email}", status_code=302)

@app.get("/home.html", response_class=HTMLResponse)
async def home(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})


@app.post("/reset.html", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    response: Response
):
    if not EXP_BACKEND_URL:
        return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": "Backend URL not configured."})

    async with httpx.AsyncClient() as client:
        try:
            reset_response = await client.post(
                f"{EXP_BACKEND_URL}/reset-password",
                data={"email": email, "new_password": new_password}
            )
            reset_response.raise_for_status()
            return RedirectResponse(url="/?message=Password reset successfully. Please log in.", status_code=302)
        except httpx.HTTPError as e:
            return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": f"Error resetting password at backend: {e}"})
        except Exception as e:
            return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": f"An unexpected error occurred during password reset: {e}"})

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Example of serving other static HTML files
@app.get("/{filename:path}", response_class=HTMLResponse)
async def serve_html(request: Request, filename: str):
    frontend_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="File not found")

# Initialize tables on startup
if not os.path.exists("explore.db"):
    create_tables_from_schema(engine, "schema.sql")