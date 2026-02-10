# saas-core

Core authentication library for Hub & Spoke SaaS architecture with Google Cloud Identity Platform (GCIP) / Firebase Authentication integration.

## Overview

`saas-core` provides a simple, consistent wrapper around Firebase Admin SDK for JWT authentication verification across microservices. It eliminates the need to copy-paste Firebase initialization and token verification code into every service.

### Key Features

- **Firebase Admin SDK Wrapper**: Uses the battle-tested Firebase Admin SDK under the hood
- **DRY Principle**: Write Firebase initialization and verification logic once, use everywhere
- **Automatic Initialization**: Handles Firebase Admin SDK setup automatically
- **Consistent Error Handling**: Standardized error messages across all services
- **Email Verification**: Configurable email verification requirement
- **Framework Agnostic**: Works with any Python web framework (FastAPI, Flask, Django, etc.)
- **Simple Configuration**: Just set environment variables

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

### 1. Set Up Firebase / Google Cloud Identity Platform

1. Create a Google Cloud project
2. Enable Firebase Authentication / Identity Platform API
3. Configure authentication providers (Google Sign-In, Email/Password, etc.)
4. Download your service account JSON key from Firebase Console:
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely

### 2. Configure Environment Variables

**Option 1: Service Account JSON File (Recommended for Local Development)**
```bash
export SAAS_CORE_FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
export SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True
```

**Option 2: Service Account JSON String (Recommended for Containers/CI)**
```bash
export SAAS_CORE_FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
export SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True
```

**Option 3: Project ID (For Google Cloud environments with Application Default Credentials)**
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

### Required (One of the following)

- **`SAAS_CORE_FIREBASE_CREDENTIALS_PATH`**: Path to Firebase service account JSON file
  - Recommended for local development
  - Download from Firebase Console → Project Settings → Service Accounts

- **`SAAS_CORE_FIREBASE_CREDENTIALS_JSON`**: Firebase service account JSON as string
  - Recommended for containers, CI/CD, and environments where mounting files is difficult
  - Pass the entire JSON content as a string (can be minified or formatted)
  - JSON is validated on load

- **`SAAS_CORE_GOOGLE_PROJECT_ID`**: Google Cloud project ID
  - Use this if running on Google Cloud (GCE, Cloud Run, etc.) with Application Default Credentials
  - Alternative to service account JSON file or string

### Optional

- **`SAAS_CORE_REQUIRE_EMAIL_VERIFIED`**: Require email verification (default: `True`)
  - Set to `False` to allow unverified emails (not recommended for production)
  - Accepts: `true`, `True`, `1`, `yes`, `false`, `False`, `0`, `no`

- **`SAAS_CORE_DATABASE_URL`**: Database connection string (placeholder for future use)
  - Not currently used - database functionality is a placeholder

## API Reference

### `verify_user(token: str) -> dict`

Verify a JWT token from Google Cloud Identity Platform.

**Parameters:**
- `token` (str): JWT token string (typically from Authorization header)

**Returns:**
- `dict`: User information dictionary with keys:
  - `uid` (str): User ID from Firebase
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

## Firebase / GCIP Integration

### Why Use a Wrapper?

Instead of copy-pasting Firebase Admin SDK initialization and verification code into every service, `saas-core` provides a simple wrapper that:

1. **Initializes Firebase Admin SDK** automatically (only once)
2. **Handles token verification** with consistent error handling
3. **Checks email verification** if required
4. **Returns standardized user info** dictionary

### Authentication Flow

1. **Client Side**: User authenticates with Firebase (via Firebase SDK)
2. **Token Issuance**: Firebase issues a JWT ID token
3. **Server Side**: Service receives request with JWT token in Authorization header
4. **Verification**: `saas-core` wraps Firebase Admin SDK's `verify_id_token()`:
   - Initializes Firebase Admin SDK (if not already done)
   - Calls `auth.verify_id_token(token)` - Firebase handles all JWT verification
   - Checks email verification status (if required)
   - Returns standardized user info
5. **User Info**: Returns verified user information

### What Firebase Admin SDK Handles

Firebase Admin SDK automatically:
- Fetches and caches Google's public keys
- Verifies JWT signature using RS256
- Validates all claims (iss, aud, exp, iat, nbf)
- Handles key rotation
- Manages certificate caching

You don't need to worry about any of this - Firebase Admin SDK does it all!

## Security Considerations

### Best Practices

1. **Always Verify Tokens**: Never trust client-provided user IDs. Always extract from verified JWT.
2. **Require Email Verification**: Keep `SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True` in production.
3. **Use HTTPS**: Always use HTTPS in production to protect tokens in transit.
4. **Handle Errors Securely**: Don't expose sensitive information in error messages.
5. **Secure Service Account Keys**: Keep your Firebase service account JSON file secure and never commit it to version control.
6. **Use Application Default Credentials**: On Google Cloud, prefer `SAAS_CORE_GOOGLE_PROJECT_ID` over service account files.

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

- Initial release with Firebase Admin SDK wrapper
- Automatic Firebase initialization
- Consistent error handling
- Email verification enforcement
- Framework-agnostic design
