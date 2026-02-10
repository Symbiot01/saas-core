# saas-core Complete Example

This directory contains a complete example showing both frontend and backend authentication flow.

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│  React Frontend │         │  Google GCIP │         │ FastAPI     │
│  (Port 3000)    │         │              │         │ (Port 8000) │
└─────────────────┘         └──────────────┘         └─────────────┘
       │                            │                        │
       │  1. Sign In Request        │                        │
       ├───────────────────────────>│                        │
       │                            │                        │
       │  2. JWT Token              │                        │
       │<───────────────────────────┤                        │
       │                            │                        │
       │  3. API Call + Token      │                        │
       ├─────────────────────────────────────────────────────>│
       │                            │                        │
       │                            │  4. Verify Token       │
       │                            │     (saas-core)        │
       │                            │                        │
       │  5. User Data              │                        │
       │<─────────────────────────────────────────────────────┤
```

## Quick Start

### 1. Backend Setup

```bash
# Set backend config (recommended: .env in repo root)
# Create a file named ".env" in the repo root with:
#   SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
#   SAAS_CORE_REQUIRE_EMAIL_VERIFIED=False   # optional (if you don't use email verification)

# Run backend
cd examples
uvicorn backend:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

### 2. Frontend Setup

```bash
# Install dependencies
cd examples/frontend
npm install

# Configure Firebase in src/App.jsx
# Replace YOUR_API_KEY, YOUR_PROJECT_ID, etc.

# Run frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 3. Test the Flow

1. Open `http://localhost:3000` in your browser
2. Sign up / sign in with email + password
4. Click "Call Protected API" to test backend verification
5. See the user data returned from your backend

## Files

- `backend.py` - FastAPI backend with saas-core integration
- `frontend/` - React frontend with Firebase authentication
- `usage_example.py` - Original FastAPI example (without CORS)

## Configuration

### Backend Environment Variables

```bash
export SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
export SAAS_CORE_REQUIRE_EMAIL_VERIFIED=True
```

### Frontend Firebase Config

Edit `frontend/src/App.jsx`:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",  // Must match backend project ID
};
```

**Important**: The `projectId` in Firebase config must match `SAAS_CORE_GOOGLE_PROJECT_ID` in your backend!

## How It Works

### Frontend (React)
1. User signs up / signs in with email + password (Firebase Auth)
2. Firebase returns JWT token
3. Frontend stores token and sends it to backend in API requests

### Backend (FastAPI + saas-core)
1. Receives API request with `Authorization: Bearer <token>` header
2. Extracts token from header
3. Calls `verify_user(token)` from saas-core
4. saas-core verifies JWT signature and claims
5. Returns user information (uid, email, etc.)
6. Backend returns data to frontend

## Troubleshooting

### CORS Errors
- Make sure backend CORS is configured for `http://localhost:3000`
- Check that backend is running on port 8000

### Authentication Errors
- Verify `projectId` matches in both frontend and backend
- Check that Firebase project has Email/Password enabled
- Ensure `SAAS_CORE_GOOGLE_PROJECT_ID` is set correctly

### Token Errors
- Make sure token is being sent in `Authorization: Bearer <token>` format
- Check browser console for token issues
- Verify backend is receiving the token correctly
