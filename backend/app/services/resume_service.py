"""High-level resume related operations."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd
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
def upload_resume(
    *,
    file_bytes: bytes,
    filename: str,
    db: Session,
    uploaded_by: Optional[int] = None,
) -> Dict:
    """Handle resume upload, parsing & DB persistence. Returns a JSON-serialisable dict identical to the old endpoint output."""
    pdf_hash = hashlib.sha256(file_bytes).hexdigest()

    # 1) Dedup by hash
    if existing := resume_repo.get_by_hash(db, pdf_hash):
        df = pd.read_csv(existing.csv_path)
        return {
            "message": "Resume already processed – returning cached result",
            "pdf_id": existing.id,
            "rows": len(df),
            "data": df.to_dict(orient="records"),
        }

    # 2) Save file to disk
    pdf_path = MEDIA_FOLDER / filename
    pdf_path.write_bytes(file_bytes)

    # 3) Parse
    df = extract_all(pdf_path)

    # 4) Save CSV
    csv_path = MEDIA_FOLDER / f"{pdf_path.stem}_longlist.csv"
    df.to_csv(csv_path, index=False)

    # 5) Persist DB row
    row = ResumePDF(
        pdf_name=filename,
        pdf_hash=pdf_hash,
        pdf_path=str(pdf_path),
        csv_path=str(csv_path),
        size=len(file_bytes),
        uploaded_by=uploaded_by,
    )
    saved = resume_repo.add(db, row)

    return {
        "message": "Resume parsed successfully",
        "pdf_id": saved.id,
        "rows": len(df),
        "data": df.to_dict(orient="records"),
    }


def save_filtered_list(
    *,
    pdf_id: int,
    data: List[Dict],
    db: Session,
) -> Dict:
    """Persist the filtered long-list and update DB row."""
    resume = resume_repo.get_by_id(db, pdf_id)
    if resume is None:
        raise ValueError("Resume record not found")

    df = pd.DataFrame(data)
    save_path = (
        MEDIA_FOLDER
        / f"{Path(resume.pdf_name).stem}_longlist_filtered.csv"
    )
    df.to_csv(save_path, index=False)

    resume.long_listing_csv = str(save_path)
    resume_repo.update(db, resume)

    return {"message": "Filtered list saved successfully", "path": str(save_path)}
