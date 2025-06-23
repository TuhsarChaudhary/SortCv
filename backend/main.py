from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from app.api.endpoints import auth, users, resume_parser, shortlist
from app.db.database import Base, engine

from dotenv import load_dotenv
load_dotenv()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CvSorter"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(resume_parser.router, prefix="/api/resume", tags=["Resume Parsing"])
app.include_router(shortlist.router, prefix="/api/shortlisting", tags=["Shortlisting"])


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI backend!"}
