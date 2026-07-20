# Authentication & Pages Setup

## Overview

Your CareAnchor application now has a complete authentication flow with multiple pages for authenticated users.

## What Was Fixed

The 404 error occurred because the auth redirect was pointing to `/_authenticated/app` instead of `/app`. TanStack Router uses the `_authenticated` folder as a layout route, so child routes are accessed without the underscore prefix.

## New Routes

### Public Routes
- **`/`** - Landing page with product information
  - Automatically redirects authenticated users to `/dashboard`
  
- **`/auth`** - Sign in and sign up page
  - Handles both login and registration
  - Shows email confirmation screen after signup
  - Redirects to `/dashboard` after successful login

### Protected Routes (require authentication)
- **`/dashboard`** - Main dashboard
  - Overview of recovery tracking
  - Quick action cards to start chat, view profile
  - Information about how CareAnchor works
  
- **`/app`** - Chat interface
  - Full conversational interface with CareAnchor agent
  - Real-time WebSocket connection
  - Clinical memory viewer in sidebar
  - Live streaming responses
  
- **`/settings`** - User settings
  - Account information
  - Notification preferences
  - Privacy controls
  - Data management
  
- **`/logout`** - Sign out handler
  - Automatically signs user out
  - Redirects to landing page

## Navigation

All authenticated pages include a consistent navigation bar with:
- Logo/branding linking back to dashboard
- Navigation links (Dashboard, Chat, Settings)
- Connection status (for chat page)
- Sign out link

## Authentication Flow

1. **Landing Page** (`/`)
   - Unauthenticated: Shows marketing content
   - Authenticated: Auto-redirects to `/dashboard`

2. **Sign In** (`/auth`)
   - User enters credentials
   - On success: Redirect to `/dashboard`
   - On error: Show error message

3. **Sign Up** (`/auth`)
   - User creates account
   - Sends confirmation email
   - Shows confirmation screen
   - User confirms via email link
   - User returns and signs in

4. **Protected Routes**
   - Check authentication before loading
   - If not authenticated: Redirect to `/auth`
   - If authenticated: Load the page

5. **Sign Out** (`/logout`)
   - Clear session
   - Redirect to `/`

## Key Features

✅ **Auto-redirect**: Authenticated users can't access `/` or `/auth`  
✅ **Protected routes**: All routes under `_authenticated/` require login  
✅ **Persistent sessions**: Session state managed by Supabase  
✅ **Real-time updates**: WebSocket connection for chat  
✅ **Consistent navigation**: Same nav bar across all pages  
✅ **Mobile responsive**: Works on all screen sizes  

## Running the Application

```bash
# Start the development server
npm run dev

# The app will be available at http://localhost:3000
```

## Next Steps

You can now:
1. Sign in to your existing account
2. Create a new account if needed
3. Access the dashboard at `/dashboard`
4. Start chatting with CareAnchor at `/app`
5. Manage settings at `/settings`

All pages are fully functional and styled consistently with your design system.
