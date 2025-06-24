from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from pydantic import BaseModel

from app.db.database import get_db
from app.core.security import get_current_admin_user, get_password_hash
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.schemas.user_summary import UserSummary

router = APIRouter()

@router.get("/", response_model=List[UserSummary])
def read_users(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Retrieve users. Admin only."""
    users = db.query(User).offset(skip).limit(limit).all()
    summaries = [
        UserSummary(
            id=user.id,
            name=f"{user.fname} {user.lname}",
            email=user.email,
            phone=user.phone,
            cv_access=user.cv_access
        )
        for user in users
    ]
    return summaries


class CVAccessPayload(BaseModel):
    user_id: int
    cv_access: bool

@router.patch("/cv_access", response_model=UserSummary)
def update_cv_access(
    payload: CVAccessPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """Approve or revoke CV access for a user (admin only).Accepts user_id and cv_access in JSON body."""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.cv_access = payload.cv_access
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserSummary(
        id=user.id,
        name=f"{user.fname} {user.lname}",
        email=user.email,
        phone=user.phone,
        cv_access=user.cv_access
    )

# @router.post("/", response_model=UserSchema)
# def create_user(
#     user_in: UserCreate,  
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin_user)
# ) -> Any:
#     """
#     Create new user. Admin only.
#     """
#     # Check if user with this email exists
#     user = db.query(User).filter(User.email == user_in.email).first()
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A user with this email already exists"
#         )
    
#     # Check if user with this phone exists
#     user = db.query(User).filter(User.phone == user_in.phone).first()
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A user with this phone number already exists"
#         )
    
#     # Create new user
#     db_user = User(
#         fname=user_in.fname,
#         lname=user_in.lname,
#         email=user_in.email,
#         phone=user_in.phone,
#         dateofbirth=user_in.dateofbirth,
#         gender=user_in.gender,
#         country=user_in.country,
#         nationality=user_in.nationality,
#         hashed_password=get_password_hash(user_in.password),
#         is_active=True,
#         is_admin=False,
#         cv_access=bool(user_in.cv_access) if hasattr(user_in, "cv_access") else False
#     )
    
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
    
#     return db_user

# @router.get("/{user_id}", response_model=UserSchema)
# def read_user(
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin_user)
# ) -> Any:
#     """
#     Get a specific user by id. Admin only.
#     """
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#     return user

# @router.put("/{user_id}", response_model=UserSchema)        
# def update_user(
#     user_id: int,
#     user_in: UserUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin_user)
# ) -> Any:
#     """
#     Update a user. Admin only.
#     """
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     # Check if email is being updated and if it already exists
#     if user_in.email and user_in.email != user.email:
#         user_with_email = db.query(User).filter(User.email == user_in.email).first()
#         if user_with_email:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="A user with this email already exists"
#             )
    
#     # Check if phone is being updated and if it already exists
#     if user_in.phone and user_in.phone != user.phone:
#         user_with_phone = db.query(User).filter(User.phone == user_in.phone).first()
#         if user_with_phone:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="A user with this phone number already exists"
#             )
    
#     # Update user fields
#     for field, value in user_in.dict(exclude_unset=True).items():
#         if value is not None:
#             setattr(user, field, value)
    
#     db.add(user)
#     db.commit()
#     db.refresh(user)
    
#     return user

# @router.delete("/{user_id}", response_model=UserSchema)
# def delete_user(
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin_user)
# ) -> Any:
#     """
#     Delete a user. Admin only.
#     """
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     # Don't allow deleting yourself
#     if user.id == current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cannot delete your own user account"
#         )
    
#     db.delete(user)
#     db.commit()
    
    # return user
