# OAuth Authentication Setup Guide

## Overview
The platform now includes Google OAuth authentication with per-user store quotas.

## Quick Setup Steps

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen if prompted
6. Choose **Web application** as application type
7. Add authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/callback/google` (for local dev)
   - `https://your-domain.com/api/v1/auth/callback/google` (for production)
8. Save and copy the **Client ID** and **Client Secret**

### 2. Configure Backend Environment

Create or update `/home/shrey/Urumi-Ai/Backend/.env`:

```env
# OAuth - Google
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/google

# Frontend URL
FRONTEND_URL=http://localhost:5173

# JWT Secret (IMPORTANT: Change this in production!)
JWT_SECRET_KEY=generate-a-random-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Per-user store quota
MAX_STORES_PER_USER=5
```

**Generate a secure JWT secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Install Python Dependencies

```bash
cd /home/shrey/Urumi-Ai/Backend
pip install -r requirements.txt
```

### 4. Reset Database (if needed)

Since we added new models (User), you may need to reset the database:

```bash
cd /home/shrey/Urumi-Ai/Backend
rm -f stores.db  # Delete old database
# The new database with User and updated Store models will be created on startup
```

### 5. Start Backend

```bash
cd /home/shrey/Urumi-Ai/Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Frontend

```bash
cd /home/shrey/Urumi-Ai/Frontend
npm run dev
```

## Testing the Authentication Flow

1. Navigate to `http://localhost:5173`
2. You'll see the login page with "Continue with Google" button
3. Click the button to initiate OAuth flow
4. Login with your Google account
5. You'll be redirected back to the dashboard
6. Your email will be displayed in the header
7. Create stores (limited to 5 per user by default)

## How It Works

### Authentication Flow

```
User clicks "Continue with Google"
         ↓
Frontend → GET /api/v1/auth/login/google
         ↓
Backend returns Google OAuth URL
         ↓
User redirected to Google login
         ↓
User authorizes the app
         ↓
Google redirects to /api/v1/auth/callback/google
         ↓
Backend exchanges code for user info
         ↓
Backend creates/updates User in database
         ↓
Backend generates JWT token
         ↓
Redirects to frontend with token
         ↓
Frontend stores token in localStorage
         ↓
All API requests include Bearer token
```

### Per-User Store Isolation

- Each user can create up to `MAX_STORES_PER_USER` stores (default: 5)
- Users only see their own stores
- Store operations (view, delete) are scoped to the authenticated user
- Store records include `user_id` foreign key
- Deleting a user cascades to delete their stores

### Token Management

- JWT tokens expire after 7 days (configurable)
- Tokens are stored in browser localStorage
- Automatic logout on 401 responses
- Tokens include user ID and email

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | - | Google OAuth Client ID (required) |
| `GOOGLE_CLIENT_SECRET` | - | Google OAuth Client Secret (required) |
| `JWT_SECRET_KEY` | - | Secret key for signing JWT tokens (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 10080 | Token expiration time (7 days) |
| `MAX_STORES_PER_USER` | 5 | Maximum stores per user |
| `OAUTH_REDIRECT_URI` | - | OAuth callback URL |
| `FRONTEND_URL` | http://localhost:5173 | Frontend URL for redirects |

## Security Features

✅ **OAuth 2.0** - Industry-standard authentication  
✅ **JWT Tokens** - Stateless authentication  
✅ **CSRF Protection** - State parameter in OAuth flow  
✅ **Per-User Isolation** - Users only access their own resources  
✅ **Automatic Token Expiry** - 7-day expiration  
✅ **Bearer Token Auth** - Secure API access  

## API Endpoints

### Authentication

- `GET /api/v1/auth/login/google` - Initiate Google OAuth
- `GET /api/v1/auth/callback/google` - OAuth callback handler
- `GET /api/v1/auth/me` - Get current user info (requires auth)
- `POST /api/v1/auth/logout` - Logout (client-side token removal)

### Store Management (All require authentication)

- `GET /api/v1/stores` - List user's stores
- `GET /api/v1/stores/{id}` - Get store details
- `POST /api/v1/stores` - Create new store (quota enforced)
- `DELETE /api/v1/stores/{id}` - Delete store
- `GET /api/v1/stores/{id}/pods` - Get store pods

## Troubleshooting

### "Invalid authentication credentials"

- Check if JWT_SECRET_KEY is set in .env
- Verify token is being sent in Authorization header
- Check token hasn't expired

### "OAuth authentication failed"

- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
- Check redirect URI matches what's configured in Google Console
- Ensure OAuth consent screen is published (not in testing mode)

### "Maximum number of stores per user reached"

- User has reached MAX_STORES_PER_USER limit
- Delete some stores or increase the limit in config

### Database errors after upgrade

- Delete the old database: `rm Backend/stores.db`
- Restart the backend to create new schema with User model

## Production Deployment

For production, update these in your .env:

```env
DEBUG=false
OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/callback/google
FRONTEND_URL=https://your-domain.com
JWT_SECRET_KEY=<long-random-secure-key>
```

Also update Google Cloud Console with production redirect URI.

## Next Steps

- [ ] Add more OAuth providers (GitHub, Microsoft)
- [ ] Add user profile management page
- [ ] Add admin dashboard to manage all users
- [ ] Implement refresh tokens for longer sessions
- [ ] Add email verification
- [ ] Add rate limiting per user
