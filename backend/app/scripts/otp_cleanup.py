"""Background task that periodically deletes used or expired OTP rows.

This keeps the `password_reset_otps` table small without requiring an external
cron job. Import `cleanup_loop` in `main.py` and schedule it with
`asyncio.create_task(cleanup_loop())`.
"""

import asyncio
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models.user import PasswordResetOTP

# Run every hour (adjust if you want shorter / longer intervals)
CLEANUP_INTERVAL_SECONDS = 60 * 60  # 1 hour

async def cleanup_loop() -> None:
    """Coroutine that sleeps for the configured interval and prunes rows."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        prune_otps()


def prune_otps() -> None:
    """Remove OTP rows that are already used or have expired."""
    with SessionLocal() as db:
        deleted = (
            db.query(PasswordResetOTP)
            .filter(
                (PasswordResetOTP.used == True) |
                (PasswordResetOTP.expires_at < datetime.now(timezone.utc))
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            print(f"[otp_cleanup] removed {deleted} OTP rows")
