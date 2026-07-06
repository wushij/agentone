"""backend/app/core/security.py"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, role: str) -> str:
    expire_minutes = _resolve_token_expire_minutes()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(subject),
        "role": role,
        "jti": uuid4().hex,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def safe_decode_access_token(token: str) -> dict | None:
    try:
        return decode_access_token(token)
    except JWTError:
        return None


def _resolve_token_expire_minutes() -> int:
    try:
        from app.services.settings_store import settings_store

        return int(settings_store.get_all().get("jwtExpireMinutes", settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    except Exception:
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES
