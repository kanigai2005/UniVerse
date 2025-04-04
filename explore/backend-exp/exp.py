from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date, datetime
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import uvicorn

app = FastAPI()

# Construct the correct path to the frontend-exp directory
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend-exp")

# Construct paths to HTML files
explore_html_path = os.path.join(frontend_dir, "explore.html")
career_fairs_html_path = os.path.join(frontend_dir, "career-fairs.html")
expertqa_html_path = os.path.join(frontend_dir, "expertqa.html")
explore_hackathon_html_path = os.path.join(frontend_dir, "explore-hackathons.html")
internship_html_path = os.path.join(frontend_dir, "intership.html")
leader_profile_html_path = os.path.join(frontend_dir, "leader-profile.html")
leaderboard_html_path = os.path.join(frontend_dir, "leaderboard.html")

# Serve static files (e.g., JavaScript, CSS)
static_dir = os.path.join(frontend_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve HTML files
@app.get("/")
async def serve_explore_html():
    return FileResponse(explore_html_path)

@app.get("/career-fairs.html")
async def serve_career_fairs_html():
    return FileResponse(career_fairs_html_path)

@app.get("/expertqa.html")
async def serve_expertqa_html():
    return FileResponse(expertqa_html_path)

@app.get("/explore-hackathons.html")
async def serve_explore_hackathon_html():
    return FileResponse(explore_hackathon_html_path)

@app.get("/internship.html")
async def serve_internship_html():
    return FileResponse(internship_html_path)

@app.get("/leader-profile.html")
async def serve_leader_profile_html():
    return FileResponse(leader_profile_html_path)

@app.get("/leaderboard.html")
async def serve_leaderboard_html():
    return FileResponse(leaderboard_html_path)

# Database setup
DATABASE_URL = "sqlite:///explore.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    activity_score = Column(Integer)
    achievements = Column(Text)
    alumni_gems = Column(Integer)

class CareerFair(Base):
    __tablename__ = "career_fairs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    location = Column(String)
    description = Column(Text)

class Internship(Base):
    __tablename__ = "internships"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)

class Hackathon(Base):
    __tablename__ = "hackathons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    location = Column(String)
    description = Column(Text)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Initialization Function
async def initialize_database():
    def sync_init():
        db = SessionLocal()
        try:
            if not db.query(User).first():
                db.add_all([
                    User(name="Alex Johnson", email="alex@example.com", activity_score=50, achievements="Mentorship Pro, Top Contributor", alumni_gems=10),
                    User(name="Sarah Lee", email="sarah@example.com", activity_score=42, achievements="Job Connector", alumni_gems=8),
                    User(name="Michael Carter", email="michael@example.com", activity_score=38, achievements="Mentor Pro", alumni_gems=5),
                ])
            if not db.query(CareerFair).first():
                db.add_all([
                    CareerFair(name="Tech Career Fair", date=datetime.strptime("2024-12-15", "%Y-%m-%d").date(), location="San Francisco", description="Meet top tech companies."),
                    CareerFair(name="Engineering Jobs", date=datetime.strptime("2025-01-10", "%Y-%m-%d").date(), location="New York", description="Find engineering jobs."),
                ])
            if not db.query(Internship).first():
                db.add_all([
                    Internship(title="Software Dev Intern", company="Google", start_date=datetime.strptime("2024-12-01", "%Y-%m-%d").date(), end_date=datetime.strptime("2025-03-01", "%Y-%m-%d").date(), description="Work on cool projects."),
                    Internship(title="Data Science Intern", company="Amazon", start_date=datetime.strptime("2025-01-15", "%Y-%m-%d").date(), end_date=datetime.strptime("2025-04-15", "%Y-%m-%d").date(), description="Analyze large datasets."),
                ])
            if not db.query(Hackathon).first():
                db.add_all([
                    Hackathon(name="AI Hackathon", date=datetime.strptime("2024-12-10", "%Y-%m-%d").date(), location="Online", description="Develop innovative AI solutions."),
                    Hackathon(name="Web Dev Challenge", date=datetime.strptime("2025-01-20", "%Y-%m-%d").date(), location="San Francisco", description="Showcase your web development skills."),
                ])
            db.commit()
        finally:
            db.close()
    asyncio.run(asyncio.to_thread(sync_init))

# API Routes
BASE_API_PATH = "/api"

@app.get(f"{BASE_API_PATH}/career_fairs")
async def get_career_fairs(db: Session = Depends(get_db)):
    career_fairs = db.query(CareerFair).filter(CareerFair.date >= date.today()).order_by(CareerFair.date).all()
    return career_fairs

@app.get(f"{BASE_API_PATH}/internships")
async def get_internships(db: Session = Depends(get_db)):
    internships = db.query(Internship).filter(Internship.start_date >= date.today()).order_by(Internship.start_date).all()
    return internships

@app.get(f"{BASE_API_PATH}/hackathons")
async def get_hackathons(db: Session = Depends(get_db)):
    hackathons = db.query(Hackathon).filter(Hackathon.date >= date.today()).order_by(Hackathon.date).all()
    return hackathons

@app.get(f"{BASE_API_PATH}/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.activity_score.desc(), User.alumni_gems.desc()).all()
    return [
        {
            "name": user.name,
            "activity_score": user.activity_score,
            "achievements": user.achievements.split(",") if user.achievements else [],
            "alumni_gems": user.alumni_gems
        }
        for user in users
    ]

@app.get(f"{BASE_API_PATH}/user/{{username}}")
async def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "name": user.name,
        "email": user.email,
        "activity_score": user.activity_score,
        "achievements": user.achievements.split(",") if user.achievements else [],
        "alumni_gems": user.alumni_gems
    }

async def main():
    await initialize_database()
    uvicorn.run("exp:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())