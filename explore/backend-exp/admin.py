# backend-exp/admin.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from fastapi.responses import HTMLResponse # RedirectResponse not used directly here
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional, Any # Any for get_unverified_items_admin_api return
from datetime import datetime

# --- Imports from Sibling Files ---
from .models import (
    User, Job, Internship, CareerFair, Hackathon, UserIssue,
    UnverifiedJob, UnverifiedInternship, UnverifiedCareerFair, UnverifiedHackathon,
    get_db, # Database session dependency
    UserResponse, UserIssueResponse, # Pydantic models for responses
    UnverifiedJobOut, UnverifiedInternshipOut, UnverifiedCareerFairOut, UnverifiedHackathonOut,
    JobOut, InternshipOut, CareerFairOut, HackathonOut, # For potential direct admin CRUD responses
    JobCreate, InternshipCreate, CareerFairCreate, HackathonCreate, # For potential direct admin CRUD bodies
    UserStatusUpdate, UserRoleUpdate,UserActivityUpdate # Pydantic for request bodies
)

# Import shared utilities from auth_utils.py
from .auth_utils import require_admin, templates, logger as shared_root_logger

# Use a child logger for admin-specific messages, or use shared_root_logger directly
logger = logging.getLogger("exp.admin")
# Example: if you want all admin logs to go through the root "exp" logger, just use:
# logger = shared_root_logger

# --- Routers ---
admin_html_router = APIRouter(
    tags=["Admin Pages"],
    dependencies=[Depends(require_admin)] # Protect all HTML admin pages
)
admin_api_router = APIRouter(
    prefix="/api/admin",
    tags=["Admin API"],
    dependencies=[Depends(require_admin)] # Protect all admin API endpoints
)

# --- Mock Notification Helpers (or import your actual implementations) ---
def create_new_job_notifications(db: Session, job: Job): logger.info(f"ADMIN: Simulating notification for job: {job.title}")
def create_new_internship_notifications(db: Session, internship: Internship): logger.info(f"ADMIN: Simulating notification for internship: {internship.title}")
def create_new_career_fair_notifications(db: Session, career_fair: CareerFair): logger.info(f"ADMIN: Simulating notification for career fair: {career_fair.name}")
def create_new_hackathon_notifications(db: Session, hackathon: Hackathon): logger.info(f"ADMIN: Simulating notification for hackathon: {hackathon.name}")
def send_email_to_user(email: str, subject: str, body: str): logger.info(f"ADMIN: Simulating email to {email} | Subject: {subject}")


# === Admin HTML Serving Routes ===
@admin_html_router.get("/admin-home.html", response_class=HTMLResponse)
async def admin_home_page_html(request: Request, admin_user: User = Depends(require_admin)):
    if not templates: return HTMLResponse("Server error: Admin page templates not available.", status_code=503)
    return templates.TemplateResponse("admin-home.html", {"request": request, "username": admin_user.username})

@admin_html_router.get("/admin-usermanagement.html", response_class=HTMLResponse)
async def admin_user_management_page_html(request: Request, admin_user: User = Depends(require_admin)):
    if not templates: return HTMLResponse("Server error: Admin page templates not available.", status_code=503)
    return templates.TemplateResponse("admin-usermanagement.html", {"request": request, "username": admin_user.username})

@admin_html_router.get("/admin-eventmanagement.html", response_class=HTMLResponse)
async def admin_event_management_page_html(request: Request, admin_user: User = Depends(require_admin)):
    if not templates: return HTMLResponse("Server error: Admin page templates not available.", status_code=503)
    return templates.TemplateResponse("admin-eventmanagement.html", {"request": request, "username": admin_user.username})

@admin_html_router.get("/admin-feedback.html", response_class=HTMLResponse)
async def admin_feedback_page_html(request: Request, admin_user: User = Depends(require_admin)):
    if not templates: return HTMLResponse("Server error: Admin page templates not available.", status_code=503)
    return templates.TemplateResponse("admin-feedback.html", {"request": request, "username": admin_user.username})


# === Admin API: Submission Management ===
@admin_api_router.get("/unverified-items", response_model=List[Any], summary="Get Unverified Submissions")
async def get_unverified_items_admin_api(
    type: str = Query(..., description="Type: job, internship, career-fair, hackathon"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' fetching unverified '{type}' items.")
    model_map = {
        "job": (UnverifiedJob, UnverifiedJobOut), "internship": (UnverifiedInternship, UnverifiedInternshipOut),
        "career-fair": (UnverifiedCareerFair, UnverifiedCareerFairOut), "hackathon": (UnverifiedHackathon, UnverifiedHackathonOut)
    }
    if type not in model_map: raise HTTPException(status_code=400, detail="Invalid item type")
    DbModel, PydanticOutModel = model_map[type]
    items_orm = db.query(DbModel).filter(DbModel.status == 'pending').order_by(desc(DbModel.submitted_at)).all()
    return [PydanticOutModel.model_validate(item) for item in items_orm]

@admin_api_router.post("/unverified-items/{item_id}/approve", summary="Approve Submission")
async def approve_submission_admin_api(
    item_id: int, type: str = Query(...), db: Session = Depends(get_db), admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' approving {type} ID: {item_id}")
    unverified_model_map = {"job": UnverifiedJob, "internship": UnverifiedInternship, "career-fair": UnverifiedCareerFair, "hackathon": UnverifiedHackathon}
    verified_model_map = {"job": Job, "internship": Internship, "career-fair": CareerFair, "hackathon": Hackathon}
    notification_map = {"job": create_new_job_notifications, "internship": create_new_internship_notifications, "career-fair": create_new_career_fair_notifications, "hackathon": create_new_hackathon_notifications}

    if type not in unverified_model_map: raise HTTPException(status_code=400, detail="Invalid item type")
    UnverifiedDbModel = unverified_model_map[type]; VerifiedDbModel = verified_model_map[type]
    unverified_item = db.query(UnverifiedDbModel).filter(UnverifiedDbModel.id == item_id, UnverifiedDbModel.status == 'pending').first()
    if not unverified_item: raise HTTPException(status_code=404, detail="Pending submission not found or already processed")

    verified_item_data = {c.name: getattr(unverified_item, c.name) for c in VerifiedDbModel.__table__.columns if hasattr(unverified_item, c.name) and c.name not in ['id', 'created_at', 'updated_at']}
    if not verified_item_data: raise HTTPException(status_code=500, detail="Internal error mapping data.")
    
    new_verified_item = VerifiedDbModel(**verified_item_data)
    unverified_item.status = 'approved'; unverified_item.updated_at = datetime.utcnow()
    try:
        db.add(new_verified_item); db.add(unverified_item)
        if type in notification_map: notification_map[type](db, new_verified_item)
        db.commit()
        logger.info(f"{type.capitalize()} ID {unverified_item.id} approved. New verified ID: {new_verified_item.id}")
        return {"message": f"{type.capitalize()} (ID: {unverified_item.id}) approved successfully."}
    except Exception as e: db.rollback(); logger.error(f"Error approving {type} ID {item_id}: {e}", exc_info=True); raise HTTPException(500, f"Could not approve {type}")

@admin_api_router.post("/unverified-items/{item_id}/reject", summary="Reject Submission")
async def reject_submission_admin_api(
    item_id: int, type: str = Query(...), db: Session = Depends(get_db), admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' rejecting {type} ID: {item_id}")
    model_map = {"job": UnverifiedJob, "internship": UnverifiedInternship, "career-fair": UnverifiedCareerFair, "hackathon": UnverifiedHackathon}
    if type not in model_map: raise HTTPException(status_code=400, detail="Invalid item type")
    UnverifiedDbModel = model_map[type]
    item = db.query(UnverifiedDbModel).filter(UnverifiedDbModel.id == item_id, UnverifiedDbModel.status == 'pending').first()
    if not item: raise HTTPException(status_code=404, detail="Pending submission not found or already processed")
    item.status = 'rejected'; item.updated_at = datetime.utcnow()
    try:
        db.commit()
        logger.info(f"{type.capitalize()} ID {item_id} rejected.")
        return {"message": f"{type.capitalize()} (ID: {item_id}) rejected successfully."}
    except Exception as e: db.rollback(); logger.error(f"Error rejecting {type} ID {item_id}: {e}", exc_info=True); raise HTTPException(500, f"Could not reject {type}")

# admin.py
# ... (other imports: User, Job, JobCreate, JobOut, Internship, InternshipCreate, InternshipOut, etc. from models)

# === Admin API: Direct Creation of Verified Items ===

@admin_api_router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED, summary="Admin Create New Job")
async def admin_create_job_api( # Renamed to avoid conflict
    job_data: JobCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' directly creating job: {job_data.title}")
    # The Pydantic model JobCreate should have all necessary fields for a Job
    # Default created_at/updated_at will be handled by DB/SQLAlchemy if defaults are set
    new_job = Job(**job_data.model_dump(exclude_unset=True)) # Use exclude_unset for optional fields
    try:
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        create_new_job_notifications(db, new_job) # Notify users after successful commit
        db.commit() # Commit again if notifications made DB changes (usually not if just logging)
        return new_job
    except Exception as e:
        db.rollback()
        logger.error(f"Admin error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create job.")
@admin_api_router.post("/internships", response_model=InternshipOut, status_code=status.HTTP_201_CREATED, summary="Admin Create New Internship")
async def admin_create_internship_api(
    internship_data: InternshipCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' directly creating internship: {internship_data.title}")
    new_internship = Internship(**internship_data.model_dump(exclude_unset=True))
    try:
        db.add(new_internship)
        db.commit()
        db.refresh(new_internship)
        create_new_internship_notifications(db, new_internship)
        db.commit()
        return new_internship
    except Exception as e:
        db.rollback()
        logger.error(f"Admin error creating internship: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create internship.")

@admin_api_router.post("/career-fairs", response_model=CareerFairOut, status_code=status.HTTP_201_CREATED, summary="Admin Create New Career Fair")
async def admin_create_career_fair_api(
    career_fair_data: CareerFairCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' directly creating career fair: {career_fair_data.name}")
    new_career_fair = CareerFair(**career_fair_data.model_dump(exclude_unset=True))
    try:
        db.add(new_career_fair)
        db.commit()
        db.refresh(new_career_fair)
        create_new_career_fair_notifications(db, new_career_fair)
        db.commit()
        return new_career_fair
    except Exception as e:
        db.rollback()
        logger.error(f"Admin error creating career fair: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create career fair.")

@admin_api_router.post("/hackathons", response_model=HackathonOut, status_code=status.HTTP_201_CREATED, summary="Admin Create New Hackathon")
async def admin_create_hackathon_api(
    hackathon_data: HackathonCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    logger.info(f"Admin '{admin_user.username}' directly creating hackathon: {hackathon_data.name}")
    new_hackathon = Hackathon(**hackathon_data.model_dump(exclude_unset=True))
    try:
        db.add(new_hackathon)
        db.commit()
        db.refresh(new_hackathon)
        create_new_hackathon_notifications(db, new_hackathon)
        db.commit()
        return new_hackathon
    except Exception as e:
        db.rollback()
        logger.error(f"Admin error creating hackathon: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create hackathon.")



# ... (rest of your admin.py: submission approval/rejection, user management, feedback management API endpoints)

# === Admin API: User Management ===
# admin.py
# ... (imports for User, UserResponse, UserStatusUpdate, UserRoleUpdate, get_db, require_admin, etc. from .models and .auth_utils)
# ... (admin_api_router definition)

# === Admin API: User Management ===
@admin_api_router.get("/users", response_model=List[UserResponse], summary="List Users (Admin)")
async def list_users_admin_api(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    include_inactive: bool = Query(False, description="Set to true to include deactivated users"), # New filter
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    query = db.query(User)
    if not include_inactive:
        query = query.filter(User.is_active == True) # Default to only active users
    if search:
        query = query.filter(or_(User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
    users = query.order_by(User.username).offset(skip).limit(limit).all()
    return users

@admin_api_router.put("/users/{user_id}/status", response_model=UserResponse, summary="Approve User as Student/Alumni")
async def update_user_status_admin_api(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user_to_update.is_active: # Can only change status of active users
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update status of a deactivated user. Activate first.")

    update_data = status_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No status changes provided.")
    
    logger.info(f"Admin '{admin_user.username}' updating student/alumni status for user ID {user_id} with: {update_data}")
    if update_data.get('is_student') is True:
        user_to_update.is_student = True
        user_to_update.is_alumni = False # Assuming mutually exclusive for simplicity
    if update_data.get('is_alumni') is True:
        user_to_update.is_alumni = True
        user_to_update.is_student = False

    user_to_update.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(user_to_update)
        return user_to_update
    except Exception as e:
        db.rollback(); logger.error(f"Error updating user status ID {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update user status.")

@admin_api_router.put("/users/{user_id}/role", response_model=UserResponse, summary="Update User Admin Role")
async def update_user_role_admin_api(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    if admin_user.id == user_id and role_update.is_admin is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot revoke their own admin status.")
        
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user_to_update.is_active and role_update.is_admin is True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot make a deactivated user an admin. Activate first.")

    update_data = role_update.model_dump(exclude_unset=True)
    if 'is_admin' in update_data:
        user_to_update.is_admin = update_data['is_admin']
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No admin role change provided.")
        
    user_to_update.updated_at = datetime.utcnow()
    try:
        db.commit(); db.refresh(user_to_update)
        logger.info(f"Admin '{admin_user.username}' updated admin role for user ID {user_id} to is_admin={user_to_update.is_admin}")
        return user_to_update
    except Exception as e:
        db.rollback(); logger.error(f"Error updating user role ID {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update user role.")

@admin_api_router.put("/users/{user_id}/activity", response_model=UserResponse, summary="Activate or Deactivate User")
async def update_user_activity_admin_api(
    user_id: int,
    activity_update: UserActivityUpdate, # Expects {"is_active": true/false}
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    if admin_user.id == user_id and not activity_update.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot deactivate themselves.")

    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user_to_update.is_admin and not activity_update.is_active:
        # Prevent deactivating other admins unless you have super-admin logic
        if user_id != admin_user.id : # an admin can deactivate another admin if they are not themselves
             pass # Allow deactivating other admins
        else: # This case is already handled above, but for clarity
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate an admin account this way (or self).")


    user_to_update.is_active = activity_update.is_active
    if not activity_update.is_active: # If deactivating, also remove admin, student, alumni roles
        user_to_update.is_admin = False
        user_to_update.is_student = False
        user_to_update.is_alumni = False
        
    user_to_update.updated_at = datetime.utcnow()
    action = "activated" if activity_update.is_active else "deactivated"
    try:
        db.commit(); db.refresh(user_to_update)
        logger.info(f"Admin '{admin_user.username}' {action} user ID {user_id} (Username: {user_to_update.username})")
        return user_to_update
    except Exception as e:
        db.rollback(); logger.error(f"Error {action} user ID {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not {action} user.")

# REMOVE the old @admin_api_router.delete(...) endpoint if it still exists.

# ... (rest of your admin API endpoints: submissions, feedback)



# ... (rest of your admin.py: submission management, feedback management, etc.)
# === Admin API: Feedback (User Issues) Management ===
@admin_api_router.get("/issues", response_model=List[UserIssueResponse], summary="Get User Issues")
async def get_all_issues_admin_api(status_filter: Optional[str] = Query(None), db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    query = db.query(UserIssue)
    if status_filter:
        query = query.filter(UserIssue.status == status_filter)
    issues = query.order_by(desc(UserIssue.submitted_at)).all()
    return issues

@admin_api_router.put("/issues/{issue_id}/status", response_model=UserIssueResponse, summary="Update Issue Status")
async def update_issue_status_admin_api(
    issue_id: int,
    new_status: str = Body(..., embed=True, description="New status (e.g., pending, investigating, resolved, completed)"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    issue = db.query(UserIssue).filter(UserIssue.id == issue_id).first()
    if not issue: raise HTTPException(status_code=404, detail="Issue not found.")
    valid_statuses = ["pending", "investigating", "resolved", "closed", "completed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    issue.status = new_status
    issue.updated_at = datetime.utcnow()
    try:
        db.commit(); db.refresh(issue)
        logger.info(f"Admin '{admin_user.username}' updated status of issue ID {issue_id} to '{new_status}'.")
        if new_status in ["completed", "resolved"] and issue.email:
             send_email_to_user(issue.email, f"Update on your inquiry (ID: {issue.id})", f"The status of your issue (ID: {issue.id}) has been updated to: {new_status}.")
        return issue
    except Exception as e:
        db.rollback(); logger.error(f"Error updating issue status ID {issue_id}: {e}", exc_info=True)
        raise HTTPException(500, "Could not update issue status.")