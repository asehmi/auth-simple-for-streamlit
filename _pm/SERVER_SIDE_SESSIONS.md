# Server-Side Session Tokens Implementation Guide

**Status:** In Progress - Ready to implement  
**Date:** April 4, 2026

## Overview

Switching from browser cookies/localStorage to **server-side session tokens** stored in the database. This eliminates JavaScript timing issues and provides cleaner, more secure session management.

## Why This Approach

✅ No JavaScript complexity  
✅ No timing/async issues  
✅ Server controls all session data  
✅ Linear, clean code (no status flags)  
✅ Synchronous operations  
✅ More secure (tokens, not user data in browser)  

## What's Already Done

1. ✅ Created `authlib/auth_session.py` — Server-side token management class
2. ✅ Updated `authlib/common/const.py` — Added `AUTH_TOKEN` constant
3. ✅ Updated `authlib/auth.py` — Uses tokens instead of user data in browser
4. ✅ Code is ready to use once DB schemas are updated

## Step 1: Update SQLite Schema

Run these SQL commands on your SQLite database:

```sql
-- Add auth_token column
ALTER TABLE users ADD COLUMN auth_token TEXT DEFAULT NULL;

-- Add expires_at column  
ALTER TABLE users ADD COLUMN expires_at TEXT DEFAULT NULL;
```

**Location:** Your SQLite database file (likely `db/auth.db` or similar)

**Verification:** After running, check that both columns exist:
```sql
PRAGMA table_info(users);
```

Should show columns: `username`, `password`, `su`, `auth_token`, `expires_at`

## Step 2: Update Airtable Schema

If using Airtable, add two new fields to your `users` table:

1. **Field 1:**
   - Name: `auth_token`
   - Type: `Single line text`
   - Required: No
   - Default: (leave empty)

2. **Field 2:**
   - Name: `expires_at`
   - Type: `Single line text`
   - Required: No
   - Default: (leave empty)

**Verification:** Both fields should appear in your Airtable table alongside username, password, and su.

## Step 3: Test the Implementation

Once schemas are updated, the code should work immediately. Test the flow:

1. **Login with "Remember me":**
   - Enter credentials
   - Check "Remember me"
   - Click Login
   - You should see "Logging in..." message

2. **Browser Close/Reopen:**
   - Close the browser window completely
   - Reopen and navigate to the app
   - Should auto-login with "Auto-logged in" message
   - Check browser developer tools (F12 → Application → Cookies) and verify there's a simple token value (NOT user data)

3. **Logout:**
   - Click Logout button
   - Should see login form immediately
   - Browser should show no `st-auth-simple` cookie (or empty value)
   - Database `auth_token` for that user should be `NULL`

4. **Verify Database:**
   - After successful login with "Remember me", check DB:
     - SQLite: `SELECT username, auth_token, expires_at FROM users WHERE username='<your_user>';`
     - Airtable: Look at the user record, should have token and expiry date filled in
   - After logout:
     - Both `auth_token` and `expires_at` should be NULL/empty

## How It Works (Implementation Details)

### AuthSession Class (`authlib/auth_session.py`)

**Methods:**

1. **`generate_token()`**
   - Creates a secure random 32-char token
   - Used internally when creating session

2. **`create_session(store, user, expires_in_days=30)`**
   - Called on login with "Remember me"
   - Generates token
   - Stores token + expiration in DB
   - Returns token to be sent to browser

3. **`validate_session(store, token)`**
   - Called when trying to auto-login from cookie
   - Looks up token in DB
   - Checks if expired
   - Returns user dict if valid, None if invalid/expired

4. **`clear_session(store, username)`**
   - Called on logout
   - Sets token and expires_at to NULL in DB
   - Complete cleanup, no JavaScript needed

### Auth Flow Changes

**Login (with Remember me):**
```
User submits form
  ↓
Validate credentials
  ↓
Create server-side token: AuthSession.create_session()
  ↓
Store token in browser cookie (just 32 chars, not user data)
  ↓
Login complete
```

**Auto-login (browser reopens):**
```
Read token from browser cookie
  ↓
Validate token: AuthSession.validate_session(token)
  ↓
Check expiration in DB
  ↓
Return user if valid (from DB)
  ↓
If expired: delete token, show login
```

**Logout:**
```
Clear token from DB: AuthSession.clear_session()
  ↓
Delete browser cookie
  ↓
Rerun auth
  ↓
Show login form
```

## Constants Added

In `authlib/common/const.py`:
```python
AUTH_TOKEN = 'auth_token'
```

Already added, no action needed.

## No More Status Flags!

Old approach (with flags):
```python
logout():
    state.clear_cookie_on_next_auth = True  # Flag
    st.rerun()

_try_cookie_login():
    if state.clear_cookie_on_next_auth:  # Check flag
        state.clear_cookie_on_next_auth = False  # Reset flag
        return False
```

New approach (linear):
```python
logout():
    AuthSession.clear_session()  # Synchronous, done immediately
    st.rerun()

_try_cookie_login():
    user = AuthSession.validate_session(token)  # Just validate
```

## Rollback Plan (If Issues)

If something goes wrong:

1. **SQLite:** Remove the columns you added (you can do this in SQL or just delete the DB file and recreate)
2. **Airtable:** Delete the two fields you added
3. **Code:** Is already written to gracefully handle missing tokens (returns None)

The old code still supports login without "Remember me", so basic functionality works even if server-side session breaks.

## Files Modified

- ✅ `authlib/auth_session.py` — NEW file, server-side token management
- ✅ `authlib/auth.py` — Updated to use tokens
- ✅ `authlib/common/const.py` — Added AUTH_TOKEN constant

## What To Check Tomorrow

1. Are both DB schemas updated? (auth_token and expires_at columns added)
2. Can you login normally (without "Remember me")? — Should still work
3. Can you login with "Remember me"? — Token should be created in DB
4. Close/reopen browser — Auto-login should work
5. Logout — Token should be cleared from DB, login form shown
6. Hard refresh after logout — Should NOT auto-login (token is gone)

## Questions/Issues?

If you run into problems:
- Check browser console (F12) for errors
- Check DB directly to see if tokens are being created
- Verify column names are exactly: `auth_token` and `expires_at` (lowercase, no spaces)
- Make sure you're on the latest code (do `git pull` or `pip install -e .`)

Good luck! This should be much cleaner once it's working. 🎉
