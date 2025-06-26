from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import pandas as pd
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from app.services import resume_service
from typing import Optional
from app.core.security import get_current_cv_user
from app.models.user import User
import hashlib
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.resume_pdf import ResumePDF

router = APIRouter()

# Define correct relative path
MEDIA_FOLDER = os.path.join("app", "static", "media_files")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

@router.post("/upload-resume")
async def upload_resume(
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user),
):
    """Thin HTTP layer: delegates to resume_service.upload_resume."""
    file_bytes = await cv_file.read()
    return resume_service.upload_resume(
        file_bytes=file_bytes,
        filename=cv_file.filename,
        db=db,
        uploaded_by=current_user.id,
    )

# Model for receiving filtered list along with the DB id of the parent PDF
class FilteredResumeList(BaseModel):
    pdf_id: int
    data: list[dict]


@router.post("/save-filtered")
async def save_filtered_list(
    payload: FilteredResumeList,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user),
):
    """Thin HTTP layer: delegates to resume_service.save_filtered_list."""
    try:
        return resume_service.save_filtered_list(
            pdf_id=payload.pdf_id,
            data=payload.data,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
