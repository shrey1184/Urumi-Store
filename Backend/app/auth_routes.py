"""
Authentication API routes — OAuth login and user management.
"""

import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, get_oauth_client
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import UserResponse

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# State storage for OAuth CSRF protection (in-memory for now)
_oauth_states = set()


# ───────────────── OAuth Login ─────────────────
@auth_router.get("/login/{provider}")
async def login(provider: str = "google"):
    """Initiate OAuth login flow."""
    if provider not in ["google"]:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    oauth_client = get_oauth_client(provider)

    # Generate CSRF state
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    # Get authorization URL
    authorization_url, _ = oauth_client.create_authorization_url(
        settings.GOOGLE_AUTHORIZATION_ENDPOINT,
        state=state,
    )

    return {"authorization_url": authorization_url, "state": state}


# ───────────────── OAuth Callback ─────────────────
@auth_router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback and create/login user."""

    # Verify CSRF state
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    _oauth_states.discard(state)

    if provider not in ["google"]:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    oauth_client = get_oauth_client(provider)

    try:
        # Exchange code for token
        token = await oauth_client.fetch_token(
            settings.GOOGLE_TOKEN_ENDPOINT,
            code=code,
        )

        # Get user info using token in header
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                settings.GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
            resp.raise_for_status()
            user_info = resp.json()

        logger.info(f"Received user info: {user_info}")

        email = user_info.get("email")
        name = user_info.get("name")
        oauth_id = user_info.get("sub") or user_info.get("id")

        if not email or not oauth_id:
            logger.error(
                f"Missing email or oauth_id. Email: {email}, OAuth ID: {oauth_id}, Full info: {user_info}"
            )
            raise HTTPException(
                status_code=400, detail="Failed to retrieve user info from OAuth provider"
            )

        # Find or create user
        result = await db.execute(
            select(User).where(User.email == email, User.oauth_provider == provider)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                email=email,
                name=name,
                oauth_provider=provider,
                oauth_id=oauth_id,
                last_login=datetime.now(UTC),
            )
            db.add(user)
        else:
            # Update last login
            user.last_login = datetime.now(UTC)
            if name and not user.name:
                user.name = name

        await db.commit()
        await db.refresh(user)

        # Create JWT access token (sub must be a string per JWT spec)
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=frontend_url)

    except Exception as e:
        logger.exception("OAuth error: %s", e)
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")


# ───────────────── Get Current User ─────────────────
@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user)


# ───────────────── Logout ─────────────────
@auth_router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (token invalidation handled client-side)."""
    return {"message": "Logged out successfully"}
