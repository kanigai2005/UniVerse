import sqlite3 # For IntegrityError specific to Daily Spark question posting
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from jsonschema import ValidationError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func
from sqlalchemy.exc import OperationalError # For get_feed_events

# Relative imports (from .. means one level up from 'user' directory)
from models import DailySparkAnswerVote, DailySparkQuestionOut, FeatureOut, User, Job, Internship, CareerFair, Hackathon, DailySparkQuestion, DailySparkAnswer,  Feature, Event, DailySparkQuestionCreate, DailySparkAnswerOut, DailySparkSubmit,DailySparkAnswerVoteSchema # Import specific models used in this file
from database import get_db
from auth_utils import require_user_from_cookie, templates, logger
from config import BASE_API_PATH

from fastapi import APIRouter

router = APIRouter()
html_router = APIRouter()

# --- HTML Serving Endpoints for Home Module ---

GEMS_FOR_DAILY_SPARK_ANSWER = 3
GEMS_FOR_DAILY_SPARK_UPVOTE = 1

def log_gem_award(username: str, gems_awarded: int, new_total: Optional[int], action_description: str):
    if new_total is not None:
        logger.info(f"Awarded {gems_awarded} alumni_gems to '{username}' for {action_description}. New total: {new_total}")
    else:
        logger.warning(f"Attempted to award {gems_awarded} alumni_gems to '{username}' for {action_description}, but new total is unknown.")

@html_router.get("/home.html", response_class=HTMLResponse, tags=["Pages"])
async def user_home_page(
    request: Request,
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"Type of templates object in user/home.py: {type(templates)}")
    if not templates:
        logger.error("USER HOME: Critical - templates object is None or Falsy!")
    logger.info(f"Serving home page for user '{current_user.username}' (ID: {current_user.id})")
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_id": current_user.id,
        "username": current_user.username,
    })

@html_router.get("/user/admin-home.html", response_class=HTMLResponse, tags=["Pages", "Admin"])
async def admin_home_page( # Renamed to avoid conflict if admin.py has admin_home
    request: Request,
    current_user: User = Depends(require_user_from_cookie)
):
    if not current_user.is_admin:
        logger.warning(f"Non-admin user '{current_user.username}' attempted to access /admin-home.html. Redirecting to /user/home.")
        # Assuming RedirectResponse is available or imported if needed, but HTMLResponse is fine for error page
        return HTMLResponse("Access Denied. You must be an admin.", status_code=status.HTTP_403_FORBIDDEN)
        # Or redirect: return RedirectResponse(url="{BASE_API_PATH}/user/home", status_code=status.HTTP_303_SEE_OTHER)


    logger.info(f"Serving admin home page for admin user '{current_user.username}' (ID: {current_user.id})")
    return templates.TemplateResponse("admin-home.html", { # Ensure admin-home.html is in your templates dir
        "request": request,
        "username": current_user.username,
    })

@html_router.get("/dailyspark.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_daily_spark_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("dailyspark.html", {"request": request, "username": user.username})

@html_router.get("/explore.html", response_class=HTMLResponse, tags=["Pages"])
async def serve_explore_html(request: Request, user: User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("explore.html", {"request": request, "username": user.username})


# --- Feed API ---
@router.get(f"{BASE_API_PATH}/feed/events", response_model=List[Event], tags=["Feed", "API"])
async def get_feed_events(limit_per_type: int = 3, db: Session = Depends(get_db)):
    """
    Compiles a feed of recent events (verified jobs, internships, hackathons).
    Public endpoint. Uses 'start_date' as the common date field for sorting and output.
    """
    logger.info(f"API request for feed events (limit per type: {limit_per_type}).")
    today = date.today()
    feed_items_dicts: List[Dict] = []

    try:
        # === Fetch Recent Verified Jobs ===
        try:
            jobs_db = db.query(Job)\
                .order_by(desc(Job.date_posted), desc(Job.created_at))\
                .limit(limit_per_type).all()
            for j in jobs_db:
                job_relevant_date = None
                if j.date_posted:
                    if isinstance(j.date_posted, datetime): job_relevant_date = j.date_posted.date()
                    elif isinstance(j.date_posted, date): job_relevant_date = j.date_posted
                feed_items_dicts.append({
                    'id': j.id, 'name': j.title, 'description': j.description,
                    'start_date': job_relevant_date, 'location': j.location, 'url': j.url,
                    'type': 'job', 'company': j.company
                })
        except Exception as e_job:
             logger.error(f"Error fetching jobs for feed: {e_job}", exc_info=True)
             logger.warning("Skipping jobs in feed due to error.")

        # === Fetch Upcoming/Ongoing Verified Internships ===
        try:
            internships_db = db.query(Internship)\
                .filter(
                    (Internship.start_date >= today) |
                    (Internship.end_date == None) |
                    (Internship.end_date >= today)
                )\
                .order_by(Internship.start_date.asc().nulls_last(), desc(Internship.created_at))\
                .limit(limit_per_type).all()
            for i in internships_db:
                internship_relevant_date = None
                if i.start_date:
                    if isinstance(i.start_date, datetime): internship_relevant_date = i.start_date.date()
                    elif isinstance(i.start_date, date): internship_relevant_date = i.start_date
                feed_items_dicts.append({
                    'id': i.id, 'name': i.title, 'description': i.description,
                    'start_date': internship_relevant_date, 'location': None, 'url': i.url, # Location might be None for internships
                    'type': 'internship', 'company': i.company
                })
        except Exception as e_internship:
            logger.error(f"Error fetching internships for feed: {e_internship}", exc_info=True)
            logger.warning("Skipping internships in feed due to error.")

        # === Fetch Upcoming Verified Hackathons ===
        try:
            hackathons_db = db.query(Hackathon)\
                .filter(Hackathon.start_date != None, Hackathon.start_date >= today)\
                .order_by(Hackathon.start_date.asc(), desc(Hackathon.created_at))\
                .limit(limit_per_type).all()
            for h in hackathons_db:
                hackathon_relevant_date = None
                if h.start_date:
                    if isinstance(h.start_date, datetime): hackathon_relevant_date = h.start_date.date()
                    elif isinstance(h.start_date, date): hackathon_relevant_date = h.start_date
                feed_items_dicts.append({
                    'id': h.id, 'name': h.name, 'description': h.description,
                    'start_date': hackathon_relevant_date, 'location': h.location, 'url': h.url,
                    'type': 'hackathon', 'company': None # Company might be None for hackathons
                })
        except OperationalError as e_hackathon_op: # More specific error for schema issues
            db.rollback()
            logger.error(f"Database schema error fetching hackathons for feed: {e_hackathon_op}", exc_info=False)
            logger.warning("Skipping hackathons in feed due to database schema error.")
        except Exception as e_hackathon_other:
            logger.error(f"Unexpected error fetching hackathons for feed: {e_hackathon_other}", exc_info=True)
            logger.warning("Skipping hackathons in feed due to unexpected error.")

        feed_items_dicts.sort(key=lambda item: item.get('start_date') if item.get('start_date') is not None else date.min, reverse=True)

        feed_events = []
        try:
            # Ensure Event Pydantic model is correctly defined
            feed_events = [Event(**item) for item in feed_items_dicts]
            logger.info(f"Successfully generated feed with {len(feed_events)} items.")
            return feed_events
        except ValidationError as e_val: # Assuming ValidationError is from Pydantic
            logger.error(f"Pydantic validation error creating Event models for feed: {e_val.errors()}", exc_info=True) # Log Pydantic errors
            # ... (your problematic_items logging)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error processing feed data. Validation failed. Error: {e_val.errors()}"
            )
    except Exception as e_general:
        logger.error(f"Unexpected error generating feed events: {e_general}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generating feed events.")

# --- Features API ---
@router.get(f"{BASE_API_PATH}/features", response_model=List[FeatureOut], tags=["General", "API"])
async def get_features_list(db: Session = Depends(get_db)):
    logger.info("API request for features list.")
    try:
        features = db.query(Feature).order_by(Feature.id.asc()).all()
        return features
    except Exception as e:
        logger.error(f"Error fetching features list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching features list")


# --- Daily Spark API ---
@router.post(f"{BASE_API_PATH}/daily-spark/questions", response_model=DailySparkQuestionOut, status_code=status.HTTP_201_CREATED, tags=["Daily Spark", "API", "Alumni Only"])
async def create_daily_spark_question(
    question_data: DailySparkQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"API POST /daily-spark/questions by '{current_user.username}'")
    if not current_user.is_alumni:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only alumni can post Daily Spark questions.")

    today = date.today()
    DAILY_SPARK_OVERALL_LIMIT = 5
    questions_posted_today_overall_count = db.query(DailySparkQuestion).filter(
        DailySparkQuestion.posted_date == today
    ).count()

    if questions_posted_today_overall_count >= DAILY_SPARK_OVERALL_LIMIT:
        logger.warning(f"Overall daily limit of {DAILY_SPARK_OVERALL_LIMIT} Daily Spark questions reached.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Max {DAILY_SPARK_OVERALL_LIMIT} Daily Spark questions for today already posted.")

    db_spark_question_instance = DailySparkQuestion(
        question=question_data.question_text,
        company=question_data.company,
        role=question_data.role,
        user_id=current_user.id,
        posted_date=today
    )
    try:
        db.add(db_spark_question_instance); db.commit(); db.refresh(db_spark_question_instance)
        if not hasattr(db_spark_question_instance, 'posted_by_alumnus') or not db_spark_question_instance.posted_by_alumnus:
            db_spark_question_instance.posted_by_alumnus = current_user # Ensure relationship is loaded for response
        if not hasattr(db_spark_question_instance, 'answers') or db_spark_question_instance.answers is None:
             db_spark_question_instance.answers = []
        logger.info(f"Alumnus '{current_user.username}' posted Daily Spark question ID {db_spark_question_instance.id}")
        return db_spark_question_instance
    except sqlite3.IntegrityError as ie: # Catch SQLite specific integrity error for unique constraint
        db.rollback()
        if "UNIQUE constraint failed" in str(ie) and "uq_alumni_spark_once_per_day" in str(ie): # Check for your specific constraint name
            logger.warning(f"Alumnus '{current_user.username}' attempted to post Daily Spark again today.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already posted a Daily Spark question today.")
        else:
            logger.error(f"DB integrity error creating Daily Spark question: {ie}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB conflict creating question.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Daily Spark question: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save question.")


@router.get(f"{BASE_API_PATH}/daily-spark/today", response_model=DailySparkQuestionOut, tags=["Daily Spark", "API"])
async def get_todays_daily_spark_question_api(db: Session = Depends(get_db)): # Renamed
    logger.info("API request for today's daily spark question.")
    today = date.today()
    try:
        latest_question = db.query(DailySparkQuestion)\
                            .options(
                                selectinload(DailySparkQuestion.posted_by_alumnus), # User who asked question
                                selectinload(DailySparkQuestion.answers)            # Load answers
                                # NO selectinload(DailySparkAnswer.user/answer_author) needed here
                                # because DailySparkAnswer.user is a simple string column.
                                # If DailySparkAnswerOut needed to show who voted on each answer (from DailySparkAnswerVote):
                                # selectinload(DailySparkQuestion.answers).selectinload(DailySparkAnswer.all_votes).selectinload(DailySparkAnswerVote.voter)
                            )\
                            .filter(DailySparkQuestion.posted_date == today)\
                            .order_by(desc(DailySparkQuestion.created_at))\
                            .first()
        if not latest_question:
            logger.warning("No Daily Spark question posted today, returning latest overall.")
            latest_question = db.query(DailySparkQuestion)\
                                .options(
                                    selectinload(DailySparkQuestion.posted_by_alumnus),
                                    selectinload(DailySparkQuestion.answers)
                                )\
                                .order_by(desc(DailySparkQuestion.posted_date), desc(DailySparkQuestion.created_at))\
                                .first()
            if not latest_question:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Daily Spark question found.")
        return latest_question # Pydantic will map DailySparkAnswer.user string to DailySparkAnswerOut.user
    except Exception as e:
        logger.error(f"Error fetching today's daily spark question: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching daily spark.")

@router.get(f"{BASE_API_PATH}/daily-spark/top-liked", response_model=List[DailySparkQuestionOut], tags=["Daily Spark", "API"])
async def get_top_liked_daily_spark_questions(limit: int = 5, db: Session = Depends(get_db)): # Renamed
    logger.info(f"API request for top {limit} liked daily spark questions.")
    try:
        questions_with_votes = db.query(
                DailySparkQuestion,
                func.sum(DailySparkAnswer.votes).label('total_votes')
            )\
            .outerjoin(DailySparkAnswer, DailySparkQuestion.id == DailySparkAnswer.question_id)\
            .group_by(DailySparkQuestion.id)\
            .order_by(desc('total_votes'))\
            .limit(limit).all()
        top_questions = [q for q, votes in questions_with_votes]
        # Manually eager load relationships for each question if not done by default for the list
        for q_obj in top_questions:
            db.refresh(q_obj, ['answers', 'posted_by_alumnus']) # Example, adjust as needed
        return top_questions
    except Exception as e:
        logger.error(f"Error fetching top liked daily spark questions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching top questions.")

@router.post(f"{BASE_API_PATH}/daily-spark/submit", response_model=DailySparkAnswerOut, status_code=status.HTTP_201_CREATED, tags=["User APIs", "Daily Spark"])
async def submit_user_daily_spark_answer_api(
    data: DailySparkSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by '{current_user.username}' to submit Daily Spark answer.")
    today_question = db.query(DailySparkQuestion).order_by(desc(DailySparkQuestion.created_at)).first()
    if not today_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Today's Daily Spark question not found.")
    
    new_answer = DailySparkAnswer(
        question_id=today_question.id,
        text=data.text,
        user=current_user.username # Storing username string
    )
    try:
        db.add(new_answer)

        # --- AWARD ALUMNI GEMS if user is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_DAILY_SPARK_ANSWER
            # This change will be part of the db.commit() below

        db.commit()
        db.refresh(new_answer)
        if current_user.is_alumni: # Refresh user to get updated gem count for logging
            db.refresh(current_user)
            log_gem_award(current_user.username, GEMS_FOR_DAILY_SPARK_ANSWER, current_user.alumni_gems, "submitting Daily Spark answer", f"QID {today_question.id}")

        logger.info(f"User '{current_user.username}' submitted answer ID {new_answer.id} for Q ID {today_question.id}")
        
        # Prepare the response based on DailySparkAnswerOut
        # If DailySparkAnswerOut expects a User object for 'user', you might need to fetch it or adjust.
        # Since your model stores username as string, and DailySparkAnswerOut likely expects 'user: str', this is fine.
        return new_answer
    except OperationalError as oe: # More specific DB error
        db.rollback()
        logger.error(f"Database OperationalError submitting Daily Spark answer: {oe}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database issue during submission.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit Daily Spark answer DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save submission.")
async def _handle_daily_spark_vote(
    answer_id: int,
    vote_value: int, # +1 for upvote, -1 for downvote
    db: Session,
    current_user: User # This is the User object of the person voting
):
    """Helper function to handle upvoting/downvoting logic."""
    answer = db.query(DailySparkAnswer).filter(DailySparkAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    
    # CORRECTED: Compare the username string from answer.user with current_user.username
    if answer.user == current_user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot vote on your own answer")

    # DailySparkAnswerVote correctly uses user_id (ForeignKey to User table)
    existing_vote = db.query(DailySparkAnswerVote).filter(
        DailySparkAnswerVote.user_id == current_user.id, # current_user.id is correct here
        DailySparkAnswerVote.answer_id == answer_id
    ).first()

    vote_action_message = "Vote processed."
    user_final_vote = vote_value # Default to the current action's vote value

    try:
        if existing_vote:
            if existing_vote.vote_type == vote_value:
                db.delete(existing_vote)
                answer.votes = (answer.votes or 0) - vote_value # Ensure answer.votes is not None
                vote_action_message = "Vote removed."
                user_final_vote = 0 # Vote is removed, so user's effective vote is neutral
            else:
                answer.votes = (answer.votes or 0) - existing_vote.vote_type # Remove old vote
                existing_vote.vote_type = vote_value
                answer.votes = (answer.votes or 0) + vote_value # Add new vote
                vote_action_message = "Vote changed."
                # user_final_vote remains vote_value
        else:
            new_vote_record = DailySparkAnswerVote(
                user_id=current_user.id,
                answer_id=answer_id,
                vote_type=vote_value
            )
            db.add(new_vote_record)
            answer.votes = (answer.votes or 0) + vote_value
            vote_action_message = "Vote recorded."
            # user_final_vote remains vote_value

        db.commit()
        db.refresh(answer)
        logger.info(f"User '{current_user.username}' action: '{vote_action_message}' on answer ID {answer_id}. New total votes: {answer.votes}")
        return {"votes": answer.votes, "message": vote_action_message, "user_vote": user_final_vote}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record vote on answer ID {answer_id} by user '{current_user.username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not record vote.")


@router.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/upvote", status_code=status.HTTP_200_OK, tags=["User APIs", "Daily Spark"])
async def upvote_user_daily_spark_answer_api( # Renamed
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by '{current_user.username}' to upvote Daily Spark answer ID {answer_id}.")
    return await _handle_daily_spark_vote(answer_id, 1, db, current_user)

@router.post(f"{BASE_API_PATH}/daily-spark/answers/{{answer_id}}/downvote", status_code=status.HTTP_200_OK, tags=["User APIs", "Daily Spark"])
async def downvote_user_daily_spark_answer_api( # Renamed
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by '{current_user.username}' to downvote Daily Spark answer ID {answer_id}.")
    return await _handle_daily_spark_vote(answer_id, -1, db, current_user)
