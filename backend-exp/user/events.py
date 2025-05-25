from typing import List, Optional, Dict, Any # Dict, Any added for get_hackathons
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse # Removed unused response types
from sqlalchemy.orm import Session
from sqlalchemy import desc # asc is used implicitly or can be added
from sqlalchemy.exc import OperationalError # For specific DB errors

# Relative imports (from .. means one level up from 'user' direct
# 
import models # Access all models via models.User, models.JobCreate etc.
from database import get_db
from auth_utils import require_user_from_cookie, templates, logger
from config import BASE_API_PATH

router = APIRouter()
html_router=APIRouter()

# --- HTML Serving Endpoints for Events Module ---

GEMS_FOR_SUBMISSION = 2 

def log_gem_award(username: str, gems_awarded: int, new_total: Optional[int], item_type: str, item_name: str):
    if new_total is not None:
        logger.info(f"Awarded {gems_awarded} alumni_gems to '{username}' for submitting {item_type} '{item_name}'. New total: {new_total}")
    else:
        logger.warning(f"Attempted to award {gems_awarded} alumni_gems to '{username}' for {item_type} '{item_name}', but new total is unknown (user might not have been refreshed).")


def create_notification(db: Session, user_id: int, message: str, type: str, related_id: Optional[int] = None):
    """Adds a notification object to the database session (does not commit)."""
    try:
        notification = models.Notification(
            user_id=user_id,
            message=message,
            type=type,
            related_id=related_id
        )
        db.add(notification)
    except Exception as e:
        # Log error but don't raise, as notification failure might not be critical
        logger.error(f"Error creating notification object for user {user_id}: {e}", exc_info=True)

def create_new_hackathon_notifications(db: Session, hackathon: models.Hackathon):
    """Adds notifications for all non-admin users about a new hackathon (does not commit)."""
    try:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Hackathon Alert: '{hackathon.name}' is now available!",
                type="new_hackathon",
                related_id=hackathon.id
            )
        logger.info(f"Prepared notifications for new hackathon '{hackathon.name}'.")
    except Exception as e:
        logger.error(f"Error preparing hackathon notifications: {e}", exc_info=True)

def create_new_job_notifications(db: Session, job: models.Job):
    """Adds notifications for all non-admin users about a new job (does not commit)."""
    try:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Job Alert: '{job.title}' at {job.company or 'Unknown Company'}!",
                type="new_job",
                related_id=job.id
            )
        logger.info(f"Prepared notifications for new job '{job.title}'.")
    except Exception as e:
        logger.error(f"Error preparing job notifications: {e}", exc_info=True)

def create_new_internship_notifications(db: Session, internship: models.Internship):
    """Adds notifications for all non-admin users about a new internship (does not commit)."""
    try:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        for user in users:
            create_notification(
                db,
                user_id=user.id,
                message=f"New Internship Opportunity: '{internship.title}' at {internship.company or 'Unknown Company'}!",
                type="new_internship",
                related_id=internship.id
            )
        logger.info(f"Prepared notifications for new internship '{internship.title}'.")
    except Exception as e:
        logger.error(f"Error preparing internship notifications: {e}", exc_info=True)




@router.get("/user/career-fairs.html", response_class=HTMLResponse, tags=["Pages", "Events"])
async def serve_career_fairs_html(request: Request, user: models.User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("career-fairs.html", {"request": request, "username": user.username})

@router.get("/user/intership.html", response_class=HTMLResponse, tags=["Pages", "Events"]) # Corrected typo from intership.html
async def serve_internship_html(request: Request, user: models.User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("intership.html", {"request": request, "username": user.username}) # Ensure template is internship.html

@router.get("/user/explore-hackathons.html", response_class=HTMLResponse, tags=["Pages", "Events"])
async def serve_explore_hackathons_html(request: Request, user: models.User = Depends(require_user_from_cookie)): # Renamed function for clarity
     return templates.TemplateResponse("explore-hackathons.html", {"request": request, "username": user.username})


# --- Career Fairs API ---
@router.get(f"{BASE_API_PATH}/career_fairs", response_model=List[models.CareerFairOut], tags=["Career Fairs", "API"])
async def get_career_fairs(upcoming_only: bool = False, db: Session = Depends(get_db)):
    logger.info(f"API request for career fairs (upcoming_only={upcoming_only}).")
    try:
        query = db.query(models.CareerFair)
        if upcoming_only:
            query = query.filter(models.CareerFair.start_date >= date.today())
        career_fairs = query.order_by(models.CareerFair.start_date.asc()).all()
        return career_fairs
    except Exception as e:
        logger.error(f"Error fetching career fairs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error fetching career fairs")

@router.post(f"{BASE_API_PATH}/career_fairs", response_model=models.UnverifiedCareerFairOut, status_code=status.HTTP_201_CREATED, tags=["Career Fairs", "Submissions"])
async def submit_career_fair_for_verification(
    career_fair_data: models.CareerFairCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"User '{current_user.username}' submitting career fair '{career_fair_data.name}' for verification.")
    db_unverified_fair = models.UnverifiedCareerFair(
        **career_fair_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.now(timezone.utc), # Use timezone-aware UTC
        status='pending'
    )
    try:
        db.add(db_unverified_fair)

        # --- AWARD ALUMNI GEMS if user is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_SUBMISSION

        db.commit()
        db.refresh(db_unverified_fair)
        if current_user.is_alumni:
            db.refresh(current_user)
            log_gem_award(current_user.username, GEMS_FOR_SUBMISSION, current_user.alumni_gems, "career fair", db_unverified_fair.name)

        logger.info(f"Career fair '{db_unverified_fair.name}' (Unverified ID: {db_unverified_fair.id}) submitted by '{current_user.username}'.")
        return db_unverified_fair
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database schema/operational error submitting career fair '{career_fair_data.name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during career fair submission.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit career fair '{career_fair_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save career fair submission.")



# --- Jobs API ---
@router.get(f"{BASE_API_PATH}/jobs", response_model=List[models.JobOut], tags=["Jobs", "API"])
async def get_jobs(db: Session = Depends(get_db)):
    logger.info("API request for jobs.")
    try:
        jobs = db.query(models.Job).order_by(desc(models.Job.date_posted), desc(models.Job.created_at)).all()
        return jobs
    except OperationalError as e:
        logger.error(f"Database schema mismatch fetching jobs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB error fetching jobs. Schema might be outdated.")
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching job listings")

@router.post(f"{BASE_API_PATH}/jobs", response_model=models.UnverifiedJobOut, status_code=status.HTTP_201_CREATED, tags=["Jobs", "Submissions"])
async def submit_job_for_verification(
    job_data: models.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"User '{current_user.username}' submitting job '{job_data.title}' for verification.")
    db_unverified_job = models.UnverifiedJob(
        **job_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.now(timezone.utc), # Use timezone-aware UTC
        status='pending'
    )
    try:
        db.add(db_unverified_job)

        # --- AWARD ALUMNI GEMS if user is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_SUBMISSION
            # No separate commit for gems needed here, it will be part of the main commit

        db.commit()
        db.refresh(db_unverified_job)
        if current_user.is_alumni: # Refresh user to get updated gem count for logging
            db.refresh(current_user)
            log_gem_award(current_user.username, GEMS_FOR_SUBMISSION, current_user.alumni_gems, "job", db_unverified_job.title)

        logger.info(f"Job '{db_unverified_job.title}' (Unverified ID: {db_unverified_job.id}) submitted by '{current_user.username}'.")
        return db_unverified_job
    except OperationalError as e: # Catch specific DB schema/connection errors
        db.rollback()
        logger.error(f"Database schema/operational error submitting job '{job_data.title}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during job submission.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit job '{job_data.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save job submission.")

# --- Internships API ---
@router.get(f"{BASE_API_PATH}/internships", response_model=List[models.InternshipOut], tags=["Internships", "API"])
async def get_internships(upcoming_only: bool = True, db: Session = Depends(get_db)):
    logger.info(f"API request for internships (upcoming_only={upcoming_only}).")
    try:
        query = db.query(models.Internship)
        if upcoming_only:
            today = date.today()
            query = query.filter(
                (models.Internship.start_date >= today) |
                (models.Internship.end_date == None) |
                (models.Internship.end_date >= today)
            )
        internships = query.order_by(models.Internship.start_date.asc()).all()
        return internships
    except Exception as e:
        logger.error(f"Error fetching internships: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error fetching internships")

@router.post(f"{BASE_API_PATH}/internships", response_model=models.UnverifiedInternshipOut, status_code=status.HTTP_201_CREATED, tags=["Internships", "Submissions"])
async def submit_internship_for_verification(
    internship_data: models.InternshipCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"User '{current_user.username}' submitting internship '{internship_data.title}' for verification.")
    db_unverified_internship = models.UnverifiedInternship(
        **internship_data.model_dump(),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.now(timezone.utc), # Use timezone-aware UTC
        status='pending'
    )
    try:
        db.add(db_unverified_internship)

        # --- AWARD ALUMNI GEMS if user is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_SUBMISSION

        db.commit()
        db.refresh(db_unverified_internship)
        if current_user.is_alumni:
            db.refresh(current_user)
            log_gem_award(current_user.username, GEMS_FOR_SUBMISSION, current_user.alumni_gems, "internship", db_unverified_internship.title)

        logger.info(f"Internship '{db_unverified_internship.title}' (Unverified ID: {db_unverified_internship.id}) submitted by '{current_user.username}'.")
        return db_unverified_internship
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database schema/operational error submitting internship '{internship_data.title}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during internship submission.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit internship '{internship_data.title}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save internship submission.")

# --- Hackathons API ---
@router.get(f"{BASE_API_PATH}/hackathons", response_model=List[models.HackathonOut], tags=["Hackathons", "API"]) # Re-added response_model assuming HackathonOut is correctly defined
async def get_hackathons(upcoming_only: bool = True, db: Session = Depends(get_db)):
    logger.info(f"API GET /hackathons (upcoming={upcoming_only})")
    try:
        query = db.query(models.Hackathon)
        if upcoming_only:
            today = date.today()
            query = query.filter(models.Hackathon.start_date != None, models.Hackathon.start_date >= today)
        hackathons_db = query.order_by(models.Hackathon.start_date.asc()).all()

        # If HackathonOut is well-defined and handles potential None values for dates,
        # direct return should work. If you were manually creating dicts due to Pydantic issues,
        # ensure HackathonOut fields are Optional or have defaults.
        return hackathons_db
    except Exception as e:
         logger.error(f"Error fetching hackathons: {e}", exc_info=True)
         # Check if e is a Pydantic ValidationError if response_model is used
         if isinstance(e, models.ValidationError): # Assuming ValidationError is from pydantic
             logger.error(f"Pydantic validation error for hackathons: {e.errors()}", exc_info=False)
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data validation error for hackathons: {e.errors()}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error preparing hackathon data")

@router.post(f"{BASE_API_PATH}/hackathons", response_model=models.UnverifiedHackathonOut, status_code=status.HTTP_201_CREATED, tags=["Hackathons", "Submissions"])
async def submit_hackathon_for_verification(
    hackathon_data: models.HackathonCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"User '{current_user.username}' submitting hackathon '{hackathon_data.name}' for verification.")
    db_unverified_hackathon = models.UnverifiedHackathon(
        **hackathon_data.model_dump(exclude_unset=True),
        submitted_by_user_id=current_user.id,
        submitted_at=datetime.now(timezone.utc), # Use timezone-aware UTC
        status='pending'
    )
    try:
        db.add(db_unverified_hackathon)

        # --- AWARD ALUMNI GEMS if user is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_SUBMISSION

        db.commit()
        db.refresh(db_unverified_hackathon)
        if current_user.is_alumni:
            db.refresh(current_user)
            log_gem_award(current_user.username, GEMS_FOR_SUBMISSION, current_user.alumni_gems, "hackathon", db_unverified_hackathon.name)

        logger.info(f"Hackathon '{db_unverified_hackathon.name}' (Unverified ID: {db_unverified_hackathon.id}) submitted by '{current_user.username}'.")
        return db_unverified_hackathon
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database schema/operational error submitting hackathon '{hackathon_data.name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during hackathon submission.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit hackathon '{hackathon_data.name}' DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save hackathon submission.")