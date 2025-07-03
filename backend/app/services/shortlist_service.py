"""Business logic for shortlisting candidates against a JD."""

from __future__ import annotations

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF
from app.models.job_description_pdf import JobDescriptionPDF
from app.repositories import resume_repo, jd_repo
from slmod import (
    extract_job_description,
    extract_relevant_job_sections,
    rank_cvs,
)

import asyncio
from app.db.database import SessionLocal
from fastapi import HTTPException

# Configure media folder via environment variable so deployments (e.g. AWS) can override
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # backend directory
MEDIA_FOLDER_ENV = os.getenv("MEDIA_FOLDER")
if MEDIA_FOLDER_ENV:
    MEDIA_FOLDER = Path(MEDIA_FOLDER_ENV)
else:
    MEDIA_FOLDER = PROJECT_ROOT / "app" / "static" / "media_files"

# Ensure the directory exists
MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Running heavy work without blocking the event-loop
# ---------------------------------------------------------------------------
# We keep the original (blocking) implementation as `shortlist_sync` and expose an
# async wrapper that executes it in a background thread via `asyncio.to_thread`.
#
#   • Incoming HTTP handler awaits the async wrapper – this releases control
#     back to the event-loop while the real work runs in the thread-pool.
#   • No extra infrastructure is required (zero-dep option A).

# ---------------------------------------------------------------------------
# Blocking implementation (moved from original `shortlist`)
# ---------------------------------------------------------------------------

def shortlist_sync(
    *,
    pdf_id: int,
    jd_file_bytes: bytes,
    jd_filename: str,
    jd_template: str,
    weight_experience: float,
    weight_qualifications: float,
    weight_skills: float,
    db: Session | None = None,
) -> Dict:
    _local_session = False
    if db is None:
        db = SessionLocal()
        _local_session = True
    resume = resume_repo.get_by_id(db, pdf_id)
    if resume is None or (resume.long_listing_csv is None and resume.csv_path is None):
        raise ValueError("Filtered list not found for given resume")

    csv_source = resume.long_listing_csv or resume.csv_path
    if not csv_source or not os.path.isfile(csv_source):
        raise FileNotFoundError("CSV source not found on server")

    filtered_df = pd.read_csv(csv_source)

    # --------------------------------------------------------------
    # Compute JD hash & dedup row lookup **before** saving the file
    # --------------------------------------------------------------
    # Prevent directory traversal in user-provided filenames
    jd_filename = os.path.basename(jd_filename)
    jd_hash = hashlib.sha256(jd_file_bytes).hexdigest()
    existing_jd = jd_repo.get_by_hash_resume_template(db, jd_hash, resume.id, jd_template)

    # If DB row exists but underlying file is missing -> clean up row & treat as new
    if existing_jd and not os.path.isfile(existing_jd.jd_path):
        db.delete(existing_jd)
        db.commit()
        existing_jd = None

    if existing_jd:
        # Reuse previously stored file path – no need to write again
        jd_path = Path(existing_jd.jd_path)
    else:
        # Persist the newly uploaded JD PDF
        jd_path = MEDIA_FOLDER / jd_filename
        with open(jd_path, "wb") as f:
            f.write(jd_file_bytes)

    # ------------------------------------------------------------------
    # Obtain relevant JD text (cached or freshly extracted)
    # ------------------------------------------------------------------
    relevant_section_text: str | None = None
    if existing_jd and existing_jd.relevant_text_path and os.path.isfile(existing_jd.relevant_text_path):
        with open(existing_jd.relevant_text_path, "r", encoding="utf-8") as fh:
            relevant_section_text = fh.read()
    else:
        # Need to parse JD and extract relevant text
        full_jd_text = extract_job_description(str(jd_path))
        relevant_section_text = extract_relevant_job_sections(full_jd_text, jd_template)
        # Persist extracted text to disk for reuse
        rel_txt_name = f"{Path(jd_filename).stem}_{jd_template}_{jd_hash[:8]}.txt"
        rel_txt_path = MEDIA_FOLDER / rel_txt_name
        with open(rel_txt_path, "w", encoding="utf-8") as fh:
            fh.write(relevant_section_text)
        # Update or create JD DB row later with this path

    # Validate JD text – must not be empty
    if not relevant_section_text or not relevant_section_text.strip():
        # Delete the newly saved JD path/text file to keep storage clean
        if 'jd_path' in locals() and jd_path.exists():
            jd_path.unlink(missing_ok=True)
        if 'rel_txt_path' in locals() and rel_txt_path.exists():
            rel_txt_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="JD file has no extractable text or template mismatch."
        )

    # 3. Rank CVs (using default required experience/degree for now)
    # Optional debug logging
    ranked_df = rank_cvs(
        job_description=relevant_section_text,
        required_experience=resume.min_experience or 0,
        required_degree=resume.min_degree or "Any",
        df=filtered_df,
        weight_experience=weight_experience,
        weight_qualifications=weight_qualifications,
        weight_skills=weight_skills,
    )

    # We no longer persist shortlist CSV files – keep ranking only in-memory
    shortlist_path = None

    # Persist / update JD row (without shortlist_csv)
    if existing_jd:
        # Update relevant text path if generated this run
        if 'rel_txt_path' in locals():
            existing_jd.relevant_text_path = str(rel_txt_path)
        jd_repo.update(db, existing_jd)
        jd_ref = existing_jd  # Reference to link back to ResumePDF
    else:
        jd_row = JobDescriptionPDF(
            jd_name=jd_filename,
            jd_hash=jd_hash,
            jd_path=str(jd_path),
            template_type=jd_template,
            relevant_text_path=str(rel_txt_path),
            resume_id=resume.id,
        )
        try:
            jd_repo.add(db, jd_row)
        except IntegrityError:
            # Row was inserted concurrently by another request – fetch it instead
            db.rollback()
            jd_row = jd_repo.get_by_hash_resume_template(db, jd_hash, resume.id, jd_template)
        jd_ref = jd_row  # Reference to link back to ResumePDF

    # ------------------------------------------------------------------
    # Update convenience foreign key on ResumePDF to point to latest JD
    # ------------------------------------------------------------------
    resume.jd_id = jd_ref.id
    resume_repo.update(db, resume)

    result = {
        "relevant_section_text": relevant_section_text,
        "shortlisted": ranked_df.to_dict(orient="records"),
    }
    if _local_session:
        db.close()
    return result
    

# ---------------------------------------------------------------------------
# Async wrapper – Non-blocking public API
# ---------------------------------------------------------------------------

async def shortlist(
    *,
    pdf_id: int,
    jd_file_bytes: bytes,
    jd_filename: str,
    jd_template: str,
    weight_experience: float,
    weight_qualifications: float,
    weight_skills: float,
    db: Session | None = None,
) -> Dict:
    """Run :pyfunc:`shortlist_sync` in a thread so the event-loop stays free.

    The signature mirrors ``shortlist_sync`` so callers (e.g. API layer) remain
    unchanged.  All heavy CPU + blocking I/O work happens in a worker thread
    from the default asyncio thread-pool.
    """

    return await asyncio.to_thread(
        shortlist_sync,
        pdf_id=pdf_id,
        jd_file_bytes=jd_file_bytes,
        jd_filename=jd_filename,
        jd_template=jd_template,
        weight_experience=weight_experience,
        weight_qualifications=weight_qualifications,
        weight_skills=weight_skills,
    )
