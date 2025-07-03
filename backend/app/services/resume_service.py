"""High-level resume related operations."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd
import asyncio
from fastapi import HTTPException
from app.db.database import SessionLocal
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF
from app.repositories import resume_repo
from llmod import extract_all

# Configure media folder via environment variable so deployments (e.g. AWS) can override
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # backend directory
MEDIA_FOLDER_ENV = os.getenv("MEDIA_FOLDER")
if MEDIA_FOLDER_ENV:
    MEDIA_FOLDER = Path(MEDIA_FOLDER_ENV)
else:
    MEDIA_FOLDER = PROJECT_ROOT / "app" / "static" / "media_files"

# Ensure the directory exists
MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)

# Public functions 
def upload_resume_sync(
    *,
    file_bytes: bytes,
    filename: str,
    db: Session | None = None,
    uploaded_by: Optional[int] = None,
) -> Dict:
    """Handle resume upload, parsing & DB persistence. Returns a JSON-serialisable dict identical to the old endpoint output."""
    _local_session = False
    if db is None:
        db = SessionLocal()
        _local_session = True

    pdf_hash = hashlib.sha256(file_bytes).hexdigest()

    # 1) Dedup logic
    # a) Does the same user already have this file? – return cached
    existing_same_user = resume_repo.get_by_hash_and_user(db, pdf_hash, uploaded_by or -1)
    if existing_same_user and _artefacts_exist(existing_same_user):
        df = pd.read_csv(existing_same_user.csv_path)
        result = {
            "message": "Resume already processed – returning cached result",
            "pdf_id": existing_same_user.id,
            "rows": len(df),
            "data": df.to_dict(orient="records"),
        }
        if _local_session:
            db.close()
        return result
    elif existing_same_user and not _artefacts_exist(existing_same_user):
        # Stale DB row – clean it up so we can re-parse cleanly
        # 1) Drop the convenience FK from ResumePDF -> JobDescriptionPDF
        existing_same_user.jd_id = None  # breaks ResumePDF -> JD FK
        # 2) Delete child JobDescriptionPDF rows that point back to this resume
        for jd_row in list(existing_same_user.job_descriptions):
            db.delete(jd_row)
        # Flush the above changes so the dependency graph is linear
        db.commit()

        # 3) Safe to delete the stale resume row now that no cycles exist
        db.delete(existing_same_user)
        db.commit()

    # b) File exists from another user – reuse artefacts but create new DB row
    existing_any = resume_repo.get_first_by_hash(db, pdf_hash)
    if existing_any and _artefacts_exist(existing_any):
        df = pd.read_csv(existing_any.csv_path)
        new_row = ResumePDF(
            pdf_name=existing_any.pdf_name,
            pdf_hash=pdf_hash,
            pdf_path=existing_any.pdf_path,
            csv_path=existing_any.csv_path,
            size=existing_any.size,
            uploaded_by=uploaded_by,
        )
        saved = resume_repo.add(db, new_row)
        result = {
            "message": "Resume already processed by another user – linked to existing parse",
            "pdf_id": saved.id,
            "rows": len(df),
            "data": df.to_dict(orient="records"),
        }
        if _local_session:
            db.close()
        return result
    elif existing_any and not _artefacts_exist(existing_any):
        # Artefacts missing – ignore this optimisation path and fall through to fresh parse
        pass

    # 2) Save file to disk (first time this file is ever seen)
    safe_filename = os.path.basename(filename)
    pdf_path = MEDIA_FOLDER / safe_filename
    pdf_path.write_bytes(file_bytes)

    # 3) Parse
    try:
        df = extract_all(pdf_path)
    except Exception as e:
        # truly unreadable file
        pdf_path.unlink(missing_ok=True)          # delete the saved PDF
        raise HTTPException(
            status_code=400,
            detail=f"File could not be parsed: {e}"
        )

    if df.empty:
        # No candidate information found – treat as client error
        pdf_path.unlink(missing_ok=True)          # delete the saved PDF
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid resume PDF."
        )

    # Additional sanity check: ensure the first resume has a valid Gender
    # field ('male', 'female', or 'other'). Any other value (or missing
    # column) indicates the PDF is not a proper P-11 form.
    valid_genders = {"male", "female", "other"}
    first_gender: str | None = None
    if "Gender" in df.columns and not df["Gender"].isna().all():
        first_gender = str(df.loc[0, "Gender"]).strip().lower()

    if first_gender is None or first_gender not in valid_genders:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid P-11 resume PDF (invalid or missing gender field)."
        )

    # 4) Save CSV
    csv_path = MEDIA_FOLDER / f"{pdf_path.stem}_longlist.csv"
    df.to_csv(csv_path, index=False)

    # 5) Persist DB row
    row = ResumePDF(
        pdf_name=safe_filename,
        pdf_hash=pdf_hash,
        pdf_path=str(pdf_path),
        csv_path=str(csv_path),
        size=len(file_bytes),
        uploaded_by=uploaded_by,
    )
    saved = resume_repo.add(db, row)

    result = {
        "message": "Resume parsed successfully",
        "pdf_id": saved.id,
        "rows": len(df),
        "data": df.to_dict(orient="records"),
    }
    if _local_session:
        db.close()
    return result


async def upload_resume(
    *,
    file_bytes: bytes,
    filename: str,
    uploaded_by: Optional[int] = None,
) -> Dict:
    """Async wrapper to offload blocking parsing to a thread."""
    return await asyncio.to_thread(
        upload_resume_sync,
        file_bytes=file_bytes,
        filename=filename,
        db=None,  # Let the sync fn create a thread-local session
        uploaded_by=uploaded_by,
    )


def save_filtered_list(
    *,
    pdf_id: int,
    data: List[Dict],
    min_experience: int | None,
    min_degree: str | None,
    db: Session,
) -> Dict:
    """Persist the filtered long-list and update DB row."""
    resume = resume_repo.get_by_id(db, pdf_id)
    if resume is None:
        raise ValueError("Resume record not found")

    df = pd.DataFrame(data)
    # Make filename unique per ResumePDF row so users don't overwrite each other's filtered list
    save_path = (
        MEDIA_FOLDER
        / f"{Path(resume.pdf_name).stem}_{resume.id}_longlist_filtered.csv"
    )
    df.to_csv(save_path, index=False)

    resume.long_listing_csv = str(save_path)
    resume.min_experience = min_experience
    resume.min_degree = min_degree
    resume_repo.update(db, resume)

    return {"message": "Filtered list saved successfully", "path": str(save_path)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _artefacts_exist(row: ResumePDF) -> bool:  # pragma: no cover – trivial helper
    """Return True only if all stored artefact paths actually exist on disk."""
    return row and os.path.isfile(row.csv_path) and os.path.isfile(row.pdf_path)
