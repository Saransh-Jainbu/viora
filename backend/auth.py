"""
Firebase Authentication middleware.

Verifies Firebase ID tokens sent in the Authorization header.
Initialises the Firebase Admin SDK on first import.
"""

import firebase_admin
from firebase_admin import auth, credentials, db as firebase_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config import settings

# ── Initialise Firebase Admin SDK (runs once) ────────────────────────────────
_cred = credentials.Certificate(settings.firebase_service_account_key)
firebase_admin.initialize_app(
    _cred,
    {"databaseURL": settings.firebase_database_url},
)

# ── Bearer-token scheme ──────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    Dependency that extracts and verifies the Firebase ID token.

    Returns the decoded token dict (contains `uid`, `email`, etc.).
    Raises 401 if the token is missing, expired, or invalid.
    """
    token = creds.credentials
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired. Please re-authenticate.",
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
        )


def get_user_ref(uid: str):
    """Return a Firebase Realtime Database reference for a user."""
    return firebase_db.reference(f"users/{uid}")
