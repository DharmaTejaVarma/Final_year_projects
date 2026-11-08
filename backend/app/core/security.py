from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

try:
    from app.core.config import settings
    from app.core.logger import logger
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logger import logger

# Initialize Argon2id password hasher with secure production parameters
password_hasher = PasswordHasher(
    time_cost=2,       # Number of iterations
    memory_cost=65536, # 64 MB of RAM
    parallelism=1,     # Number of parallel threads
    hash_len=32,       # Length of hash in bytes
    salt_len=16,       # Length of salt in bytes
)


def hash_password(password: str) -> str:
    """Hash a plain-text password using the Argon2id algorithm."""
    if not password:
        raise ValueError("Password cannot be empty")
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain-text password matches the stored Argon2 hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during password verification: {e}")
        return False


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed JWT access token for authentication."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access_token",
    }
    if extra_claims:
        payload.update(extra_claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT token."""
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return decoded
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None

