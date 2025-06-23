from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional, Union
import pandas as pd
import os
import shutil
from pathlib import Path
from app.services import shortlist_service
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.resume_pdf import ResumePDF
from app.core.security import get_current_cv_user
from app.models.user import User

router = APIRouter()

MEDIA_FOLDER = os.path.join("app", "static", "media_files")


os.makedirs(MEDIA_FOLDER, exist_ok=True)



@router.post("/shortlist")
async def shortlist_candidates(
    pdf_id: int = Form(...),
    jd_file: UploadFile = File(...),
    skills: Union[List[str], str] = Form(...),
    experience: Optional[int] = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user),
):

    # Parse skills list from form
    if isinstance(skills, str):
        skills_parsed = [s.strip() for s in skills.strip("[]").split(",") if s.strip()]
    else:
        skills_parsed = skills

    filters = {"skills": skills_parsed, "experience": experience}

    try:
        return shortlist_service.shortlist(
            pdf_id=pdf_id,
            jd_file_bytes=await jd_file.read(),
            jd_filename=jd_file.filename,
            filters=filters,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shortlisting failed: {str(e)}")
