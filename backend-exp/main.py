# backend-exp/main.py

import os
import uvicorn
import logging # For basicConfig
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Project-specific imports - relative to main.py's location (backend-exp)
from database import engine, Base # Base is used for table creation, engine for binding
from config import FRONTEND_DIR, STATIC_DIR, APP_HOST, APP_PORT, BASE_API_PATH # Config values
from auth_utils import logger, templates # Shared utilities (templates might be None if dir not found)

# Import routers
from login import router as login_router # Assuming login.py defines a router

# Import routers from the 'user' sub-package
# Option 1: If user/__init__.py re-exports them:
# from user import home_router, profile_router, events_router, connection_router, notifications_router, roadmapexpertqa_router
# Option 2: Import each module and access its router (safer if __init__.py is empty)
from user import home as user_home_module
from user import profile as user_profile_module
from user import events as user_events_module
from user import connection as user_connection_module
from user import notifications as user_notifications_module
from user import roadmapexpertqa as user_roadmapexpertqa_module

from admin import admin_api_router, admin_html_router
from user.home import html_router as user_home_html_router, router as user_home_api_router
from user.profile import html_router as user_profile_html_router, router as user_profile_api_router
from user.events import html_router as user_events_html_router, router as user_events_api_router
from user.connection import html_router as user_connection_html_router, router as user_connection_api_router
from user.notifications import html_router as user_notifications_html_router, router as user_notifications_api_router
from user.roadmapexpertqa import html_router as user_roadmapexpertqa_html_router, router as user_roadmapexpertqa_api_router
# --- FastAPI App ---
app = FastAPI(title="Explore App")

# --- Configure Logging (once for the application) ---
logging.basicConfig(level=logging.INFO)


# --- Create Tables (Startup Event) ---
@app.on_event("startup")
async def startup_event():
    logger.info("Running startup event: Creating database tables if they don't exist...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error creating database tables during startup: {e}", exc_info=True)

# --- Frontend Serving Setup ---
if not os.path.exists(FRONTEND_DIR):
    logger.error(f"Frontend directory not found: {FRONTEND_DIR}")
else:
    if os.path.exists(STATIC_DIR):
        try:
            app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
            logger.info(f"Static files mounted from: {STATIC_DIR}")
        except Exception as e:
            logger.error(f"Failed to mount static directory {STATIC_DIR}: {e}")
    else:
        logger.warning(f"Static directory not found: {STATIC_DIR}. Static files will not be served.")

# --- Include Routers ---
app.include_router(login_router, tags=["Authentication"])

# --- User HTML Page Routers ---
# These will serve pages like /user/home.html, /user/profile.html, etc.
logger.info("Including User HTML Routers with prefix /user")
app.include_router(user_home_html_router, prefix="/user", tags=["User Pages"])
app.include_router(user_profile_html_router, prefix="/user", tags=["User Pages"])
app.include_router(user_events_html_router, prefix="/user", tags=["User Pages"])
app.include_router(user_connection_html_router, prefix="/user", tags=["User Pages"])
app.include_router(user_notifications_html_router, prefix="/user", tags=["User Pages"])
app.include_router(user_roadmapexpertqa_html_router, prefix="/user", tags=["User Pages"])

# --- User API Routers (and any other general APIs) ---
# These will serve APIs like /api/feed/events, /api/daily-spark/today
# NO "/user" prefix is added here because the paths in the user API routers
# already start with BASE_API_PATH (e.g., "/api").
logger.info("Including User API Routers (typically with /api prefix defined within them)")
app.include_router(user_home_api_router, tags=["User APIs - Home/General"])
app.include_router(user_profile_api_router, tags=["User APIs - Profile"])
app.include_router(user_events_api_router, tags=["User APIs - Events"])
app.include_router(user_connection_api_router, tags=["User APIs - Connections"])
app.include_router(user_notifications_api_router, tags=["User APIs - Notifications"])
app.include_router(user_roadmapexpertqa_api_router, tags=["User APIs - ExpertQA"])

# Admin Routers
app.include_router(admin_html_router) # For /admin-home.html etc.
app.include_router(admin_api_router)   # For /api/admin/*


# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{APP_HOST}:{APP_PORT}", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Main Execution Block ---
if __name__ == "__main__":
    logger.info(f"--- Starting UniVerse FastAPI Server (from main.py) ---")
    logger.info(f" -> Listening on http://{APP_HOST}:{APP_PORT}")
    # DATABASE_URL is now in config.py, imported and used by database.py
    # logger.info(f" -> Database URL from config: {DATABASE_URL}") # Need to import DATABASE_URL from config for this line
    logger.info(f" -> Frontend Directory: {FRONTEND_DIR}")
    logger.info(f" -> Static Directory: {STATIC_DIR}")

    uvicorn.run(
        "main:app", # Uvicorn looks for 'app' in 'main.py' (relative to CWD or PYTHONPATH)
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level="info"
    )