"""Business logic for shortlisting candidates against a JD.
Currently mirrors the existing endpoint implementation so behaviour remains unchanged.
Replace `perform_shortlisting` with real ML/semantic matching later.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF
from app.repositories import resume_repo

MEDIA_FOLDER = Path("app/static/media_files")
MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Placeholder algorithm
# ---------------------------------------------------------------------------

def perform_shortlisting(filtered_df: pd.DataFrame, jd_file_path: str, filters: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """TEMP stub – returns a mocked JD DF plus filtered_df with fake scores."""
    jd_df = pd.DataFrame({
        "Job Title": ["AI Engineer"],
        "Skills Extracted": [filters.get("skills", [])],
        "Experience Required": [filters.get("experience", 3)],
    })
    shortlisted_df = filtered_df.copy()
    shortlisted_df["Score"] = [0.88, 0.85, 0.75][: len(filtered_df)]
    shortlisted_df = shortlisted_df.sort_values(by="Score", ascending=False)
    return jd_df, shortlisted_df

# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

def shortlist(
    *,
    pdf_id: int,
    jd_file_bytes: bytes,
    jd_filename: str,
    filters: Dict,
    db: Session,
) -> Dict:
    resume = resume_repo.get_by_id(db, pdf_id)
    if resume is None or (resume.long_listing_csv is None and resume.csv_path is None):
        raise ValueError("Filtered list not found for given resume")

    csv_source = resume.long_listing_csv or resume.csv_path
    if not csv_source or not os.path.isfile(csv_source):
        raise FileNotFoundError("CSV source not found on server")

    filtered_df = pd.read_csv(csv_source)

    # Persist JD PDF
    jd_path = MEDIA_FOLDER / jd_filename
    with open(jd_path, "wb") as f:
        f.write(jd_file_bytes)

    # Run algorithm
    jd_df, shortlisted_df = perform_shortlisting(filtered_df, str(jd_path), filters)

    # Save shortlist CSV
    shortlist_path = MEDIA_FOLDER / f"{Path(resume.pdf_name).stem}_shortlist.csv"
    shortlisted_df.to_csv(shortlist_path, index=False)

    # Update DB
    resume.job_desc_path = str(jd_path)
    resume.short_listing_csv = str(shortlist_path)
    resume_repo.update(db, resume)

    return {
        "message": "Shortlisting successful",
        "jd_data": jd_df.to_dict(orient="records"),
        "shortlisted": shortlisted_df.to_dict(orient="records"),
    }
