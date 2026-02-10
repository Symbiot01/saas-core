# saas-core

Core authentication library for Hub & Spoke SaaS architecture with Google Cloud Identity Platform (GCIP) integration.

## Overview

`saas-core` provides centralized, stateless JWT authentication verification for microservices architectures. It integrates with Google Cloud Identity Platform (GCIP) / Firebase Authentication to verify tokens issued by Google's identity services.

### Key Features

- **Stateless JWT Verification**: Verify tokens without database lookups
- **GCIP Integration**: Full support for Google Cloud Identity Platform tokens
- **Automatic Key Management**: Fetches and caches Google's public keys with automatic rotation handling
- **Comprehensive Security**: Validates signatures, expiration, issuer, audience, and email verification
- **Framework Agnostic**: Works with any Python web framework (FastAPI, Flask, Django, etc.)
- **Zero Configuration**: Simple environment variable setup

## Installation

### From GitHub

```bash
pip install git+https://github.com/yourusername/saas-core.git
```

### Development Installation

```bash
git clone https://github.com/yourusername/saas-core.git
cd saas-core
pip install -e .
```

## Quick Start

### 1. Set Up Google Cloud Identity Platform

1. Create a Google Cloud project
2. Enable Identity Platform API
3. Configure authentication providers (Google Sign-In, Email/Password, etc.)
4. Note your Project ID

### 2. Configure Environment Variables

```bash
export SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
export SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True
```

### 3. Use in Your Service

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from saas_core import verify_user, AuthenticationError, EmailNotVerifiedError

app = FastAPI()

async def get_current_user(authorization: str = Header(...)):
    """Verify JWT token and extract user information."""
    try:
        token = authorization.replace("Bearer ", "")
        return verify_user(token)
    except EmailNotVerifiedError:
        raise HTTPException(403, "Email not verified")
    except AuthenticationError:
        raise HTTPException(401, "Invalid or expired token")

@app.get("/api/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    return {
        "message": "Access granted",
        "user_id": user["uid"],
        "email": user["email"]
    }
```

## Configuration

All environment variables are prefixed with `SAAS_CORE_` to avoid conflicts:

### Required

- **`SAAS_CORE_GOOGLE_PROJECT_ID`**: Your Google Cloud project ID
  - Used to construct issuer URL: `https://securetoken.google.com/{project_id}`
  - Used as default audience for token validation

### Optional

- **`SAAS_CORE_GOOGLE_AUDIENCE`**: Custom audience (defaults to project ID)
  - Override the default audience if needed
  - Must match the audience in your JWT tokens

- **`SAAS_CORE_REQUIRE_EMAIL_VERIFIED`**: Require email verification (default: `True`)
  - Set to `False` to allow unverified emails (not recommended for production)
  - Accepts: `true`, `True`, `1`, `yes`, `false`, `False`, `0`, `no`

- **`SAAS_CORE_JWKS_CACHE_TTL`**: Public key cache TTL in seconds (default: `3600`)
  - Controls how long Google's public keys are cached
  - Shorter TTL = more frequent updates, more API calls
  - Longer TTL = fewer API calls, slower key rotation handling

- **`SAAS_CORE_JWT_LEEWAY`**: Clock skew tolerance in seconds (default: `60`)
  - Allows for small clock differences between servers
  - Prevents false rejections due to minor time discrepancies

- **`SAAS_CORE_DATABASE_URL`**: Database connection string (placeholder for future use)
  - Not currently used - database functionality is a placeholder

## API Reference

### `verify_user(token: str) -> dict`

Verify a JWT token from Google Cloud Identity Platform.

**Parameters:**
- `token` (str): JWT token string (typically from Authorization header)

**Returns:**
- `dict`: User information dictionary with keys:
  - `uid` (str): User ID from 'sub' claim
  - `email` (str): User email address
  - `email_verified` (bool): Email verification status
  - `auth_time` (int, optional): Authentication timestamp

**Raises:**
- `AuthenticationError`: If token is invalid, expired, or verification fails
- `EmailNotVerifiedError`: If email verification is required but not verified
- `ConfigurationError`: If configuration is missing or invalid

**Example:**
```python
from saas_core import verify_user

token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
user_info = verify_user(token)
print(user_info["uid"])  # "user123"
```

### `get_google_public_keys() -> dict`

Fetch and cache Google's public keys from JWKS endpoint.

**Returns:**
- `dict`: Dictionary mapping key_id (kid) to PEM-encoded public key string

**Raises:**
- `AuthenticationError`: If keys cannot be fetched
- `ConfigurationError`: If configuration is invalid

## GCIP Integration

### Authentication Flow

1. **Client Side**: User authenticates with GCIP (via Firebase SDK or Google Identity Services)
2. **Token Issuance**: GCIP issues a JWT token containing user information
3. **Server Side**: Service receives request with JWT token in Authorization header
4. **Verification**: `saas-core` verifies the token:
   - Fetches Google's public keys (with caching)
   - Verifies JWT signature using RS256
   - Validates all claims (iss, aud, exp, iat, nbf)
   - Checks email verification status
5. **User Info**: Returns verified user information

### Token Claims

GCIP tokens contain the following claims:
- `sub`: User ID (unique Google identifier)
- `email`: User email address
- `email_verified`: Boolean indicating email verification status
- `iss`: Issuer URL (`https://securetoken.google.com/{project_id}`)
- `aud`: Audience (project ID or custom)
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `auth_time`: Authentication timestamp

## Security Considerations

### Best Practices

1. **Always Verify Tokens**: Never trust client-provided user IDs. Always extract from verified JWT.
2. **Require Email Verification**: Keep `SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True` in production.
3. **Use HTTPS**: Always use HTTPS in production to protect tokens in transit.
4. **Handle Errors Securely**: Don't expose sensitive information in error messages.
5. **Monitor Key Rotation**: Public keys are cached but automatically refreshed on rotation.

### Zero-Trust Architecture

The library implements zero-trust principles:
- Never trusts client-provided user_id
- Always extracts user_id from verified JWT
- Validates all token claims before accepting
- Fails securely (denies access by default)

## Examples

See the `examples/` directory for complete integration examples:

- **FastAPI Integration**: `examples/usage_example.py`

## Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=saas_core --cov-report=html
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/saas-core.git
cd saas-core
pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy saas_core

# Run tests
pytest
```

## Architecture

This library is designed for the "Hub & Spoke" SaaS architecture:

- **Hub**: Centralized authentication (this library) and shared database
- **Spoke**: Individual services (Billing, Chatbot, etc.) that consume this library

All services use the same authentication mechanism, ensuring consistent user identity across the platform.

## Limitations

- **Database Module**: Currently a placeholder only. Database functionality will be added in a future phase.
- **Billing/Subscriptions**: No billing or subscription functionality is included in this phase.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/Symbiot01/saas-core/issues

## Changelog

### 0.1.0 (Initial Release)

- Initial release with GCIP JWT verification
- Public key caching and rotation handling
- Comprehensive claim validation
- Email verification enforcement
- Framework-agnostic design
