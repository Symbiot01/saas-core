# React Frontend Example for saas-core

Simple React frontend that demonstrates authentication with Firebase and API calls to the saas-core backend.

## Setup

### 1. Install Dependencies

```bash
cd examples/frontend
npm install
```

### 2. Configure Firebase

Edit `src/App.jsx` and replace the Firebase configuration:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",  // Must match SAAS_CORE_GOOGLE_PROJECT_ID
};
```

You can find these values in:
- Firebase Console → Project Settings → General
- Or Google Cloud Console → APIs & Services → Credentials

### 3. Run the Frontend

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## How It Works

1. **Sign In**: User clicks "Sign in with Google" → Firebase handles OAuth
2. **Get Token**: Firebase returns JWT token
3. **API Calls**: Frontend sends token to backend in `Authorization: Bearer <token>` header
4. **Backend Verifies**: saas-core verifies the token and returns user data

## Backend Setup

Make sure the backend is running (see `../backend.py`):

```bash
export SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
uvicorn examples.backend:app --reload --port 8000
```

## Features

- ✅ Google Sign-In with Firebase
- ✅ JWT token management
- ✅ Protected API calls
- ✅ User profile fetching
- ✅ Error handling
- ✅ Clean, simple UI
