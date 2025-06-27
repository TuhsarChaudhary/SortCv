from typing import Optional
from sqlalchemy.orm import Session

from app.models.job_description_pdf import JobDescriptionPDF


def get_by_hash_resume_template(
    db: Session,
    jd_hash: str,
    resume_id: int,
    template_type: str,
) -> Optional[JobDescriptionPDF]:
    """Return JD row that matches hash + resume + template_type."""
    return (
        db.query(JobDescriptionPDF)
        .filter(
            JobDescriptionPDF.jd_hash == jd_hash,
            JobDescriptionPDF.resume_id == resume_id,
            JobDescriptionPDF.template_type == template_type,
        )
        .first()
    )


def add(db: Session, obj: JobDescriptionPDF) -> JobDescriptionPDF:
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: JobDescriptionPDF) -> JobDescriptionPDF:
    db.commit()
    db.refresh(obj)
    return obj
