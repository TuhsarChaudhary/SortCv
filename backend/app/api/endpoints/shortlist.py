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
    # required_experience: int = Form(...),
    # required_degree: str = Form(...),
    jd_file: UploadFile = File(...),
    jd_template: str = Form(...),
    # search_query: str = Form(""),
    # search_operator: str = Form("OR"),
    weight_experience: float = Form(0.3),
    weight_qualifications: float = Form(0.3),
    weight_skills: float = Form(0.4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user),
):
    """Thin HTTP layer: delegates to shortlist_service.shortlist."""
    try:
        # Delegate heavy lifting to service layer
        return await shortlist_service.shortlist(
            pdf_id=pdf_id,
            # required_experience=required_experience,
            # required_degree=required_degree,
            jd_file_bytes=await jd_file.read(),
            jd_filename=jd_file.filename,
            jd_template=jd_template,
            # search_query=search_query,
            # search_operator=search_operator.upper(),
            weight_experience=weight_experience,
            weight_qualifications=weight_qualifications,
            weight_skills=weight_skills,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise HTTPExceptions from service layer (e.g., 400 for invalid JD)
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shortlisting failed: {str(e)}")
