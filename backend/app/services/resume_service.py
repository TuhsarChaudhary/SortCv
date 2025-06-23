"""High-level resume related operations.
Until real parsing & scoring modules arrive, we keep the previous logic here so existing
endpoints behave exactly the same. When the real modules are ready, they can replace
`parse_pdf_to_df` and `perform_shortlisting` below without touching the routers.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.resume_pdf import ResumePDF
from app.repositories import resume_repo

# Re-use existing media folder location
MEDIA_FOLDER = Path("app/static/media_files")
MEDIA_FOLDER.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Placeholder PDF → DataFrame parser (keep behaviour unchanged)
# ---------------------------------------------------------------------------

def parse_pdf_to_df(file_path: str | Path) -> pd.DataFrame:
    """TEMP stub – returns a mocked DataFrame.
    Replace with real parser when available.
    """
    data = {
        "CV ID": ["CV 2", "CV 5", "CV 7"],
        "Name": ["Sushil Kumar", "Piyush Singh", "Vivek Mathur"],
        "Highest Degree": ["Bachelors Degree", "Masters Degree", "Masters Degree"],
        "YOE": [12, 4, 4],
        "Gender": ["Male", "Male", "Male"],
        "Nationality": ["India", "India", "India"],
    }
    return pd.DataFrame(data)

# ---------------------------------------------------------------------------
# Public service functions used by routers
# ---------------------------------------------------------------------------

def upload_resume(
    *,
    file_bytes: bytes,
    filename: str,
    db: Session,
    uploaded_by: Optional[int] = None,
) -> Dict:
    """Handle resume upload, parsing & DB persistence.
    Returns a JSON-serialisable dict identical to the old endpoint output.
    """
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
    df = parse_pdf_to_df(pdf_path)

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
