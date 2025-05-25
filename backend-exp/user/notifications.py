from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse # Only HTMLResponse needed for these HTML pages
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import ( # '..' goes up to backend-exp, then imports from models.py
    User, 
    Notification, NotificationOut, NotificationMarkRead, 
    UserIssue, UserIssueCreate, UserIssueResponse # <--- UserIssueResponse is now correctly imported
)
from database import get_db
from auth_utils import (
    require_user_from_cookie,
    get_current_user_from_cookie, # For optional auth on help submission
    templates,
    logger
)
from config import BASE_API_PATH

router = APIRouter()
html_router=APIRouter()
# --- HTML Serving Endpoints for Notifications Module ---

@router.get("/user/notifications.html", response_class=HTMLResponse, tags=["Pages", "Notifications"])
async def serve_notifications_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("notifications.html", {"request": request, "username": user.username})

@router.get("/user/help.html", response_class=HTMLResponse, tags=["Pages", "Help"])
async def serve_help_html(request: Request): # Help page might be accessible without login
     # If login is required for help page, change to:
     # user: User = Depends(require_user_from_cookie)
     # and pass user.username to template if needed
     return templates.TemplateResponse("help.html", {"request": request})


# --- Notifications API ---
@router.get(f"{BASE_API_PATH}/notifications", response_model=List[NotificationOut], tags=["Notifications", "API"])
async def get_user_notifications(
    only_unread: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by '{current_user.username}' for notifications (unread={only_unread}).")
    try:
        query = db.query(Notification).filter(Notification.user_id == current_user.id)
        if only_unread:
            query = query.filter(Notification.is_read == False)
        notifications = query.order_by(desc(Notification.created_at)).limit(50).all()
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve notifications")

@router.post(f"{BASE_API_PATH}/notifications/mark-read", status_code=status.HTTP_200_OK, tags=["Notifications", "API"])
async def mark_notifications_as_read(
    notification_data: NotificationMarkRead, # Pydantic model for request body
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    if not notification_data.notification_ids:
        return {"message": "No notification IDs provided", "updated_count": 0}

    logger.info(f"API request by '{current_user.username}' to mark notifications read: {notification_data.notification_ids}")
    try:
        update_query = db.query(Notification)\
            .filter(
                Notification.user_id == current_user.id,
                Notification.id.in_(notification_data.notification_ids),
                Notification.is_read == False
            )
        updated_count = update_query.update(
            {"is_read": True, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        logger.info(f"User '{current_user.username}' marked {updated_count} notifications as read.")
        return {"message": f"{updated_count} notifications marked as read", "updated_count": updated_count}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark notifications read DB error for user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update notifications")

# --- Help/Issues API ---
@router.post(f"{BASE_API_PATH}/help/submit-issue", response_model=UserIssueResponse, status_code=status.HTTP_201_CREATED, tags=["Help", "API"])
async def submit_user_issue_report(
    issue_data: UserIssueCreate, # Pydantic model for request body
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_cookie) # Optional auth
):
    user_id = current_user.id if current_user else None
    submitter_log_name = f"User ID {user_id}" if user_id else f"Anonymous ({issue_data.email})"
    logger.info(f"Issue report submission received from {submitter_log_name} for email {issue_data.email}.") # Corrected log message

    db_issue = UserIssue(
        user_id=user_id,
        name=issue_data.name,
        email=issue_data.email,
        message=issue_data.message,
        submitted_at=datetime.utcnow(),
        status='pending'
    )
    try:
        db.add(db_issue); db.commit(); db.refresh(db_issue)
        logger.info(f"Issue report ID {db_issue.id} saved successfully from {submitter_log_name}.")
        return db_issue
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit issue report DB error from {submitter_log_name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not submit issue report")