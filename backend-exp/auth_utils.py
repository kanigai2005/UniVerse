# backend-exp/auth_utils.py

from datetime import datetime, timezone
import logging
import os
from fastapi import Depends, HTTPException, status, Cookie, Request # Request for potential redirects
from fastapi import security
from fastapi.responses import RedirectResponse # For redirecting if needed in require_user
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, Annotated, Dict, Any
from urllib.parse import urlencode
from passlib.context import CryptContext # For password utils if moved here
import models
# Import User and get_db from models.py
# Assuming models.py is a sibling
from models import User, get_db
# Assuming config.py is a sibling
from config import FRONTEND_DIR # For templates path

# --- Centralized Logger ---
logger = logging.getLogger("exp") # Root logger for the app

# --- Centralized Templates Object ---
templates: Optional[Jinja2Templates] = None
if os.path.exists(FRONTEND_DIR): # FRONTEND_DIR from config.py
    try:
        templates = Jinja2Templates(directory=os.path.abspath(FRONTEND_DIR))
        logger.info(f"Templates initialized in auth_utils.py. Frontend dir: {FRONTEND_DIR}")
    except Exception as e:
        logger.error(f"Failed to initialize Jinja2Templates in auth_utils.py: {e}")
else:
    logger.error(f"Frontend directory for templates NOT found in auth_utils.py: {FRONTEND_DIR}")

# --- Centralized Session and OTP Storage ---
session_storage: Dict[str, int] = {}
otp_storage: Dict[str, Dict[str, Any]] = {} # Any to accommodate datetime for expiry

# --- Password Hashing Utilities (Moved here for better cohesion) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    from passlib.exc import UnknownHashError # Local import for less frequent use
    try:
        if not pwd_context.identify(hashed_password):
            logger.warning(f"Unrecognized hash format for password verification.")
            return False
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        logger.warning(f"UnknownHashError during password verification.")
        return False
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False

# --- Email Sending Utility (Moved here for better cohesion) ---
async def send_otp_email(email: str, otp: str) -> bool:
    # Import mail config here or pass as arguments if preferred
    from .config import MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
    from email.mime.text import MIMEText # Local import
    import smtplib # Local import

    if not all([MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER]):
        logger.error("Email configuration incomplete in auth_utils. Cannot send OTP.")
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
        logger.info(f"OTP email sent successfully to {email} from auth_utils.")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP Auth Error for {MAIL_USERNAME} from auth_utils.")
        return False
    except Exception as e:
        logger.error(f"Error sending OTP email from auth_utils to {email}: {e}", exc_info=True)
        return False

# --- Authentication Dependency Functions ---
async def get_current_user_from_cookie(
    session_token: Annotated[Optional[str], Cookie()] = None, # Use Cookie for FastAPI to extract it
    db: Session = Depends(get_db)
) -> Optional[models.User]: # Specify models.User
    if session_token is None:
        # logger.debug("No session_token cookie provided.") # Optional logging
        return None

    # Assuming session_storage is a dictionary-like object mapping tokens to user_ids
    # This part depends heavily on how your session_storage is implemented.
    # If session_storage.get() can raise an error or return a non-ID, handle it.
    user_id = session_storage.get(session_token)

    if user_id is None:
        # logger.debug(f"Session token '{session_token[:10]}...' not found in session_storage.") # Optional logging
        return None

    try:
        user_id = int(user_id) # Ensure user_id is an integer if stored as string
    except ValueError:
        logger.error(f"Invalid user_id format '{user_id}' in session_storage for token '{session_token[:10]}...'.")
        # Clean up invalid session
        if session_token in session_storage:
            try: del session_storage[session_token]
            except KeyError: pass
        return None


    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        logger.warning(f"User ID '{user_id}' from session_storage not found in database. Invalidating session token.")
        # Token is valid in session_storage but user doesn't exist in DB (e.g., deleted user)
        # Clean up the stale session token
        if session_token in session_storage:
            try:
                del session_storage[session_token]
            except KeyError:
                pass # Should not happen if user_id was just retrieved
        return None

    # --- NEW: Update last_active here ---
    try:
        user.last_active = datetime.now(timezone.utc) # Use timezone-aware UTC datetime
        db.commit()
        # db.refresh(user) # Optional: if you need the absolute latest state of the user object for the current request
        # logger.info(f"Updated last_active for user '{user.username}'.") # Optional logging
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update last_active for user '{user.username}': {e}", exc_info=True)
        # Do not let this specific error fail the authentication process itself,
        # just log it. The user is still considered authenticated.
    # --- End of last_active update ---

    return user


async def require_user_from_cookie(
    # Ensure 'User' is correctly typed, e.g., models.User if User is not imported directly
    user: Annotated[Optional[models.User], Depends(get_current_user_from_cookie)]
) -> models.User: # Return type should be models.User
    if user is None:
        query_params = urlencode({"error": "Session expired. Please log in again."})
        # Assuming login page is at root '/login.html' or just '/'
        # If your login page is e.g. /user/login.html, adjust the Location header
        login_url = "/login.html" # Or just "/" or "/user/login.html" as appropriate
        # logger.debug(f"User not authenticated, redirecting to {login_url} with error.") # Optional logging
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, # Use 307 for temporary redirect
            detail="Not authenticated. Session may have expired or is invalid.", # More descriptive detail
            headers={"Location": f"{login_url}?{query_params}"}
        )
    return user


async def require_admin(
    current_user: User = Depends(require_user_from_cookie)
) -> User:
    if not current_user.is_admin:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not an admin. Admin access DENIED by auth_utils.require_admin.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required."
        )
    logger.info(f"Admin access GRANTED for user '{current_user.username}' by auth_utils.require_admin.")
    return current_user

def get_current_user( # This is for HTTP BASIC AUTH
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Session = Depends(get_db) # get_db from models.py
) -> User: # User from models.py
    # logger is imported from auth_utils.py
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    if not user:
        logger.debug(f"HTTP Basic Auth failed: User '{credentials.username}' not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"}
        )
    # verify_password should be imported from auth_utils.py or defined in exp.py
    # Let's assume it's in auth_utils.py as per previous plan:
    from .auth_utils import verify_password
    if not verify_password(credentials.password, user.hashed_password):
        logger.debug(f"HTTP Basic Auth failed: Incorrect password for user '{credentials.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"}
        )
    logger.info(f"HTTP Basic Auth successful for user '{user.username}'.")
    return user