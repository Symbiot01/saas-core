# Quick Start Guide

Get the complete authentication flow running in 5 minutes!

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- Firebase/GCIP project set up
- Your Google Project ID

## Step 1: Backend (2 minutes)

```bash
# Set backend config (recommended: .env in repo root)
# Create a file named ".env" in the repo root with:
#   SAAS_CORE_GOOGLE_PROJECT_ID=your-project-id
#   SAAS_CORE_REQUIRE_EMAIL_VERIFIED=False   # optional (if you don't use email verification)

# Run backend
cd examples
uvicorn backend:app --reload --port 8000
```

✅ Backend running at: `http://localhost:8000`

## Step 2: Frontend - Option A: React (2 minutes)

```bash
# Install dependencies
cd examples/frontend
npm install

# Edit src/App.jsx - replace Firebase config:
#   apiKey: "YOUR_API_KEY"
#   authDomain: "YOUR_PROJECT.firebaseapp.com"
#   projectId: "YOUR_PROJECT_ID"  # Must match backend!

# Run frontend
npm run dev
```

✅ Frontend running at: `http://localhost:3000`

## Step 2: Frontend - Option B: Simple HTML (1 minute)

1. Open `examples/simple.html` in a text editor
2. Replace Firebase config (lines ~150-154):
   ```javascript
   const firebaseConfig = {
       apiKey: "YOUR_API_KEY",
       authDomain: "YOUR_PROJECT.firebaseapp.com",
       projectId: "YOUR_PROJECT_ID",  // Must match backend!
   };
   ```
3. Open `simple.html` in your browser

✅ No server needed - just open the HTML file!

## Step 3: Test It!

1. Open frontend (React: `http://localhost:3000` or HTML file)
2. Sign up / sign in with email + password
4. Click "Call Protected API"
5. See your user data from the backend! 🎉

## Troubleshooting

**Backend won't start?**
- Check `SAAS_CORE_GOOGLE_PROJECT_ID` is set
- Make sure port 8000 is available

**Frontend can't connect?**
- Check backend is running on port 8000
- Check CORS settings in `backend.py`

**Authentication fails?**
- Verify `projectId` matches in frontend and backend
- Check Firebase project has Email/Password enabled
- Check browser console for errors

**Token verification fails?**
- Ensure `SAAS_CORE_GOOGLE_PROJECT_ID` matches Firebase `projectId`
- Check backend logs for error messages

## What's Happening?

1. **User signs in** → Firebase handles Google OAuth
2. **Firebase returns JWT** → Token stored in frontend
3. **Frontend calls API** → Sends token in `Authorization: Bearer <token>` header
4. **Backend verifies** → saas-core verifies token signature and claims
5. **Backend returns data** → User information sent back to frontend

That's it! You now have a complete authentication flow. 🚀
