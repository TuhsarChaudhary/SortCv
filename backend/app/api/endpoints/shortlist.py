from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional, Union
import pandas as pd
import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.resume_pdf import ResumePDF
from app.core.security import get_current_cv_user
from app.models.user import User

router = APIRouter()

MEDIA_FOLDER = os.path.join("app", "static", "media_files")


os.makedirs(MEDIA_FOLDER, exist_ok=True)

# Plug-in: replace this with actual imported function from your module
def perform_shortlisting(filtered_df: pd.DataFrame, jd_file_path: str, filters: dict):
    # 1. parse JD file internally
    jd_df = pd.DataFrame({
        'Job Title': ['AI Engineer'],
        'Skills Extracted': [filters.get("skills", [])],
        'Experience Required': [filters.get("experience", 3)]
    })

    # 2. shortlist and score filtered candidates (mocked)
    shortlisted_df = filtered_df.copy()
    shortlisted_df["Score"] = [0.88, 0.85, 0.75][:len(filtered_df)]
    shortlisted_df = shortlisted_df.sort_values(by="Score", ascending=False)

    return jd_df, shortlisted_df

@router.post("/shortlist")
async def shortlist_candidates(
    pdf_id: int = Form(...),
    jd_file: UploadFile = File(...),
    skills: Union[List[str], str] = Form(...),
    experience: Optional[int] = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cv_user)
):

    # Fetch resume record & its filtered list
    resume_record: Optional[ResumePDF] = db.query(ResumePDF).filter(ResumePDF.id == pdf_id).first()
    if resume_record is None or resume_record.long_listing_csv is None:
        raise HTTPException(status_code=404, detail="Filtered list not found for given resume")

    # Load the dataframe – prefer filtered CSV, otherwise fallback to initial longlist CSV
    csv_source_path: str = resume_record.long_listing_csv or resume_record.csv_path

    try:
        filtered_df = pd.read_csv(csv_source_path)
    except FileNotFoundError:
        # If filtered path missing, fallback once more to original longlist
        if csv_source_path != resume_record.csv_path and os.path.isfile(resume_record.csv_path):
            filtered_df = pd.read_csv(resume_record.csv_path)
        else:
            raise HTTPException(status_code=400, detail="CSV source not found on server")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV is empty – ensure you saved filters before shortlisting")

    # Save JD PDF
    jd_file_path = os.path.join(MEDIA_FOLDER, jd_file.filename)
    with open(jd_file_path, "wb") as buffer:
        shutil.copyfileobj(jd_file.file, buffer)

    # Extract user filters from form
    if isinstance(skills, str):
        # Handle comma-separated string or bracketed list string
        skills_parsed = [s.strip() for s in skills.strip("[]").split(",") if s.strip()]
    else:
        # List[str] from Angular FormData or JS fetch()
        skills_parsed = skills

    user_filters = {
        "skills": skills_parsed,
        "experience": experience
    }


    # Call module function: get parsed JD and final shortlisted list
    try:
        jd_df, shortlisted_df = perform_shortlisting(filtered_df, jd_file_path, user_filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shortlisting failed: {str(e)}")

    # Save final shortlisted result as CSV
    shortlist_name = f"{Path(resume_record.pdf_name).stem}_shortlist.csv"
    shortlist_path = os.path.join(MEDIA_FOLDER, shortlist_name)
    shortlisted_df.to_csv(shortlist_path, index=False)

    # Update DB paths
    resume_record.job_desc_path = jd_file_path
    resume_record.short_listing_csv = shortlist_path
    db.commit()

    # Return both as JSON
    return {
        "message": "Shortlisting successful",
        "jd_data": jd_df.to_dict(orient="records"),
        "shortlisted": shortlisted_df.to_dict(orient="records")
    }
