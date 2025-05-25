# backend-exp/config.py
import os

# BASE_DIR_BACKEND will be the directory containing THIS config.py file (i.e., backend-exp)
BASE_DIR_BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR_BACKEND) # This will be 'explore'

FRONTEND_DIR = os.path.join(PROJECT_ROOT_DIR, "frontend-exp")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# DATABASE_URL should point to explore.db inside backend-exp
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR_BACKEND, 'explore.db')}"

MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

BASE_API_PATH = '/api' # Base for API routes

APP_HOST = os.environ.get("APP_HOST", "127.0.0.1")
APP_PORT = int(os.environ.get("APP_PORT", 8000)) # Changed your default from 8001 to 8000