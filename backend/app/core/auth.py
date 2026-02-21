"""
Simple JWT-based authentication for FinVault AI
"""

import jwt
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional

SECRET_KEY = os.getenv("SECRET_KEY", "finvault-ai-secret-key-minimum-32-bytes-required-for-hs256-algorithm-secure-key-generation")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

# Use argon2id for password hashing (no 72-byte limit like bcrypt)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__rounds=4,
    argon2__memory_cost=65536,
)


def hash_password(password: str) -> str:
    """Hash a password using argon2id"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> Optional[int]:
    """Decode a JWT token and return user_id, or None if invalid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except Exception:
        return None
