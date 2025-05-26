import secrets
import random
from urllib.parse import urlencode
from datetime import datetime, timedelta
from typing import Annotated, Optional, Any # Added Any for otp_storage type hint if used directly

from fastapi import APIRouter, Depends, Request, Form, Response, Cookie, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import EmailStr # For email validation in forms
from sqlalchemy.orm import Session

# Relative imports assuming login.py is in the root of backend-exp
# and other helper modules are also in the root or structured as planned.
from database import get_db
from models import User # Changed to absolute import
from auth_utils import (
    templates,
    logger,
    session_storage,
    otp_storage,
    hash_password,
    verify_password,
    send_otp_email,
    require_user_from_cookie # This might be used if any of these pages require login
)
# from .config import BASE_API_PATH # Not directly used by these root paths

router = APIRouter()

# --- Login, Logout, Registration, Password Reset Routes ---

@router.get("/", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def serve_login_html(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Serves the main login page (login.html)."""
    return templates.TemplateResponse("login.html", {"request": request, "error": error, "message": message})

@router.post("/login", response_class=RedirectResponse, tags=["Auth"])
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    logger.info(f"Login attempt for username/email: '{username}'")
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    login_error = None
    if not user or not verify_password(password, user.hashed_password):
        login_error = "Incorrect username or password."
        logger.warning(f"Login failed for '{username}'. Reason: {login_error}")
        query_params = urlencode({"error": login_error})
        return RedirectResponse(url=f"/?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    logger.info(f"User '{user.username}' (ID: {user.id}) logged in successfully.")
    session_token = secrets.token_urlsafe(32)
    session_storage[session_token] = user.id
    logger.debug(f"Stored session token {session_token[:8]}... for user ID {user.id} in session_storage.")

    # Redirect to user-prefixed home page
    redirect_url = "/user/home.html"
    if user.is_admin:
        # Assuming admin home is also under /user prefix for consistency or a specific admin router path
        redirect_url = "/admin-home.html" # Or your actual admin path
        logger.info(f"User '{user.username}' is an admin, redirecting to {redirect_url}")
    else:
        logger.info(f"User '{user.username}' is not an admin, redirecting to {redirect_url}")

    redirect_response_obj = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    redirect_response_obj.set_cookie(
        key="session_token", value=session_token, httponly=True,
        secure=request.url.scheme == "https", samesite="lax", max_age=1800
    )
    return redirect_response_obj

@router.get("/logout", response_class=RedirectResponse, tags=["Auth"])
async def logout(response: Response, session_token: Annotated[Optional[str], Cookie()] = None): # Made session_token optional
    logger.info(f"Logout requested. Session token: {session_token[:8] if session_token else 'None'}")
    redirect_url = "/?message=Logged+out+successfully."

    # Create the response object first
    response_obj = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    if session_token and session_token in session_storage:
        try:
            del session_storage[session_token]
            logger.info(f"Removed session token {session_token[:8]}... from session_storage.")
        except KeyError:
            logger.warning(f"Session token {session_token[:8]}... was already removed or invalid during logout.")

    response_obj.delete_cookie(key="session_token", httponly=True, samesite="lax")
    logger.info("Logout cookie cleared.")
    return response_obj


@router.get("/register", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def register_page(
    request: Request,
    error: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None
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

@router.post("/register", response_class=RedirectResponse, tags=["Auth"])
async def register(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    role: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    logger.info(f"Registration attempt for username: {username}, email: {email}, role: {role}")
    error_redirect_params = {"username": username, "email": email}
    if role.lower() in ["student", "alumni", "admin"]:
        error_redirect_params["role"] = role

    db_user_username = db.query(User).filter(User.username == username).first()
    db_user_email = db.query(User).filter(User.email == email).first()
    error = None
    if db_user_username: error = "Username already registered"
    elif db_user_email: error = "Email already registered"
    elif len(password) < 8: error = "Password must be at least 8 characters long"
    elif role.lower() not in ["student", "alumni", "admin"]:
        error = "Invalid role selected."
        if "role" in error_redirect_params: del error_redirect_params["role"]

    if error:
        logger.warning(f"Registration failed for '{username}': {error}")
        error_redirect_params["error"] = error
        query_params = urlencode(error_redirect_params)
        return RedirectResponse(url=f"/register?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    try:
        hashed_password_val = hash_password(password)
        is_student_val = (role.lower() == "student")
        is_alumni_val = (role.lower() == "alumni")
        is_admin_val = (role.lower() == "admin")
        new_user = User(
            username=username, email=email, hashed_password=hashed_password_val,
            is_student=is_student_val, is_alumni=is_alumni_val, is_admin=is_admin_val
        )
        db.add(new_user); db.commit(); db.refresh(new_user)
        logger.info(f"User '{username}' (ID: {new_user.id}) registered successfully as {role}.")

        # Redirect students and admins to their home page after registration
        # Redirect alumni to login page with a success message
        if role.lower() in ["student", "alumni"]:
            success_message = f"Registration as {role} successful. Welcome!"
            query_params = urlencode({"message": success_message})
            # Assuming user home page is now /user/home
            return RedirectResponse(url=f"/?{query_params}", status_code=status.HTTP_303_SEE_OTHER)
        else: # Admin
            query_params = urlencode({"message": "Registration successful. Please log in."})
            return RedirectResponse(url=f"/?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        db.rollback()
        logger.error(f"Registration DB error for user '{username}': {e}", exc_info=True)
        error_redirect_params["error"] = "Registration failed due to a server error."
        query_params = urlencode(error_redirect_params)
        return RedirectResponse(url=f"/register?{query_params}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/forgot-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def forgot_password_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return templates.TemplateResponse("forgetpass.html", {"request": request, "error": error, "message": message})

@router.post("/forgot-password", tags=["Auth"])
async def forgot_password(
    request: Request,
    email: Annotated[EmailStr, Form()],
    db: Session = Depends(get_db)
):
    logger.info(f"Forgot password request received for email: {email}")
    user = db.query(User).filter(User.email == email).first()
    message_to_show = "If an account exists for this email, an OTP has been sent."

    if user:
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        otp_storage[email] = {"otp": otp, "expiry": otp_expiry, "user_id": user.id} # Storing user_id might be useful
        logger.info(f"Generated OTP {otp} for email {email}, valid until {otp_expiry} UTC")

        email_sent = await send_otp_email(email, otp)
        if email_sent:
            logger.info(f"OTP email initiated successfully for {email}.")
            query_params = urlencode({"email": email})
            return RedirectResponse(url=f"/verify-otp?{query_params}", status_code=status.HTTP_303_SEE_OTHER)
        else:
            logger.error(f"Failed to send OTP email to {email}. User will see generic message.")
            if email in otp_storage: del otp_storage[email]
            return templates.TemplateResponse("forgetpass.html", {
                "request": request, "error": "Error sending OTP. Please try again or contact support."
            })
    else:
        logger.warning(f"Forgot password request for non-existent email: {email}")
        return templates.TemplateResponse("forgetpass.html", {"request": request, "message": message_to_show})


@router.get("/verify-otp", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def verify_otp_page(request: Request, email: str, error: Optional[str] = None):
    if not email: raise HTTPException(status_code=400, detail="Email parameter is missing.")
    return templates.TemplateResponse("otp.html", {"request": request, "email": email, "error": error})

@router.post("/verify-otp", response_class=RedirectResponse, tags=["Auth"])
async def verify_otp(
    request: Request, # request might not be strictly needed here unless for scheme check for secure cookie
    email: Annotated[EmailStr, Form()],
    otp_attempt: Annotated[str, Form()]
):
    logger.info(f"OTP verification attempt for email: {email} with OTP: '{otp_attempt}'")
    stored_otp_data = otp_storage.get(email)
    error_message = None

    if not stored_otp_data: error_message = "Invalid or expired OTP request. Please start again."
    elif datetime.utcnow() > stored_otp_data["expiry"]:
        error_message = "OTP has expired. Please request a new one."
        if email in otp_storage: del otp_storage[email]
    elif otp_attempt != stored_otp_data["otp"]: error_message = "Invalid OTP entered."

    if error_message:
        logger.warning(f"OTP verification failed for {email}: {error_message}")
        query_params = urlencode({"email": email, "error": error_message})
        return RedirectResponse(url=f"/verify-otp?{query_params}", status_code=status.HTTP_303_SEE_OTHER)
    else:
        logger.info(f"OTP verification successful for email {email}.")
        # OTP data is kept until password is reset or it expires
        query_params = urlencode({"email": email})
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/reset-password", response_class=HTMLResponse, tags=["Pages", "Auth"])
async def reset_password_page(request: Request, email: str, error: Optional[str] = None):
    if not email: raise HTTPException(status_code=400, detail="Email parameter is missing.")
    # Optional: Add a check here to ensure 'email' is in otp_storage and not expired
    # to prevent direct navigation to this page without OTP verification.
    # if email not in otp_storage or datetime.utcnow() > otp_storage[email]["expiry"]:
    #     logger.warning(f"Unauthorized access to reset password page for {email}")
    #     # Redirect to forgot password or show an error
    #     return RedirectResponse(url="/forgot-password?error=Invalid+session", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("reset.html", {"request": request, "email": email, "error": error})

@router.post("/reset-password", response_class=RedirectResponse, tags=["Auth"])
async def reset_password(
    request: Request, # request might not be strictly needed
    email: Annotated[EmailStr, Form()],
    new_password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    logger.info(f"Password reset submission received for email: {email}")
    stored_otp_data = otp_storage.get(email)
    if not stored_otp_data or datetime.utcnow() > stored_otp_data["expiry"]:
        logger.warning(f"Attempt to reset password for {email} without valid/recent OTP.")
        query_params = urlencode({"error": "Invalid or expired reset session. Please start again."})
        return RedirectResponse(url=f"/forgot-password?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    if len(new_password) < 8:
        logger.warning(f"Password reset failed for {email}: Password too short.")
        query_params = urlencode({"email": email, "error": "Password must be at least 8 characters long."})
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.email == email).first()
    if not user: # Should not happen if OTP was verified against a user
        logger.error(f"Password reset error: User {email} not found during final step.")
        if email in otp_storage: del otp_storage[email]
        query_params = urlencode({"error": "User not found. Please start again."})
        return RedirectResponse(url=f"/forgot-password?{query_params}", status_code=status.HTTP_303_SEE_OTHER)

    try:
        hashed_password_val = hash_password(new_password)
        user.hashed_password = hashed_password_val
        user.updated_at = datetime.utcnow()
        db.commit()
        if email in otp_storage: del otp_storage[email]
        logger.info(f"Password successfully reset for user '{user.username}' (Email: {email}).")
        query_params = urlencode({"message": "Password reset successfully. Please log in."})
        return RedirectResponse(url=f"/?{query_params}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset DB error for {email}: {e}", exc_info=True)
        query_params = urlencode({"email": email, "error": "Failed to reset password due to a server error."})
        return RedirectResponse(url=f"/reset-password?{query_params}", status_code=status.HTTP_303_SEE_OTHER)