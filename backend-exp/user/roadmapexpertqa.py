from sqlite3 import OperationalError
from typing import List, Optional
from datetime import date, datetime, time, timedelta # time object added

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, selectinload # selectinload added
from sqlalchemy import desc

# Relative imports
import models # Access all models
from database import get_db
from auth_utils import require_user_from_cookie, templates, logger
from config import BASE_API_PATH

router = APIRouter()
html_router=APIRouter()
# --- Configuration for Expert Q&A Time Logic ---
EXPERT_QA_SELECTION_TIME = time(20, 0) # 8 PM
EXPERT_QA_SELECTED_COUNT = 5
EXPERT_QA_ANSWERABLE_LIFESPAN_DAYS = 1 # How long a question stays "selected" for answering

# --- HTML Serving Endpoints ---

GEMS_FOR_ASKING_QUESTION = 2 # Example: Gems awarded for asking a question if user is alumni

# --- Helper to log gem awarding (optional, for consistency) ---
def log_gem_award(username: str, gems_awarded: int, new_total: Optional[int], action_description: str, item_details: str = ""):
    details_str = f" ({item_details})" if item_details else ""
    if new_total is not None:
        logger.info(f"Awarded {gems_awarded} alumni_gems to '{username}' for {action_description}{details_str}. New total: {new_total}")
    else:
        logger.warning(f"Attempted to award {gems_awarded} alumni_gems to '{username}' for {action_description}{details_str}, but new total is unknown.")


@router.get("/user/alumni-roadmaps.html", response_class=HTMLResponse, tags=["Pages", "Roadmaps"])
async def serve_alumni_roadmaps_html(request: Request, user: models.User = Depends(require_user_from_cookie)):
     return templates.TemplateResponse("alumni-roadmaps.html", {"request": request, "username": user.username})

@router.get("/user/expertqa.html", response_class=HTMLResponse, tags=["Pages", "Expert Q&A"])
async def serve_expertqa_html(request: Request, user: models.User = Depends(require_user_from_cookie)):
     # This page might need to show different sets of questions based on time
     # We'll pass a flag or the questions directly
     # For now, let's assume it calls the relevant API endpoints from the frontend.
     return templates.TemplateResponse("expertqa.html", {"request": request, "username": user.username})


# --- Helper function to determine if it's "answer time" ---
def is_expert_qa_answer_time() -> bool:
    # This should ideally use server's UTC time and then convert to a target timezone
    # For simplicity, using server's local time.
    now_time = datetime.now().time()
    return now_time >= EXPERT_QA_SELECTION_TIME

# --- Expert Q&A API Endpoints ---

@router.get(f"{BASE_API_PATH}/questions/popular", response_model=List[models.QuestionOut], tags=["Expert Q&A", "API"])
async def get_popular_questions_api(db: Session = Depends(get_db), limit: int = 10):
    logger.info(f"API request for {limit} popular questions.")
    try:
        popular_questions = db.query(models.Question)\
            .options(
                selectinload(models.Question.user),
                selectinload(models.Question.expert_answers).selectinload(models.ExpertQAAnswer.user)
            )\
            .order_by(desc(models.Question.likes), desc(models.Question.created_at))\
            .limit(limit).all()
        return popular_questions
    except Exception as e:
        logger.error(f"Error fetching popular questions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching popular questions.")


@router.get(f"{BASE_API_PATH}/expertqa/questions-for-view", response_model=List[models.QuestionOut], tags=["Expert Q&A", "API"])
async def get_expertqa_questions_for_view(db: Session = Depends(get_db)):
    logger.info("API request for Expert Q&A questions for viewing.")
    now_datetime = datetime.now()
    today = now_datetime.date()
    # Corrected usage of timedelta:
    cutoff_date_for_view = today - timedelta(days=EXPERT_QA_ANSWERABLE_LIFESPAN_DAYS)
    cutoff_date_recent = today - timedelta(days=7)


    query = db.query(models.Question)\
        .options(
            selectinload(models.Question.user),
            selectinload(models.Question.expert_answers).selectinload(models.ExpertQAAnswer.user)
        )

    if is_expert_qa_answer_time():
        logger.info("Expert Q&A answer time: Fetching selected questions.")
        questions = query.filter(models.Question.created_at >= cutoff_date_for_view)\
                         .order_by(desc(models.Question.likes), desc(models.Question.created_at))\
                         .limit(EXPERT_QA_SELECTED_COUNT).all()
    else:
        logger.info("Expert Q&A general viewing time: Fetching broader set of questions.")
        questions = query.filter(models.Question.created_at >= cutoff_date_recent) \
                         .order_by(desc(models.Question.likes), desc(models.Question.created_at))\
                         .limit(20).all()
    if not questions:
        return []
    return questions




@router.get(f"{BASE_API_PATH}/expertqa/answerable-questions", response_model=List[models.QuestionOut], tags=["Expert Q&A", "API"])
async def get_answerable_expert_questions(db: Session = Depends(get_db)):
    logger.info("API request for answerable Expert Q&A questions for alumni.")
    
    if not is_expert_qa_answer_time():
        logger.info("Not yet answer time for selected Expert Q&A questions.")
        return []

    today = datetime.now().date()
    # ***** CORRECTED LINE *****
    cutoff_date = today - timedelta(days=EXPERT_QA_ANSWERABLE_LIFESPAN_DAYS)
    # ***** END OF CORRECTION *****

    try:
        answerable_questions = db.query(models.Question)\
            .options(
                selectinload(models.Question.user),
                selectinload(models.Question.expert_answers).selectinload(models.ExpertQAAnswer.user)
            )\
            .filter(models.Question.created_at >= cutoff_date)\
            .order_by(desc(models.Question.likes), desc(models.Question.created_at))\
            .limit(EXPERT_QA_SELECTED_COUNT).all()

        logger.info(f"Returning {len(answerable_questions)} answerable questions for alumni.")
        return answerable_questions
    except Exception as e:
        logger.error(f"Error fetching answerable questions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error fetching answerable questions.")

# ... (rest of your API endpoints: create_question_api, get_user_questions_api, etc.
#      These other endpoints also use `datetime.utcnow()` or `datetime.now().date()`.
#      Ensure `datetime` is imported and `timezone` is imported if using `datetime.now(timezone.utc)`
#      for timezone-aware datetimes, which is good practice.)



@router.post(f"{BASE_API_PATH}/questions", response_model=models.QuestionOut, status_code=status.HTTP_201_CREATED, tags=["Expert Q&A", "API"])
async def create_question_api(
    question_data: models.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"API POST /questions by '{current_user.username}' with text: '{question_data.question_text[:50]}...'") # Log part of question
    
    db_question = models.Question(
        question_text=question_data.question_text,
        user_id=current_user.id,
        # created_at is likely handled by SQLAlchemy default or database default
    )
    try:
        db.add(db_question)

        # --- AWARD ALUMNI GEMS if the user asking is an alumnus ---
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + GEMS_FOR_ASKING_QUESTION
            # This change to current_user will be committed along with the new question

        db.commit()
        db.refresh(db_question) # Refresh to get ID, created_at, etc.
        
        if current_user.is_alumni: # Refresh user to get updated gem count for logging
            db.refresh(current_user)
            log_gem_award(
                current_user.username,
                GEMS_FOR_ASKING_QUESTION,
                current_user.alumni_gems,
                "asking a question",
                f"QID {db_question.id}"
            )

        # Ensure relationships are loaded if QuestionOut expects them (e.g., user, expert_answers)
        # It's good practice to explicitly load what the Pydantic model needs.
        # If QuestionOut includes user details:
        db.refresh(db_question, ['user']) # Refresh the 'user' relationship on db_question
        
        # Pydantic expects expert_answers to be a list, even if empty.
        # If the relationship isn't automatically initialized as an empty list by SQLAlchemy for new objects:
        if not hasattr(db_question, 'expert_answers') or db_question.expert_answers is None:
             db_question.expert_answers = []
        # If 'expert_answers' is a relationship that needs to be loaded for QuestionOut:
        # You might need selectinload when querying if QuestionOut requires it,
        # but for a newly created question, it will be empty.
        # db.refresh(db_question, ['expert_answers']) # Usually not needed for an empty list on create

        logger.info(f"Question ID {db_question.id} created by '{current_user.username}'.")
        return db_question
    except OperationalError as oe:
        db.rollback()
        logger.error(f"Database OperationalError creating question: {oe}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database issue creating question.")
    except Exception as e:
        db.rollback()
        logger.error(f"Create question DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB error creating question.")

@router.get(f"{BASE_API_PATH}/users/{{username}}/questions", response_model=List[models.QuestionOut], tags=["Expert Q&A", "Users", "API"])
async def get_user_questions_api( # Renamed
    username: str,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_user_from_cookie) # If auth needed
):
    logger.info(f"API request for questions asked by user '{username}'.")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        questions = db.query(models.Question)\
            .filter(models.Question.user_id == user.id)\
            .options(selectinload(models.Question.user), selectinload(models.Question.expert_answers)).order_by(desc(models.Question.created_at)).all()
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions for user '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user questions")

@router.get(f"{BASE_API_PATH}/questions/{{question_id}}", response_model=models.QuestionOut, tags=["Expert Q&A", "API"])
async def get_single_question_api(question_id: int, db: Session = Depends(get_db)): # Renamed
    logger.info(f"API request for question ID {question_id}")
    try:
        question = db.query(models.Question)\
            .options(
                selectinload(models.Question.user),
                selectinload(models.Question.expert_answers).selectinload(models.ExpertQAAnswer.user)
            )\
            .filter(models.Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        return question
    except models.ValidationError as ve: # Pydantic validation error
         logger.error(f"Pydantic Validation Error for question {question_id}: {ve.errors()}", exc_info=False)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data validation error: {ve.errors()}")
    except Exception as e:
        logger.error(f"Error fetching question {question_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching question details")

@router.get(f"{BASE_API_PATH}/questions/me/liked", response_model=List[int], tags=["Expert Q&A", "API"])
async def get_my_liked_question_ids_api( # Renamed
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by {current_user.username} for their liked question IDs.")
    try:
        liked_ids_tuples = db.query(models.QuestionLike.question_id)\
                      .filter(models.QuestionLike.user_id == current_user.id)\
                      .all()
        return [item[0] for item in liked_ids_tuples]
    except Exception as e:
        logger.error(f"Error fetching liked question IDs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve liked questions.")

@router.post(f"{BASE_API_PATH}/questions/{{question_id}}/like", status_code=status.HTTP_200_OK, tags=["Expert Q&A", "API"])
async def toggle_like_question_api( # Renamed
    question_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"API request by '{current_user.username}' to toggle like for question ID {question_id}.")
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    existing_like = db.query(models.QuestionLike).filter(
        models.QuestionLike.user_id == current_user.id,
        models.QuestionLike.question_id == question_id
    ).first()
    try:
        if existing_like:
            db.delete(existing_like)
            db_question.likes = max(0, (db_question.likes or 0) - 1)
            action_message, liked_status = "Like removed.", False
        else:
            new_like = models.QuestionLike(user_id=current_user.id, question_id=question_id)
            db.add(new_like)
            db_question.likes = (db_question.likes or 0) + 1
            action_message, liked_status = "Like added.", True
        db.commit(); db.refresh(db_question)
        return {"message": action_message, "likes": db_question.likes, "liked": liked_status}
    except Exception as e:
        db.rollback()
        logger.error(f"Toggle like DB error for question {question_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update like status.")

@router.post(f"{BASE_API_PATH}/expertqa/answers/{{question_id}}", response_model=models.ExpertQAAnswerOut, status_code=status.HTTP_201_CREATED, tags=["Expert Q&A", "API"])
async def submit_expertqa_answer_api(
    question_id: int,
    answer_data: models.ExpertQAAnswerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"API POST /expertqa/answers/{question_id} by '{current_user.username}'")
    if not current_user.is_alumni:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only alumni can answer expert questions.")

    question_to_answer = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question_to_answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    if not is_expert_qa_answer_time():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="It is not currently time to answer selected Expert Q&A questions.")

    today = datetime.now().date()
    # Corrected usage of timedelta here as well:
    cutoff_date = today - timedelta(days=EXPERT_QA_ANSWERABLE_LIFESPAN_DAYS)
    if question_to_answer.created_at.date() < cutoff_date: # Compare dates if created_at is datetime
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This question is too old to be answered in the current selection.")

    db_answer = models.ExpertQAAnswer(
        question_id=question_id, user_id=current_user.id,
        answer_text=answer_data.answer_text, is_alumni_answer=True
    )
    try:
        db.add(db_answer)
        # Add gem increment logic here if needed
        if current_user.is_alumni:
            current_user.alumni_gems = (current_user.alumni_gems or 0) + 3 # Example: GEMS_FOR_DAILY_SPARK_ANSWER
        db.commit()
        db.refresh(db_answer)
        db.refresh(db_answer.user) # Assuming ExpertQAAnswerOut needs user details
        if current_user.is_alumni:
            db.refresh(current_user) # For logging new gem count
            # log_gem_award(...) # Call your logging helper if you have one
        logger.info(f"Alumnus '{current_user.username}' submitted answer ID {db_answer.id} for question ID {question_id}")
        return db_answer
    except Exception as e:
        db.rollback()
        logger.error(f"Submit EQA answer DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB error submitting answer.")

@router.post(f"{BASE_API_PATH}/expertqa/answers/{{answer_id}}/like", status_code=status.HTTP_200_OK, tags=["Expert Q&A", "API"])
async def like_expertqa_answer_api( # Renamed
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user_from_cookie)
):
    logger.info(f"API POST /expertqa/answers/{answer_id}/like by '{current_user.username}'")
    answer = db.query(models.ExpertQAAnswer).filter(models.ExpertQAAnswer.id == answer_id).first()
    if not answer: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    if answer.user_id == current_user.id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like own answer")

    # Implement one-like-per-user logic if needed for answers too, similar to questions or Daily Spark answers
    # For now, simple increment:
    answer.likes = (answer.likes or 0) + 1
    try:
        db.commit(); db.refresh(answer)
        return {"likes": answer.likes, "message": "Answer liked."} # Added message
    except Exception as e:
        db.rollback(); logger.error(f"Like EQA answer DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB error liking answer")