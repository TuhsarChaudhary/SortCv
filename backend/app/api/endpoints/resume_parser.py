from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import pandas as pd
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from typing import Optional
from app.core.security import get_current_cv_user
from app.models.user import User
import hashlib
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.resume_pdf import ResumePDF

router = APIRouter()

# ✅ Define correct relative path
MEDIA_FOLDER = os.path.join("app", "static", "media_files")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# 📌 Placeholder function for now
def parse_pdf_to_df(file_path: str) -> pd.DataFrame:
    # Simulate longlist from a parsed PDF
    data = {
        'CV ID': ['CV 2', 'CV 5', 'CV 7'],
        'Name': ['Sushil Kumar', 'Piyush Singh', 'Vivek Mathur'],
        'Highest Degree': ['Bachelors Degree', 'Masters Degree', 'Masters Degree'],
        'YOE': [12, 4, 4],
        'Gender': ['Male', 'Male', 'Male'],
        'Nationality': ['India', 'India', 'India']
    }
    return pd.DataFrame(data)

@router.post("/upload-resume")
async def upload_resume(
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user)
):

    """Upload a resume PDF and return its long-listing in JSON format.

    If the same file name was previously processed we skip re-processing and
    return the cached result from the database / filesystem instead.
    """

    # 0️⃣ Read file bytes & compute SHA-256 hash to reliably identify duplicates
    file_bytes = await cv_file.read()
    pdf_hash = hashlib.sha256(file_bytes).hexdigest()

    # 1️⃣ Check if this exact resume was already handled earlier via hash
    existing: Optional[ResumePDF] = (
        db.query(ResumePDF).filter(ResumePDF.pdf_hash == pdf_hash).first()
    )
    if existing:
        try:
            df = pd.read_csv(existing.csv_path)
            return {
                "message": "Resume already processed – returning cached result",
                "pdf_id": existing.id,
                "rows": len(df),
                "data": df.to_dict(orient="records")
            }
        except FileNotFoundError:
            # CSV was removed from disk for some reason – fall through to re-process
            pass

    # ✅ Step 1: Save uploaded file to the media folder
    pdf_path = os.path.join(MEDIA_FOLDER, cv_file.filename)
    with open(pdf_path, "wb") as buffer:
        buffer.write(file_bytes)

    # ✅ Step 2: Parse file to DataFrame
    try:
        df = parse_pdf_to_df(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

    # ✅ Step 3: Save DataFrame as CSV
    csv_file_name = f"{Path(cv_file.filename).stem}_longlist.csv"
    csv_path = os.path.join(MEDIA_FOLDER, csv_file_name)
    df.to_csv(csv_path, index=False)

    # ✅ Step 4: Persist artefact info in DB (short-listing still empty)
    new_entry = ResumePDF(
        pdf_name=cv_file.filename,
        pdf_hash=pdf_hash,
        pdf_path=pdf_path,
        csv_path=csv_path,
        long_listing_csv=None,
        short_listing_csv=None,
        job_desc_path=None,
        size=len(file_bytes)
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # ✅ Step 5: Return JSON response
    return {
        "message": "Resume parsed successfully",
        "pdf_id": new_entry.id,
        "rows": len(df),
        "data": df.to_dict(orient="records")
    }

# Model for receiving filtered list along with the DB id of the parent PDF
class FilteredResumeList(BaseModel):
    pdf_id: int
    data: list[dict]


@router.post("/save-filtered")
async def save_filtered_list(
    payload: FilteredResumeList,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user)
):
    try:
        resume_record: ResumePDF | None = db.query(ResumePDF).filter(ResumePDF.id == payload.pdf_id).first()
        if resume_record is None:
            raise HTTPException(status_code=404, detail="Resume record not found")

        # Persist filtered list to disk
        df = pd.DataFrame(payload.data)
        save_name = f"{Path(resume_record.pdf_name).stem}_longlist_filtered.csv"
        save_path = os.path.join(MEDIA_FOLDER, save_name)
        df.to_csv(save_path, index=False)

        # Update DB row
        resume_record.long_listing_csv = save_path
        db.commit()

        return {"message": "Filtered list saved successfully", "path": save_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
