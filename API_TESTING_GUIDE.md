# Complete API Testing Guide - WildWud Backend

## Base URL
```
http://127.0.0.1:8000
```

## ✅ Setup Status
- ✅ Migrations: Applied successfully
- ✅ Demo Users: 3 users created (demo_user1, demo_user2, demo_user3)
- ✅ Products: 91 products imported with 858 images and 611 reviews
- ✅ Pagination: Removed (frontend handles pagination - APIs return arrays directly)
- ✅ Swagger: Available at `http://127.0.0.1:8000/swagger/`

---

## 🔐 Authentication

Most APIs require JWT Bearer token. Get token from login/register endpoints first.
- **Token Validity:** 30 days
- **Admin APIs:** Require admin user token
- **Authenticated APIs:** Require any logged-in user token
- **Public APIs:** No authentication needed (GET requests)

### Demo Users:
```
Username: demo_user1, demo_user2, demo_user3
Password: DemoPass123!
Email: demo1@example.com, demo2@example.com, demo3@example.com
```

---

## 📋 Table of Contents

1. [Accounts APIs](#1-accounts-apis)
2. [GalleryItem APIs](#2-galleryitem-apis)
   - [Categories](#21-categories-apis)
   - [Gallery Items](#22-gallery-items-apis)
   - [Variants](#23-variants-apis)
   - [Reviews](#24-reviews-apis)
   - [Wishlist](#25-wishlist-apis)
3. [Testing Workflow](#testing-workflow)
4. [Common Issues & Solutions](#common-issues--solutions)

---

## 1. Accounts APIs

### 1.1 User Registration
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

### 1.2 User Login
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/accounts/login/`  
**Headers:** 
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "demo_user1",
    "password": "DemoPass123!"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Login successful",
    "user": {...},
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.3 Get User Profile (Authenticated)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/accounts/profile/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 1.4 Update User Profile (Authenticated)
**Method:** `PATCH`  
**URL:** `http://127.0.0.1:8000/api/accounts/profile/update/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "first_name": "Johnny",
    "last_name": "Smith",
    "email": "johnny.smith@example.com"
}
```

### 1.5 User Logout (Authenticated)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/accounts/logout/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 1.6 List All Users (Admin Only)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/accounts/users/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

---

## 2. GalleryItem APIs

### 2.1 Categories APIs

#### List All Categories (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/categories/`  
**Headers:** 
```
Content-Type: application/json
```

**Expected Response (200 OK):**
```json
[
    {
        "id": 1,
        "title": "Imported Products",
        "description": "Products imported from JSON",
        "image": null,
        "parent": null,
        "children": []
    }
]
```
**Note:** Returns array directly (no pagination)

#### Get Category Detail (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/categories/<id>/`

---

### 2.2 Gallery Items APIs

#### List All Gallery Items (Public - No Token Required!)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/`  
**Headers:** 
```
Content-Type: application/json
```

**Query Parameters:**
- `category` (optional): Filter by category ID (e.g., `?category=1`)
- `search` (optional): Search in title, description, keywords (e.g., `?search=laptop`)
- `ordering` (optional): Order by: `timeStamp`, `updated`, `total_views`, `title` (e.g., `?ordering=-timeStamp`)

**Expected Response (200 OK):**
```json
[
    {
        "id": 1,
        "title": "German Shepherd Statue or Sculpture...",
        "slug": "german-shepherd-statue-or-sculpture",
        "description": "...",
        "category": 1,
        "category_title": "Imported Products",
        "default_variant_price": "44.99",
        "default_variant_image": "/media/products/images/small/product_1_img_0.jpg",
        "active": true,
        "total_views": 0,
        "average_rating": 4.75,
        "review_count": 4,
        "timeStamp": "2024-01-15T10:30:00Z",
        "updated": "2024-01-20T15:45:00Z"
    },
    ...
]
```
**Note:** 
- ✅ Returns array directly (no pagination wrapper)
- ✅ No token needed - public API
- ✅ Should return all 91 products

#### Get Gallery Item Detail by ID (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/<id>/`  
**Headers:** 
```
Content-Type: application/json
```

**Expected Response (200 OK):**
```json
{
    "id": 1,
    "category": {...},
    "title": "Full Product Title",
    "slug": "product-slug",
    "description": "Full description...",
    "default_variant": {...},
    "variants": [...],
    "reviews": [...],
    "average_rating": 4.75,
    "review_count": 4,
    "total_views": 1
}
```
**Note:** `total_views` increments automatically on each GET request

#### Get Gallery Item by Slug (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/slug/<slug>/`  
**Example:** `http://127.0.0.1:8000/api/gallery/items/slug/german-shepherd-statue-or-sculpture/`

#### Create Gallery Item (Admin Only)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "category": 1,
    "title": "New Product",
    "description": "Product description here",
    "active": true,
    "metaKeyWords": "keyword1, keyword2, keyword3",
    "metaKeyDescription": "Meta description for SEO"
}
```

#### Update Gallery Item (Admin Only)
**Method:** `PUT` or `PATCH`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/<id>/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Delete Gallery Item (Admin Only)
**Method:** `DELETE`  
**URL:** `http://127.0.0.1:8000/api/gallery/items/<id>/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
```

---

### 2.3 Variants APIs

#### List Variants (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/variants/?product=1`  
**Headers:** 
```
Content-Type: application/json
```

**Query Parameters:**
- `product` (required): Filter by product ID
- `is_best_seller` (optional): Filter best sellers (e.g., `?is_best_seller=true`)
- `ordering` (optional): Order by field

**Expected Response:** Array of variants (no pagination)

#### Get Variant Detail (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/variants/<id>/`

#### Create Variant (Admin Only)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/gallery/variants/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "product": 1,
    "title": "32GB RAM, 1TB SSD",
    "price": "1299.99",
    "quantity": 25,
    "is_best_seller": false,
    "active": true
}
```

#### Update Variant (Admin Only)
**Method:** `PUT` or `PATCH`  
**URL:** `http://127.0.0.1:8000/api/gallery/variants/<id>/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Delete Variant (Admin Only)
**Method:** `DELETE`  
**URL:** `http://127.0.0.1:8000/api/gallery/variants/<id>/`  
**Headers:** 
```
Authorization: Bearer <admin_access_token>
```

---

### 2.4 Reviews APIs

#### List Reviews (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/reviews/?product=1`  
**Headers:** 
```
Content-Type: application/json
```

**Query Parameters:**
- `product` (required): Filter by product ID
- `rating` (optional): Filter by rating 1-5
- `featured` (optional): Filter featured reviews
- `ordering` (optional): Order by field

**Expected Response:** Array of reviews (no pagination)

#### Get Review Detail (Public)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/reviews/<id>/`

#### Create Review (Authenticated)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/gallery/reviews/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "product": 1,
    "content": "This is an amazing product!",
    "rating": 5,
    "keep_anonymous": false
}
```

#### Update Review (Owner or Admin)
**Method:** `PUT` or `PATCH`  
**URL:** `http://127.0.0.1:8000/api/gallery/reviews/<id>/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Delete Review (Owner or Admin)
**Method:** `DELETE`  
**URL:** `http://127.0.0.1:8000/api/gallery/reviews/<id>/`  
**Headers:** 
```
Authorization: Bearer <access_token>
```

---

### 2.5 Wishlist APIs

#### Get User's Wishlist (Authenticated)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/wishlist/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Expected Response:** Array of wishlist items (no pagination)

#### Add to Wishlist (Authenticated)
**Method:** `POST`  
**URL:** `http://127.0.0.1:8000/api/gallery/wishlist/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "product_id": 1
}
```

#### Get Wishlist Item Detail (Authenticated)
**Method:** `GET`  
**URL:** `http://127.0.0.1:8000/api/gallery/wishlist/<id>/`  
**Headers:** 
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Remove from Wishlist (Authenticated)
**Method:** `DELETE`  
**URL:** `http://127.0.0.1:8000/api/gallery/wishlist/<id>/`  
**Headers:** 
```
Authorization: Bearer <access_token>
```

---

## Testing Workflow

### Step 1: Setup Authentication
1. Register/Login using Accounts APIs to get `access_token`
2. Save token in Postman environment variable: `access_token`
3. For admin APIs, create admin user via Django admin and get admin token

### Step 2: Test Public APIs (No Token Needed)
1. Test Categories APIs
2. Test Gallery Items List API (`GET /api/gallery/items/`)
3. Test Gallery Item Detail API
4. Test Variants List API
5. Test Reviews List API

### Step 3: Test Authenticated APIs
1. Add `Authorization: Bearer {{access_token}}` header
2. Test Create Review API
3. Test Wishlist APIs (GET, POST, DELETE)

### Step 4: Test Admin APIs
1. Use admin user's token
2. Test Create/Update/Delete Gallery Item
3. Test Create/Update/Delete Variant

---

## Postman Collection Variables

Create these variables in Postman:
- `base_url`: `http://127.0.0.1:8000`
- `access_token`: (will be set after login)
- `admin_token`: (admin user's token)

Then use in URLs: `{{base_url}}/api/gallery/items/`

---

## Common Issues & Solutions

1. **401 Unauthorized**: 
   - Check if token is valid and not expired (30 days validity)
   - Ensure `Authorization: Bearer <token>` header is set correctly

2. **403 Forbidden**: 
   - User doesn't have admin permissions (for admin-only APIs)
   - User trying to update/delete someone else's review

3. **400 Bad Request**: 
   - Check request body format and required fields
   - Ensure `product` parameter is provided for variants/reviews list
   - Check data types (e.g., `rating` must be 1-5 integer)

4. **404 Not Found**: 
   - Check if ID exists in database
   - Verify URL path is correct

5. **Pagination**: 
   - ✅ Pagination removed - all list APIs return arrays directly
   - No `count`, `next`, `previous`, `results` wrapper
   - Just plain array: `[{...}, {...}]`

6. **View Count**: 
   - Gallery Item detail view increments `total_views` on each GET request
   - This happens automatically

---

## Swagger UI Testing

You can also test APIs directly in Swagger UI:
- URL: `http://127.0.0.1:8000/swagger/`
- Click "Authorize" button
- Enter: `Bearer <your_access_token>`
- Test APIs directly from browser
- All APIs are organized under tags:
  - Accounts
  - Gallery Items
  - Variants
  - Categories
  - Reviews
  - Wishlist

---

## API Endpoints Summary

### Public APIs (No Auth Required)
- `GET /api/gallery/categories/` - List categories
- `GET /api/gallery/categories/<id>/` - Get category
- `GET /api/gallery/items/` - List gallery items
- `GET /api/gallery/items/<id>/` - Get gallery item
- `GET /api/gallery/items/slug/<slug>/` - Get gallery item by slug
- `GET /api/gallery/variants/?product=<id>` - List variants
- `GET /api/gallery/variants/<id>/` - Get variant
- `GET /api/gallery/reviews/?product=<id>` - List reviews
- `GET /api/gallery/reviews/<id>/` - Get review

### Authenticated APIs (User Token Required)
- `POST /api/gallery/reviews/` - Create review
- `PUT/PATCH /api/gallery/reviews/<id>/` - Update own review
- `DELETE /api/gallery/reviews/<id>/` - Delete own review
- `GET /api/gallery/wishlist/` - Get wishlist
- `POST /api/gallery/wishlist/` - Add to wishlist
- `GET /api/gallery/wishlist/<id>/` - Get wishlist item
- `DELETE /api/gallery/wishlist/<id>/` - Remove from wishlist

### Admin APIs (Admin Token Required)
- `POST /api/gallery/items/` - Create gallery item
- `PUT/PATCH /api/gallery/items/<id>/` - Update gallery item
- `DELETE /api/gallery/items/<id>/` - Delete gallery item
- `POST /api/gallery/variants/` - Create variant
- `PUT/PATCH /api/gallery/variants/<id>/` - Update variant
- `DELETE /api/gallery/variants/<id>/` - Delete variant

---

**Happy Testing!** 🚀

