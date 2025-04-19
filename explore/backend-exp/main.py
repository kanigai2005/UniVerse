from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Annotated
from passlib.context import CryptContext
from urllib.parse import urlencode
import os
import secrets
from datetime import timedelta
from sqlalchemy.sql import func
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables (consider using a .env file for sensitive data)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///universe.db")

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
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend-exp")

app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
templates = Jinja2Templates(directory=frontend_dir)

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

# --- Function to get the current logged-in user (for integration with exp.py) ---
async def get_logged_in_user_id_for_exp(request: Request, db: Session = Depends(get_db)):
    """
    This is a simplified example. In a real application, you would use
    session management (e.g., cookies) to identify the logged-in user.
    For this example, we'll try to extract the username from a query parameter
    or form data. This is NOT secure for production.
    """
    username = request.query_params.get("username")
    if not username:
        form_data = await request.form()
        username = form_data.get("username")

    if username:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return str(user.id)  # Return the user ID as a string
    return None

# --- Routes ---
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

    # Redirect to the home page served by exp.py
    return RedirectResponse(url="http://localhost:8001/home", status_code=302)

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
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return templates.TemplateResponse("forgetpass.html", {"request": request, "error": "There is no account associated with this email."})

    # In a REAL APPLICATION, you would generate a reset token,
    # store it, and send it to the user's email.
    # For this simplified example, we'll just generate a temporary password
    # and redirect to the reset password form.
    reset_token = secrets.token_urlsafe(32) # Generate a unique token
    # In a REAL APP, store this token in the database linked to the user and email

    return RedirectResponse(url=f"/reset-password?email={email}&reset_token={reset_token}", status_code=302)
@app.get("/reset-password-info", response_class=HTMLResponse)
async def reset_password_info_page(request: Request, email: str, temp_password: str):
    # In a REAL APPLICATION, you would NOT display the temporary password.
    # You would instruct the user to check their email for a reset link.
    return templates.TemplateResponse("reset_info.html", {"request": request, "email": email, "temp_password": temp_password})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str, error: str = None):
    # This route is no longer part of the direct flow in this simplified version.
    # You might still keep it for other reset mechanisms.
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
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(new_password)
    user.hashed_password = hashed_password
    db.commit()

    return RedirectResponse(url="/?message=Password reset successfully. Please log in.", status_code=302)

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user