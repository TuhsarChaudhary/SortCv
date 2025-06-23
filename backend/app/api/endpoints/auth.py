from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from typing import Any
from app.core.email_utils import send_email
from app.core.security import create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

from app.db.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.user import User, PasswordResetOTP
from app.schemas.user import (
    UserCreate,
    User as UserSchema,
    UserUpdate,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)

router = APIRouter()

@router.post("/register", response_model=UserSchema)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
    """
    # Check if user with this email exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    # Check if user with this phone exists
    user = db.query(User).filter(User.phone == user_in.phone).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this phone number already exists"
        )
    
    # Create new user
    db_user = User(
        fname=user_in.fname,
        lname=user_in.lname,
        email=user_in.email,
        phone=user_in.phone,
        dateofbirth=user_in.dateofbirth,
        gender=user_in.gender,
        country=user_in.country,
        nationality=user_in.nationality,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_admin=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "is_admin": user.is_admin
    }

@router.post("/login/init")
def login_init(user_login: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    Regular login endpoint for frontend applications.
    """
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    #Generate OTP and Save
    otp = f"{random.randint(0, 999999):06d}"
    otp_hash = get_password_hash(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=2)
    
    otp_entry = PasswordResetOTP(user_id=user.id, otp_hash=otp_hash, expires_at=expires_at)
    db.add(otp_entry)
    db.commit()

    #Send OTP
    try:
        send_email(user.email, "Login OTP for SortCV", f"Your OTP is {otp}. It expires in 2 minutes.")

    except RuntimeError as exc:
        # Rollback OTP creation so user can retry
        db.delete(otp_entry)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"message": "OTP sent successfully", "user_id": user.id}

@router.post("/login/verify")
def login_verify(user_id: int = Form(...), otp: str = Form(...), db: Session = Depends(get_db)) -> Any: 
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    otp_entry = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used == False,
            PasswordResetOTP.expires_at > datetime.utcnow(),
        )
        .order_by(PasswordResetOTP.expires_at.desc())
        .first()
    )

    if not otp_entry or not verify_password(otp, otp_entry.otp_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp_entry.used = True
    db.commit()

    #JWt Token Issued here
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "fname": user.fname,
        "lname": user.lname,
        "is_admin": user.is_admin
    }  

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)) -> Any:
    # Always return success to avoid email enumeration
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=5)
    )

    reset_url = f"https://CV-RANKING.com/change-password?token={token}"

    try:
        send_email(
                to_email=user.email,
                subject="Reset your SortCV password",
                body=f"Click this link to reset your password:\n{reset_url}\n\nLink expires in 2 minutes.",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"message": "Password reset email sent successfully"}


@router.post("/reset-password-link")
async def reset_password_via_link(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
    ) -> Any:
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    return {"message": "Password reset successful. Please login again."}


@router.post("/auth/change-password", response_model=UserSchema)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change password for logged in user"""
    # Verify old password
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user.
    """
    # Check if email is being updated and if it already exists
    if user_in.email and user_in.email != current_user.email:
        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
    
    # Check if phone is being updated and if it already exists
    if user_in.phone and user_in.phone != current_user.phone:
        user = db.query(User).filter(User.phone == user_in.phone).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this phone number already exists"
            )
    
    # Update user fields
    for field, value in user_in.dict(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user
