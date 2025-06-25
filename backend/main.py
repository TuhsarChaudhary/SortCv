import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from app.api.endpoints import auth, users, resume_parser, shortlist
from app.db.database import Base, engine
from app.scripts.create_admin import create_admin

from dotenv import load_dotenv
load_dotenv()

from app.middleware.log_response_time import LogResponseTimeMiddleware
from app.middleware.error_notifier import ErrorNotifierMiddleware

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CvSorter"
)

@app.on_event("startup")
def startup_admin_check():
    if os.getenv("ENSURE_ADMIN_ON_STARTUP", "false").lower() == "true":
        create_admin()

# Configure CORS
# CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Custom middlewares
app.add_middleware(LogResponseTimeMiddleware)
app.add_middleware(ErrorNotifierMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(resume_parser.router, prefix="/api/resume", tags=["Resume Parsing"])
app.include_router(shortlist.router, prefix="/api/shortlisting", tags=["Shortlisting"])


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI backend!"}
