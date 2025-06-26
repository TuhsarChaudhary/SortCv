"""Business logic for shortlisting candidates against a JD."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF
from app.repositories import resume_repo
from slmod import (
    extract_job_description,
    extract_relevant_job_sections,
    rank_cvs,
)

MEDIA_FOLDER = Path("app/static/media_files")
MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

def shortlist(
    *,
    pdf_id: int,
    jd_file_bytes: bytes,
    jd_filename: str,
    jd_template: str,
    search_query: str,
    search_operator: str,
    weight_experience: float,
    weight_qualifications: float,
    weight_skills: float,
    db: Session,
) -> Dict:
    resume = resume_repo.get_by_id(db, pdf_id)
    if resume is None or (resume.long_listing_csv is None and resume.csv_path is None):
        raise ValueError("Filtered list not found for given resume")

    csv_source = resume.long_listing_csv or resume.csv_path
    if not csv_source or not os.path.isfile(csv_source):
        raise FileNotFoundError("CSV source not found on server")

    filtered_df = pd.read_csv(csv_source)

    # ------------------------------------------------------------------
    # Optional search query filtering BEFORE ranking
    # ------------------------------------------------------------------
    if search_query:
        terms = [t.strip().lower() for t in search_query.split(",") if t.strip()]
        if terms:
            def matches(text: str) -> bool:
                text_l = str(text).lower()
                if search_operator == "AND":
                    return all(term in text_l for term in terms)
                # Default OR behaviour
                return any(term in text_l for term in terms)

            # Assume Employment History column exists at index 6 or with name 'Employment History'
            if "Employment History" in filtered_df.columns:
                mask = filtered_df["Employment History"].apply(matches)
            else:
                # Fallback: apply to the string representation of the row
                mask = filtered_df.apply(lambda row: matches(" ".join(map(str, row.values))), axis=1)
            filtered_df = filtered_df[mask].reset_index(drop=True)

    # Persist JD PDF
    jd_path = MEDIA_FOLDER / jd_filename
    with open(jd_path, "wb") as f:
        f.write(jd_file_bytes)

    # ------------------------------------------------------------------
    # JD processing pipeline
    # ------------------------------------------------------------------
    # 1. Extract full JD text
    full_jd_text = extract_job_description(str(jd_path))

    # 2. Extract relevant sections based on template
    relevant_section_text = extract_relevant_job_sections(full_jd_text, jd_template)

    # 3. Rank CVs (using default required experience/degree for now)
    ranked_df = rank_cvs(
        relevant_section_text or full_jd_text,
        required_experience=0,
        required_degree="Any",
        df=filtered_df,
        weight_experience=weight_experience,
        weight_qualifications=weight_qualifications,
        weight_skills=weight_skills,
    )

    # Save shortlist CSV
    shortlist_path = MEDIA_FOLDER / f"{Path(resume.pdf_name).stem}_shortlist.csv"
    ranked_df.to_csv(shortlist_path, index=False)

    # Update DB
    resume.job_desc_path = str(jd_path)
    resume.short_listing_csv = str(shortlist_path)
    resume_repo.update(db, resume)

    return {
        "relevant_section_text": relevant_section_text,
        "shortlisted": ranked_df.to_dict(orient="records"),
    }
