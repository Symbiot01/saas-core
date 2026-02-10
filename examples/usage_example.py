"""
Example usage of saas-core library with FastAPI.

This example demonstrates how to integrate saas-core authentication
into a FastAPI service using Google Cloud Identity Platform (GCIP).
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from saas_core import verify_user, AuthenticationError, EmailNotVerifiedError

app = FastAPI(title="Example Service with GCIP Authentication")


async def get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and verify JWT token from Authorization header.

    This dependency function can be used with FastAPI's Depends() to
    protect endpoints that require authentication.

    Args:
        authorization: Authorization header containing "Bearer <token>"

    Returns:
        Dictionary with user information (uid, email, email_verified, auth_time)

    Raises:
        HTTPException: 401 for invalid/expired tokens, 403 for unverified emails
    """
    try:
        # Extract token from "Bearer <token>" format
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


@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {"message": "Welcome to the API", "status": "public"}


@app.get("/api/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    """Protected endpoint - requires valid GCIP JWT token.

    This endpoint demonstrates basic authentication. The user information
    is automatically extracted from the verified JWT token.

    Returns:
        JSON response with user information
    """
    return {
        "message": "Access granted",
        "user_id": user["uid"],
        "email": user["email"],
        "email_verified": user["email_verified"],
    }


@app.get("/api/user/profile")
async def user_profile(user: dict = Depends(get_current_user)):
    """Get user profile information.

    This endpoint shows how to use the authenticated user information
    to provide user-specific data.

    Returns:
        User profile information
    """
    return {
        "user_id": user["uid"],
        "email": user["email"],
        "email_verified": user["email_verified"],
        "authenticated_at": user.get("auth_time"),
    }


@app.get("/api/admin")
async def admin_endpoint(user: dict = Depends(get_current_user)):
    """Example admin endpoint.

    This endpoint demonstrates how you might add additional authorization
    logic on top of authentication. In a real application, you would
    check user roles/permissions here.

    Returns:
        Admin-only information
    """
    # Example: Check if user has admin privileges
    # In a real app, you'd query a database or check user roles
    # For now, this is just an example structure

    return {
        "message": "Admin access granted",
        "user_id": user["uid"],
        "note": "Add role-based authorization logic here",
    }


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app
    # Make sure to set environment variables before running:
    # export SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
    uvicorn.run(app, host="0.0.0.0", port=8000)
