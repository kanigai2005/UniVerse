from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3

app = FastAPI()

# Enable CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "https://your-production-domain.com"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect("explore.db")
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic model for newsletter subscription
class NewsletterSubscription(BaseModel):
    email: EmailStr

@app.get("/")
def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the Explore API! Use the available endpoints to access data."}

@app.get("/api/features")
def get_features():
    """
    Endpoint to fetch all features from the database.
    """
    conn = get_db_connection()
    features = conn.execute("SELECT * FROM features").fetchall()
    conn.close()
    return JSONResponse(content=[dict(feature) for feature in features])

@app.get("/api/features/{feature_id}")
def get_feature_by_id(feature_id: int):
    """
    Endpoint to fetch a specific feature by ID.
    """
    conn = get_db_connection()
    feature = conn.execute("SELECT * FROM features WHERE id = ?", (feature_id,)).fetchone()
    conn.close()
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return JSONResponse(content=dict(feature))

@app.post("/api/newsletter")
def subscribe_newsletter(subscription: NewsletterSubscription):
    """
    Endpoint to handle Monthly Newsletter subscription.
    """
    return {"message": "Subscription successful!", "email": subscription.email}