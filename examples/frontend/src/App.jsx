import { useState, useEffect } from 'react'
import { initializeApp } from 'firebase/app'
import { 
  getAuth, 
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendEmailVerification,
  signOut, 
  onAuthStateChanged 
} from 'firebase/auth'
import './App.css'

// Firebase configuration
// Replace these with your Firebase project credentials
const firebaseConfig = {
  apiKey: "AIzaSyDVlV_SrHSDFEO13By3-0V8Fu7nC-Gi72g",
  authDomain: "medrecs-485208.firebaseapp.com",
  projectId: "medrecs-485208" , // This should match SAAS_CORE_GOOGLE_PROJECT_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

// Backend API URL
const API_URL = 'http://localhost:8000'

function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [apiData, setApiData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  
  // Email/password form state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)

  useEffect(() => {
    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        setUser(firebaseUser)
        // Get the JWT token
        const idToken = await firebaseUser.getIdToken()
        setToken(idToken)
        setNotice(null)
      } else {
        setUser(null)
        setToken(null)
        setApiData(null)
        setNotice(null)
      }
    })

    return () => unsubscribe()
  }, [])

  const handleSignUp = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      const result = await createUserWithEmailAndPassword(auth, email, password)
      console.log('Signed up:', result.user.email)
      await sendEmailVerification(result.user)
      setNotice('Verification email sent. Check your inbox, click the link, then come back and click “I verified, refresh”.')
      // Clear form
      setEmail('')
      setPassword('')
    } catch (err) {
      setError(`Sign up error: ${err.message}`)
      console.error('Sign up error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSignIn = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      const result = await signInWithEmailAndPassword(auth, email, password)
      console.log('Signed in:', result.user.email)
      // Clear form
      setEmail('')
      setPassword('')
    } catch (err) {
      setError(`Sign in error: ${err.message}`)
      console.error('Sign in error:', err)
    } finally {
      setLoading(false)
    }
  }

  const resendVerificationEmail = async () => {
    if (!auth.currentUser) return
    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      await sendEmailVerification(auth.currentUser)
      setNotice('Verification email re-sent. Check your inbox (and spam).')
    } catch (err) {
      setError(`Resend verification error: ${err.message}`)
      console.error('Resend verification error:', err)
    } finally {
      setLoading(false)
    }
  }

  const refreshAfterVerification = async () => {
    if (!auth.currentUser) return
    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      // Refresh local user record from Firebase Auth
      await auth.currentUser.reload()
      setUser({ ...auth.currentUser })
      // Force-refresh ID token so email_verified claim updates
      const freshToken = await auth.currentUser.getIdToken(true)
      setToken(freshToken)
      if (auth.currentUser.emailVerified) {
        setNotice('Email verified ✅ Token refreshed.')
      } else {
        setNotice('Still showing unverified. Make sure you clicked the link in the email, then try again.')
      }
    } catch (err) {
      setError(`Refresh error: ${err.message}`)
      console.error('Refresh error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut(auth)
      setApiData(null)
      setNotice(null)
      console.log('Signed out')
    } catch (err) {
      setError(`Sign out error: ${err.message}`)
      console.error('Sign out error:', err)
    }
  }

  const fetchProtectedData = async () => {
    if (!token) {
      setError('No token available')
      return
    }
    if (user && !user.emailVerified) {
      setError('Email not verified yet. Verify your email, then click “I verified, refresh”.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      
      const response = await fetch(`${API_URL}/api/protected`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to fetch data')
      }

      const data = await response.json()
      setApiData(data)
      console.log('API Response:', data)
    } catch (err) {
      setError(`API error: ${err.message}`)
      console.error('API error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProfile = async () => {
    if (!token) {
      setError('No token available')
      return
    }
    if (user && !user.emailVerified) {
      setError('Email not verified yet. Verify your email, then click “I verified, refresh”.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setNotice(null)
      
      const response = await fetch(`${API_URL}/api/user/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to fetch profile')
      }

      const data = await response.json()
      setApiData(data)
      console.log('Profile Response:', data)
    } catch (err) {
      setError(`API error: ${err.message}`)
      console.error('API error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="card">
        <h1>🔐 saas-core Auth Example</h1>
        <p className="subtitle">React + Firebase + FastAPI</p>

        {!user ? (
          <div className="auth-section">
            <div className="auth-tabs">
              <button 
                className={!isSignUp ? 'tab active' : 'tab'}
                onClick={() => setIsSignUp(false)}
              >
                Sign In
              </button>
              <button 
                className={isSignUp ? 'tab active' : 'tab'}
                onClick={() => setIsSignUp(true)}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={isSignUp ? handleSignUp : handleSignIn}>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                  minLength={6}
                />
              </div>

              <button 
                type="submit"
                disabled={loading}
                className="btn btn-primary"
              >
                {loading 
                  ? (isSignUp ? 'Signing up...' : 'Signing in...') 
                  : (isSignUp ? 'Sign Up' : 'Sign In')
                }
              </button>
            </form>
          </div>
        ) : (
          <div className="user-section">
            <div className="user-info">
              <h2>Welcome! 👋</h2>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>User ID:</strong> {user.uid}</p>
              <p>
                <strong>Email verified:</strong>{' '}
                {user.emailVerified ? '✅ Yes' : '❌ No'}
              </p>
              <p className="token-preview">
                <strong>Token:</strong> {token ? `${token.substring(0, 50)}...` : 'Loading...'}
              </p>
            </div>

            <div className="actions">
              {!user.emailVerified && (
                <>
                  <button
                    onClick={resendVerificationEmail}
                    disabled={loading}
                    className="btn btn-secondary"
                  >
                    {loading ? 'Loading...' : 'Resend verification email'}
                  </button>
                  <button
                    onClick={refreshAfterVerification}
                    disabled={loading}
                    className="btn btn-secondary"
                  >
                    {loading ? 'Loading...' : 'I verified, refresh'}
                  </button>
                </>
              )}
              <button 
                onClick={fetchProtectedData}
                disabled={loading || (user && !user.emailVerified)}
                className="btn btn-secondary"
              >
                {loading ? 'Loading...' : 'Call Protected API'}
              </button>
              
              <button 
                onClick={fetchProfile}
                disabled={loading || (user && !user.emailVerified)}
                className="btn btn-secondary"
              >
                {loading ? 'Loading...' : 'Get Profile'}
              </button>

              <button 
                onClick={handleSignOut}
                className="btn btn-danger"
              >
                Sign Out
              </button>
            </div>

            {apiData && (
              <div className="api-response">
                <h3>API Response:</h3>
                <pre>{JSON.stringify(apiData, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {notice && (
          <div className="notice">
            <strong>Info:</strong> {notice}
          </div>
        )}

        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className="info">
          <p><strong>Backend:</strong> {API_URL}</p>
          <p><strong>Status:</strong> {user ? '✅ Authenticated' : '❌ Not authenticated'}</p>
        </div>
      </div>
    </div>
  )
}

export default App
