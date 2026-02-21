"""
Authentication and Query History API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from typing import List, Optional
from app.core.auth import hash_password, verify_password, create_access_token, decode_token
from app.core.db import get_db_connection
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["auth"])


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: int
    username: str


class QueryHistoryItem(BaseModel):
    id: int
    query: str
    mode: str
    retrieval_mode: str
    analysis: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: str


class SaveQueryRequest(BaseModel):
    query: str
    mode: str = "quick"
    retrieval_mode: str = "hybrid"
    analysis: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None


def get_current_user_id(authorization: str = Header(None, alias="Authorization")) -> int:
    """Extract and validate user_id from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        token = authorization.replace("Bearer ", "")
        user_id = decode_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization")


@router.post("/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    """Create a new user account"""
    if not request.username or len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if not request.password or len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE username = %s", (request.username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Create user
            hashed_pw = hash_password(request.password)
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (request.username, hashed_pw)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            
            token = create_access_token(user_id)
            return {
                "access_token": token,
                "user_id": user_id,
                "username": request.username,
            }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Signup error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create account")
    finally:
        if conn:
            conn.close()


@router.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """Login with username and password"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (request.username,))
            result = cur.fetchone()
            
            if not result or not verify_password(request.password, result[1]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            user_id = result[0]
            token = create_access_token(user_id)
            
            return {
                "access_token": token,
                "user_id": user_id,
                "username": request.username,
            }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Login error: {exc}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        if conn:
            conn.close()


@router.post("/query-history/save")
def save_query(request: SaveQueryRequest, authorization: str = Header(None)):
    """Save a query to history"""
    user_id = get_current_user_id(authorization)
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO query_history 
                (user_id, query, mode, retrieval_mode, analysis, model_used, latency_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, request.query, request.mode, request.retrieval_mode, 
                 request.analysis, request.model_used, request.latency_ms)
            )
            conn.commit()
            return {"success": True}
    except Exception as exc:
        logger.error(f"Save query error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to save query")
    finally:
        if conn:
            conn.close()


@router.get("/query-history", response_model=List[QueryHistoryItem])
def get_query_history(authorization: str = Header(None), limit: int = 20):
    """Get user's query history"""
    user_id = get_current_user_id(authorization)
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, query, mode, retrieval_mode, analysis, model_used, latency_ms, created_at
                FROM query_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "query": row[1],
                    "mode": row[2],
                    "retrieval_mode": row[3],
                    "analysis": row[4],
                    "model_used": row[5],
                    "latency_ms": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error(f"Get history error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")
    finally:
        if conn:
            conn.close()


@router.delete("/query-history")
def clear_query_history(authorization: str = Header(None)):
    """Clear user's query history"""
    user_id = get_current_user_id(authorization)
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM query_history WHERE user_id = %s", (user_id,))
            conn.commit()
            return {"success": True}
    except Exception as exc:
        logger.error(f"Clear history error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to clear history")
    finally:
        if conn:
            conn.close()
