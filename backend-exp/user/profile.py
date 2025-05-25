# backend-exp/user/profile.py

import json
from typing import List, Optional, Dict, Annotated
from datetime import datetime, date

from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials # For Basic Auth
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Relative imports to access modules in the parent 'backend-exp' package
import models # Access as models.User, models.UserResponse etc.
from database import get_db # Assuming get_db is in backend-exp/database.py

from auth_utils import (
    require_user_from_cookie,
    get_current_user_from_cookie,
    templates,
    logger,
    verify_password # Needed for Basic Auth if defined here
)
from config import BASE_API_PATH

try:
    from utils import json_serial
except ImportError:
    logger.warning("utils.py or json_serial not found, defining fallback json_serial in profile.py.")
    def json_serial(obj):
        if isinstance(obj, (datetime, date)): return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable by fallback json_serial")

router = APIRouter()
html_router=APIRouter()
# --- HTTP Basic Auth Dependency (Local to this router/file if preferred) ---
security_profile_basic = HTTPBasic()

def get_current_user_for_profile_basic_auth( # Specific name for this instance
    credentials: Annotated[HTTPBasicCredentials, Depends(security_profile_basic)],
    db: Session = Depends(get_db)
) -> models.User:
    user = db.query(models.User).filter(
        (models.User.username == credentials.username) | (models.User.email == credentials.username)
    ).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.debug(f"Profile Basic Auth failed for user '{credentials.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials (Basic Auth for profile)",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

# --- HTML Serving Endpoints ---

@router.get("/user/profile.html", response_class=HTMLResponse, tags=["Pages", "Profile"], include_in_schema=False)
async def serve_profile_html(
    request: Request, username: Optional[str] = None, db: Session = Depends(get_db),
    viewer_user: models.User = Depends(require_user_from_cookie)
):
    if not templates: return HTMLResponse("Server error: Templates not available.", status_code=503)
    target_username_to_view: str; profile_user_orm: Optional[models.User] = None
    is_own_profile: bool
    if username is None or username == viewer_user.username:
        profile_user_orm = viewer_user; target_username_to_view = viewer_user.username
        is_own_profile = True
    else:
        target_username_to_view = username
        profile_user_orm = db.query(models.User).filter(models.User.username == target_username_to_view).first()
        if not profile_user_orm: raise HTTPException(status_code=404, detail=f"User '{target_username_to_view}' not found")
        is_own_profile = (viewer_user.id == profile_user_orm.id)
    try:
        profile_data_pydantic = models.UserResponse.model_validate(profile_user_orm)
        profile_data_json_str = json.dumps(profile_data_pydantic.model_dump(), default=json_serial)
    except Exception as e:
        logger.error(f"Error serializing profile for '{target_username_to_view}': {e}", exc_info=True)
        return HTMLResponse(f"Error loading profile data.", status_code=500)
    context = {"request": request, "profile_data_json": profile_data_json_str, "is_own_profile": is_own_profile, "viewer_username": viewer_user.username }
    return templates.TemplateResponse("profile.html", context)

@router.get("/user/leaderboard.html", response_class=HTMLResponse, tags=["Pages", "Leaderboard"])
async def serve_leaderboard_html(request: Request, user: models.User = Depends(require_user_from_cookie)):
    if not templates: return HTMLResponse("Server error: Templates not available.", status_code=503)
    return templates.TemplateResponse("leaderboard.html", {"request": request, "username": user.username})

# --- User Profile API Endpoints ---
@router.get(f"{BASE_API_PATH}/users/me", response_model=models.UserResponse, tags=["Users", "API"])
async def read_users_me_api_profile_router(current_user: models.User = Depends(require_user_from_cookie)):
    return current_user

@router.get(f"{BASE_API_PATH}/users/current", response_model=models.UserResponse, tags=["Users", "API"])
async def read_current_user_profile_api_profile_router(current_user: models.User = Depends(require_user_from_cookie)):
    return current_user

@router.put(f"{BASE_API_PATH}/users/me", response_model=models.UserResponse, tags=["Users", "API"])
async def update_own_user_profile_api(
    updated_data: models.UserProfileUpdate = Body(...), db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    update_data_dict = updated_data.model_dump(exclude_unset=True)
    if not update_data_dict: return current_user
    for key, value in update_data_dict.items():
        if hasattr(current_user, key): setattr(current_user, key, value)
    current_user.updated_at = datetime.utcnow()
    try: db.commit(); db.refresh(current_user); return current_user
    except Exception as e: db.rollback(); logger.error(f"DB error updating own profile: {e}"); raise HTTPException(500, "Could not update profile.")

@router.put(f"{BASE_API_PATH}/users/{{username_path:str}}", response_model=models.UserResponse, tags=["Users", "API"])
async def update_user_profile_by_username_api(
    username_path: str, user_update: models.UserUpdate, db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie) # Authenticated user
):
    if username_path != current_user.username and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user_to_update = db.query(models.User).filter(models.User.username == username_path).first()
    if not user_to_update: raise HTTPException(status_code=404, detail="User to update not found")
    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data: raise HTTPException(status_code=400, detail="No update data")
    for key, value in update_data.items():
        if hasattr(user_to_update, key): setattr(user_to_update, key, value)
    user_to_update.updated_at = datetime.utcnow()
    try: db.commit(); db.refresh(user_to_update); return user_to_update
    except Exception as e: db.rollback(); logger.error(f"DB error updating profile for {username_path}: {e}"); raise HTTPException(500, "Could not update profile.")

# This is the route that likely caused the TypeError if get_current_user was misconfigured
@router.get(f"{BASE_API_PATH}/users/{{username_path:str}}", response_model=models.UserResponse, tags=["Users", "API"])
async def read_user_profile_by_username_via_basic_auth_api( # Distinct name
    username_path: str,
    db: Session = Depends(get_db),
    # Uses the locally defined Basic Auth dependency
    authenticated_actor: models.User = Depends(get_current_user_for_profile_basic_auth)
):
    logger.info(f"API (Basic Auth by {authenticated_actor.username}) req for profile: '{username_path}'")
    db_user = db.query(models.User).filter(models.User.username == username_path).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.get(f"{BASE_API_PATH}/public/users/{{username_path:str}}", response_model=models.UserResponse, tags=["Users", "API"])
async def read_user_profile_public_api_profile_router(
    username_path: str, db: Session = Depends(get_db),
    viewer_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    log_msg_viewer = f"viewed by '{viewer_user.username}'" if viewer_user else "viewed by anonymous"
    logger.info(f"Public API request for profile of '{username_path}', {log_msg_viewer}")
    db_user = db.query(models.User).filter(models.User.username == username_path).first()
    if not db_user: raise HTTPException(status_code=404, detail="User not found")
    return db_user

# --- Leaderboard & Alumni API Endpoints ---
@router.get(f"{BASE_API_PATH}/alumni", response_model=List[models.AlumniResponse], tags=["Alumni", "API"])
async def get_all_alumni_api_profile_router(db: Session = Depends(get_db)):
    alumni_list = db.query(models.User).filter(models.User.is_alumni == True).order_by(models.User.username.asc()).all()
    return alumni_list

# In your Python API router file

# ... imports ...
# from config import BASE_API_PATH # Make sure BASE_API_PATH is defined and used if your paths start with it

@router.get(f"{BASE_API_PATH}/leaderboard", response_model=List[models.AlumniResponse], tags=["Leaderboard", "API"])
async def get_leaderboard_api_profile_router(db: Session = Depends(get_db)):
    # The query already includes users who are alumni and orders by activity_score then alumni_gems.
    # Since we're removing activity_score sort from frontend default, let's make gems primary sort here.
    users = db.query(models.User).filter(models.User.is_alumni == True)\
        .order_by(desc(models.User.alumni_gems), desc(models.User.activity_score), models.User.username.asc()).limit(100).all() # Gems first
    # If activity_score is truly removed from consideration, you can remove it from order_by too:
    # .order_by(desc(models.User.alumni_gems), models.User.username.asc()).limit(100).all()
    logger.info(f"Leaderboard data being returned: {[u.username for u in users[:5]]}") # Log a few
    return users
@router.get(f"{BASE_API_PATH}/alumni/top-liked", response_model=Dict[str, List[models.AlumniResponse]], tags=["Alumni", "API"])
async def get_top_liked_alumni_api_profile_router(limit: int = 5, db: Session = Depends(get_db)):
    top_alumni_db = db.query(models.User).filter(models.User.is_alumni == True).order_by(desc(models.User.likes)).limit(limit * 5).all()
    grouped_alumni_dict: Dict[str, List[models.AlumniResponse]] = {}
    processed_alumni_for_response: List[models.AlumniResponse] = []
    for alumni_db_item in top_alumni_db:
        if len(processed_alumni_for_response) >= limit: break
        try:
            alumni_resp = models.AlumniResponse.model_validate(alumni_db_item)
            if any(pa.id == alumni_resp.id for pa in processed_alumni_for_response): continue
            department_key = alumni_resp.department if alumni_resp.department else "Other"
            grouped_alumni_dict.setdefault(department_key, []).append(alumni_resp)
            processed_alumni_for_response.append(alumni_resp)
        except Exception as e: logger.error(f"Error processing alumni for top-liked: {e}")
    return grouped_alumni_dict

@router.get(f"{BASE_API_PATH}/alumni/{{alumni_id:int}}", response_model=models.AlumniResponse, tags=["Alumni", "API"])
async def get_alumni_by_id_api_profile_router(
    alumni_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_user_from_cookie)
):
    alumnus = db.query(models.User).filter(models.User.id == alumni_id, models.User.is_alumni == True).first()
    if not alumnus: raise HTTPException(status_code=404, detail="Alumnus not found")
    return alumnus

@router.post(f"{BASE_API_PATH}/alumni/{{alumni_id:int}}/like", status_code=status.HTTP_200_OK, tags=["Alumni", "API"])
async def like_alumnus_api_profile_router(
    alumni_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_user_from_cookie)
):
    if alumni_id == current_user.id: raise HTTPException(status_code=400, detail="Cannot like self.")
    alumnus = db.query(models.User).filter(models.User.id == alumni_id, models.User.is_alumni == True).first()
    if not alumnus: raise HTTPException(status_code=404, detail="Alumnus not found.")
    existing_like = db.query(models.AlumniLike).filter(models.AlumniLike.liker_user_id == current_user.id, models.AlumniLike.liked_alumni_id == alumni_id).first()
    if existing_like: return {"likes": alumnus.likes, "message": "Already liked.", "liked": True}
    try:
        new_like = models.AlumniLike(liker_user_id=current_user.id, liked_alumni_id=alumni_id)
        db.add(new_like)
        alumnus.likes = (alumnus.likes or 0) + 1
        db.commit(); db.refresh(alumnus)
        return {"likes": alumnus.likes, "message": "Like recorded.", "liked": True}
    except Exception as e: db.rollback(); logger.error(f"DB error liking alumni: {e}"); raise HTTPException(500, "Could not update like.")

@router.get(f"{BASE_API_PATH}/alumni/me/liked", response_model=List[int], tags=["Alumni", "API"])
async def get_my_liked_alumni_ids_api_profile_router(
    db: Session = Depends(get_db), current_user: models.User = Depends(require_user_from_cookie)
):
    liked_ids_tuples = db.query(models.AlumniLike.liked_alumni_id).filter(models.AlumniLike.liker_user_id == current_user.id).all()
    return [item[0] for item in liked_ids_tuples]