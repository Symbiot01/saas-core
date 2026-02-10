"""
Simple FastAPI backend example with saas-core authentication.

This backend demonstrates how to verify JWT tokens from Firebase/GCIP
using the saas-core library.

Run with:
    # Option 1: Service account JSON file
    export SAAS_CORE_FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
    # OR Option 2: Service account JSON as string (for containers)
    export SAAS_CORE_FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
    # OR Option 3: Project ID (for Google Cloud environments)
    export SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
    
    uvicorn examples.backend:app --reload --port 8000
"""

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from saas_core import verify_user, AuthenticationError, EmailNotVerifiedError
from saas_core.exceptions import ConfigurationError

# Load environment variables from a local .env (searched upward from CWD).
# This makes the example work without manually exporting SAAS_CORE_* vars.
load_dotenv(find_dotenv(usecwd=True))

app = FastAPI(title="saas-core Backend Example")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and verify JWT token from Authorization header.
    
    This is used as a FastAPI dependency to protect endpoints.
    """
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )

        token = authorization.replace("Bearer ", "")
        user_info = verify_user(token)
        return user_info

    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=403, detail="Email verification required"
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except ConfigurationError as e:
        # Misconfiguration is a server error (not a client auth failure).
        raise HTTPException(
            status_code=500,
            detail=(
                "Backend misconfigured. Set one of: SAAS_CORE_FIREBASE_CREDENTIALS_PATH, "
                "SAAS_CORE_FIREBASE_CREDENTIALS_JSON, or SAAS_CORE_GOOGLE_PROJECT_ID (and restart). "
                f"Details: {str(e)}"
            ),
        )


@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {
        "message": "saas-core Backend API",
        "status": "running",
        "endpoints": {
            "public": "/",
            "protected": "/api/protected",
            "profile": "/api/user/profile"
        }
    }


@app.get("/api/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    """Protected endpoint - requires valid JWT token."""
    return {
        "message": "Access granted!",
        "user_id": user["uid"],
        "email": user["email"],
        "email_verified": user["email_verified"],
    }


@app.get("/api/user/profile")
async def user_profile(user: dict = Depends(get_current_user)):
    """Get authenticated user's profile."""
    return {
        "user_id": user["uid"],
        "email": user["email"],
        "email_verified": user["email_verified"],
        "authenticated_at": user.get("auth_time"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
