from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ResumeBase(BaseModel):
    pdf_name: str


class ResumeCreate(ResumeBase):
    pdf_path: str
    csv_path: str
    uploaded_by: Optional[int] = None  # resolved from auth token; optional for now


class Resume(ResumeBase):
    id: int
    pdf_hash: str
    pdf_path: str
    csv_path: str
    long_listing_csv: Optional[str] = None
    short_listing_csv: Optional[str] = None
    job_desc_path: Optional[str] = None
    size: Optional[int] = None
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
