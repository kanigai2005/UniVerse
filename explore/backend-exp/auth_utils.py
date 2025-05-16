# backend-exp/auth_utils.py

import logging
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, Annotated, Dict, Any # Keep Dict, Any
from urllib.parse import urlencode
import os # For path joining

# Import User and get_db from models.py
from .models import User, get_db

# --- Centralized Logger ---
logger = logging.getLogger("exp") # Use a common root logger name

# --- Centralized Templates Object ---
templates: Optional[Jinja2Templates] = None
AUTH_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = os.path.dirname(AUTH_UTILS_DIR)
FRONTEND_DIR_FOR_TEMPLATES = os.path.join(PROJECT_ROOT_DIR, "frontend-exp")
if os.path.exists(FRONTEND_DIR_FOR_TEMPLATES):
    try:
        templates = Jinja2Templates(directory=os.path.abspath(FRONTEND_DIR_FOR_TEMPLATES))
        logger.info(f"Templates initialized in auth_utils.py. Frontend dir: {FRONTEND_DIR_FOR_TEMPLATES}")
    except Exception as e:
        logger.error(f"Failed to initialize Jinja2Templates in auth_utils.py: {e}")
else:
    logger.error(f"Frontend directory for templates NOT found in auth_utils.py: {FRONTEND_DIR_FOR_TEMPLATES}")

# --- !!!!!!! CENTRALIZED SESSION AND OTP STORAGE !!!!!!! ---
# --- !!!!!!! DEFINED HERE - SINGLE INSTANCE FOR THE WHOLE APP !!!!!!! ---
session_storage: Dict[str, int] = {}
otp_storage: Dict[str, Dict[str, Any]] = {}
# --- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ---

# --- Authentication Functions ---
async def get_current_user_from_cookie(
    session_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    # logger.debug(f"get_current_user_from_cookie called. Token: '{session_token}'")
    if session_token is None:
        return None
    
    # Now uses the session_storage defined in THIS auth_utils.py file
    user_id = session_storage.get(session_token) 
    if user_id is None:
        # logger.debug(f"Session token '{session_token}' not found in session_storage (auth_utils).")
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"User ID {user_id} from session token '{session_token}' not found in DB. Cleaning session from auth_utils storage.")
        if session_token in session_storage:
            try:
                del session_storage[session_token]
            except KeyError:
                pass
        return None
    # logger.debug(f"User '{user.username}' (ID: {user.id}) authenticated from cookie (auth_utils).")
    return user

async def require_user_from_cookie(
    user: Annotated[Optional[User], Depends(get_current_user_from_cookie)]
) -> User:
    if user is None:
        # logger.warning("require_user_from_cookie (auth_utils): No authenticated user. Redirecting.")
        query_params = urlencode({"error": "Session expired. Please log in."})
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authenticated",
            headers={"Location": f"/?{query_params}"}
        )
    return user

async def require_admin(
    current_user: User = Depends(require_user_from_cookie)
) -> User:
    if not current_user.is_admin:
        # logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) not admin. Denied by require_admin (auth_utils).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required."
        )
    # logger.info(f"Admin access granted for user '{current_user.username}' by require_admin (auth_utils).")
    return current_user