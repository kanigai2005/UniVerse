import json
from datetime import date, datetime, timedelta # timedelta might not be used here but good to have with dates
from typing import Optional

from sqlalchemy.orm import Session

# Relative imports (assuming utils.py is in the root of backend-exp)
import models # To access Notification, User, Hackathon, Job, Internship SQLAlchemy models
from auth_utils import logger # Import the configured logger

# --- JSON Serialization Helper ---
def json_serial(obj: object) -> str:
    """JSON serializer for objects not serializable by default json code, like datetime."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable by json_serial helper")


# --- Notification Creation Helper Functions ---
# These functions add notification objects to the database session but DO NOT COMMIT.
# The calling function should handle the commit after the primary action succeeds.

def create_notification(
    db: Session,
    user_id: int,
    message: str,
    type: str, # e.g., "connection_request", "new_job", "event_reminder"
    related_id: Optional[int] = None, # ID of the related entity (e.g., job_id, connection_id)
    related_url: Optional[str] = None # Optional URL for frontend navigation
):
    """
    Adds a generic notification object to the database session (does not commit).
    """
    try:
        notification = models.Notification(
            user_id=user_id,
            message=message,
            type=type,
            related_id=related_id,
            related_url=related_url # Make sure your Notification model has this field
        )
        db.add(notification)
        logger.debug(f"Notification object created for user {user_id}, type {type}.")
    except Exception as e:
        # Log error but don't raise, as notification failure might not be critical to the main operation
        logger.error(f"Error creating notification object for user {user_id} (type: {type}): {e}", exc_info=True)

def create_new_hackathon_notifications(db: Session, hackathon: models.Hackathon):
    """Adds notifications for all non-admin users about a new hackathon (does not commit)."""
    try:
        # Ensure your User model has 'is_admin' and 'id' attributes
        users_to_notify = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users_to_notify:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Hackathon Alert: '{hackathon.name}' is now available!",
                type="new_hackathon",
                related_id=hackathon.id,
                related_url=f"/user/explore-hackathons.html#hackathon-{hackathon.id}" # Example URL
            )
        logger.info(f"Prepared notifications for new hackathon '{hackathon.name}' for {len(users_to_notify)} users.")
    except Exception as e:
        logger.error(f"Error preparing new hackathon notifications for '{hackathon.name}': {e}", exc_info=True)

def create_new_job_notifications(db: Session, job: models.Job):
    """Adds notifications for all non-admin users about a new job (does not commit)."""
    try:
        users_to_notify = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users_to_notify:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Job Alert: '{job.title}' at {job.company or 'Unknown Company'}!",
                type="new_job",
                related_id=job.id,
                related_url=f"/user/explore.html#job-{job.id}" # Example URL
            )
        logger.info(f"Prepared notifications for new job '{job.title}' for {len(users_to_notify)} users.")
    except Exception as e:
        logger.error(f"Error preparing new job notifications for '{job.title}': {e}", exc_info=True)

def create_new_internship_notifications(db: Session, internship: models.Internship):
    """Adds notifications for all non-admin users about a new internship (does not commit)."""
    try:
        users_to_notify = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users_to_notify:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Internship Opportunity: '{internship.title}' at {internship.company or 'Unknown Company'}!",
                type="new_internship",
                related_id=internship.id,
                related_url=f"/user/internship.html#internship-{internship.id}" # Example URL
            )
        logger.info(f"Prepared notifications for new internship '{internship.title}' for {len(users_to_notify)} users.")
    except Exception as e:
        logger.error(f"Error preparing new internship notifications for '{internship.title}': {e}", exc_info=True)

# You can add other general utility functions here as your project grows.
# For example, a function to generate slugs, format dates in specific ways, etc.

# Example of the manual password update utility (if you decide to keep it and not put it in an admin script)
# This should be used with extreme caution and ideally through a secure admin interface.
def utility_update_user_password(username_or_email: str, new_password: str, db: Session): # Takes db session as arg now
    """
    Utility to update a user's password.
    This is intended for admin use or recovery, NOT as a regular API endpoint.
    Caller is responsible for providing the db session and committing/rolling back.
    """
    if len(new_password) < 8:
        logger.error(f"[ADMIN_UTIL] New password for '{username_or_email}' is too short. Not updated.")
        return False

    from .auth_utils import hash_password # Import hash_password here to avoid circular dependency if auth_utils imports utils

    user_to_update = db.query(models.User).filter(
        (models.User.username == username_or_email) | (models.User.email == username_or_email)
    ).first()

    if user_to_update:
        try:
            hashed = hash_password(new_password)
            user_to_update.hashed_password = hashed
            user_to_update.updated_at = datetime.utcnow()
            # The caller will handle db.commit()
            logger.info(f"[ADMIN_UTIL] Password prepared for update for user '{user_to_update.username}'. Commit externally.")
            return True
        except Exception as e:
            logger.error(f"[ADMIN_UTIL] Error preparing password update for '{username_or_email}': {e}")
            return False
    else:
        logger.warning(f"[ADMIN_UTIL] User '{username_or_email}' not found. No password updated.")
        return False