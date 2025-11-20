# Postman API Testing Guide - WildWud Backend

## Base URL
```
http://127.0.0.1:8000
```

## Authentication
Most APIs require JWT Bearer token. Get token from login/register endpoints first.

---

## 1. User Registration
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/accounts/register/`  
**Headers:** 
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
}
```

**Expected Response (201 Created):**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2024-01-15T10:30:00Z",
        "is_active": true
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response (400 Bad Request) - Password Mismatch:**
```json
{
    "password": ["Password fields didn't match."]
}
```

**Error Response (400 Bad Request) - Duplicate Username:**
```json
{
    "username": ["A user with that username already exists."]
}
```

---

## 2. User Login
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/accounts/login/`  
**Headers:** 
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "SecurePass123!"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2024-01-15T10:30:00Z",
        "is_active": true
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response (401 Unauthorized) - Invalid Credentials:**
```json
{
    "error": "Invalid credentials"
}
```

**Error Response (400 Bad Request) - Missing Fields:**
```json
{
    "error": "Username and password are required"
}
```

---

## 3. Get User Profile (Authenticated)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/accounts/profile/`  
**Headers:** 
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA1MzQ0MDAwLCJpYXQiOjE3MDUzMDAwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ...
Content-Type: application/json
```

**Request Body:** None

**Expected Response (200 OK):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2024-01-15T10:30:00Z",
    "is_active": true
}
```

**Error Response (401 Unauthorized) - No Token:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## 4. Update User Profile (Authenticated)
**Method:** `PUT` or `PATCH`  
**URL:** `http://127.0.0.1:8000/api/accounts/profile/update/`  
**Headers:** 
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA1MzQ0MDAwLCJpYXQiOjE3MDUzMDAwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ...
Content-Type: application/json
```

### 5a. Update Profile Only (PATCH)
**Request Body:**
```json
{
    "first_name": "Johnny",
    "last_name": "Smith",
    "email": "johnny.smith@example.com"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Profile updated successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "johnny.smith@example.com",
        "first_name": "Johnny",
        "last_name": "Smith",
        "date_joined": "2024-01-15T10:30:00Z",
        "is_active": true
    }
}
```

### 5b. Update Password (PATCH)
**Request Body:**
```json
{
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "confirm_password": "NewSecurePass456!"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Profile updated successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2024-01-15T10:30:00Z",
        "is_active": true
    }
}
```

### 5c. Update Profile + Password (PATCH)
**Request Body:**
```json
{
    "first_name": "Johnny",
    "email": "johnny@example.com",
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "confirm_password": "NewSecurePass456!"
}
```

**Error Response (400 Bad Request) - Wrong Current Password:**
```json
{
    "current_password": ["You have entered a wrong password"]
}
```

**Error Response (400 Bad Request) - Password Mismatch:**
```json
{
    "confirm_password": ["Confirm password does not match"]
}
```

---

## 5. User Logout (Authenticated)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/accounts/logout/`  
**Headers:** 
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA1MzQ0MDAwLCJpYXQiOjE3MDUzMDAwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ...
Content-Type: application/json
```

**Request Body (Optional):**
```json
{
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Logout successful"
}
```

**Error Response (401 Unauthorized) - No Token:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## 6. List All Users (Admin Only)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/accounts/users/`  
**Headers:** 
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA1MzQ0MDAwLCJpYXQiOjE3MDUzMDAwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ...
Content-Type: application/json
```

**Request Body:** None

**Expected Response (200 OK) - Paginated:**
```json
{
    "count": 10,
    "next": "http://127.0.0.1:8000/api/accounts/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "date_joined": "2024-01-15T10:30:00Z",
            "is_active": true
        },
        {
            "id": 2,
            "username": "jane_smith",
            "email": "jane.smith@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_joined": "2024-01-16T11:00:00Z",
            "is_active": true
        }
    ]
}
```

**Error Response (403 Forbidden) - Not Admin:**
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

## Testing Workflow in Postman

### Step 1: Register a New User
1. Use **Registration API** with dummy data
2. Copy the `access_token` from response
3. Save it for next requests (valid for 30 days)

### Step 2: Test Authenticated APIs
1. Add `Authorization: Bearer <token>` header
2. Test Profile APIs
3. Test Logout API

### Step 3: Create Admin User (via Django Admin)
1. Go to `http://127.0.0.1:8000/admin/`
2. Create superuser: `python manage.py createsuperuser`
3. Login and set `is_staff=True` and `is_superuser=True` for a user
4. Use that user's token to test Admin APIs

---

## Postman Collection Variables

Create these variables in Postman:
- `base_url`: `http://127.0.0.1:8000`
- `access_token`: (will be set after login)

Then use in URLs: `{{base_url}}/api/accounts/login/`

---

## Quick Test Data

### User 1 (Regular User)
```json
{
    "username": "testuser1",
    "email": "testuser1@example.com",
    "first_name": "Test",
    "last_name": "User1",
    "password": "TestPass123!",
    "password2": "TestPass123!"
}
```

### User 2 (Regular User)
```json
{
    "username": "testuser2",
    "email": "testuser2@example.com",
    "first_name": "Test",
    "last_name": "User2",
    "password": "TestPass123!",
    "password2": "TestPass123!"
}
```

### Admin User (Create via Django Admin)
- Username: `admin`
- Email: `admin@example.com`
- Password: `AdminPass123!`
- Set `is_staff=True` and `is_superuser=True`

---

## Common Issues & Solutions

1. **401 Unauthorized**: Check if token is valid and not expired
2. **403 Forbidden**: User doesn't have admin permissions
3. **400 Bad Request**: Check request body format and required fields
4. **Token Expired**: Access token is valid for 30 days. If expired, user needs to login again.

---

## Swagger UI Testing

You can also test APIs directly in Swagger UI:
- URL: `http://127.0.0.1:8000/swagger/`
- Click "Authorize" button
- Enter: `Bearer <your_access_token>`
- Test APIs directly from browser

