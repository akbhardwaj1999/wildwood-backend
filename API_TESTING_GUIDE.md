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

## 🛒 Cart APIs

Cart APIs allow users to manage their shopping cart, addresses, orders, and coupons.

### Important Notes:
- **Session-based Cart**: Cart operations use session-based cart, so no authentication is required for basic cart operations (add, update, remove items)
- **Address & Orders**: Address management and order history require authentication
- **Cart Persistence**: Cart is stored in session, so same browser/session maintains cart across requests

---

### 1. Cart Operations

#### 1.1 Get Current Cart
**GET** `/api/cart/cart/`

**Description**: Get current user's cart with all items, pricing, and totals.

**Authentication**: Not required (uses session)

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/cart/
Content-Type: application/json
```

**Response** (200 OK):
```json
{
  "id": 1,
  "reference_number": "2025-11-27-12345678",
  "items": [
    {
      "id": 1,
      "variant": {
        "id": 1,
        "title": "32GB RAM, 1TB SSD",
        "price": "1299.99",
        "image": "/products/images/small/product_1_img_0.jpg"
      },
      "quantity": 2,
      "item_price": "1299.99",
      "total_item_price": "2599.98",
      "product_title": "Premium Gaming Laptop",
      "variant_title": "32GB RAM, 1TB SSD"
    }
  ],
  "subtotal": "2599.98",
  "coupon_discount_amount": "0.00",
  "total": "2599.98",
  "total_shipping_cost": "0.00",
  "tax_amount": "0.00",
  "ordered": false,
  "status": "N"
}
```

---

#### 1.2 Add Item to Cart
**POST** `/api/cart/cart/add-item/`

**Description**: Add item to cart. If item already exists, increases quantity.

**Authentication**: Not required (uses session)

**Request**:
```http
POST http://127.0.0.1:8000/api/cart/cart/add-item/
Content-Type: application/json

{
  "variant_id": 1,
  "quantity": 2
}
```

**Response** (200 OK):
```json
{
  "message": "Item added to cart successfully",
  "cart": {
    "id": 1,
    "items": [...],
    "subtotal": "2599.98",
    "total": "2599.98"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "variant_id": ["This variant is out of stock"]
}
```

---

#### 1.3 Update Cart Item Quantity
**PUT** `/api/cart/cart/update-item/<item_id>/`

**Description**: Update cart item quantity.

**Authentication**: Not required (uses session)

**Request**:
```http
PUT http://127.0.0.1:8000/api/cart/cart/update-item/1/
Content-Type: application/json

{
  "quantity": 5
}
```

**Response** (200 OK):
```json
{
  "message": "Cart item updated successfully",
  "cart": {
    "id": 1,
    "items": [...],
    "subtotal": "6499.95",
    "total": "6499.95"
  }
}
```

---

#### 1.4 Remove Item from Cart
**DELETE** `/api/cart/cart/remove-item/<item_id>/`

**Description**: Remove item from cart.

**Authentication**: Not required (uses session)

**Request**:
```http
DELETE http://127.0.0.1:8000/api/cart/cart/remove-item/1/
```

**Response** (200 OK):
```json
{
  "message": "Item removed from cart successfully",
  "cart": {
    "id": 1,
    "items": [],
    "subtotal": "0.00",
    "total": "0.00"
  }
}
```

---

#### 1.5 Clear Entire Cart
**DELETE** `/api/cart/cart/clear/`

**Description**: Clear entire cart (remove all items).

**Authentication**: Not required (uses session)

**Request**:
```http
DELETE http://127.0.0.1:8000/api/cart/cart/clear/
```

**Response** (200 OK):
```json
{
  "message": "Cart cleared successfully"
}
```

---

### 2. Address Management

#### 2.1 List User Addresses
**GET** `/api/cart/addresses/`

**Description**: List all addresses for authenticated user.

**Authentication**: Required

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/addresses/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email_address": "john.doe@example.com",
    "phone_number": "1234567890",
    "address_line_1": "123 Main Street",
    "address_line_2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "country": "United States",
    "zip_code": "10001",
    "address_type": "S",
    "address_type_display": "Shipping",
    "default": false
  }
]
```

---

#### 2.2 Create Address
**POST** `/api/cart/addresses/`

**Description**: Create new address.

**Authentication**: Required

**Request**:
```http
POST http://127.0.0.1:8000/api/cart/addresses/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email_address": "john.doe@example.com",
  "phone_number": "1234567890",
  "address_line_1": "123 Main Street",
  "address_line_2": "Apt 4B",
  "city": "New York",
  "state": "NY",
  "country": "United States",
  "zip_code": "10001",
  "address_type": "S",
  "default": false
}
```

**Note**: `address_type` - "S" for Shipping, "B" for Billing

**Response** (201 Created):
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  ...
}
```

---

#### 2.3 Get Address Detail
**GET** `/api/cart/addresses/<id>/`

**Description**: Get address details.

**Authentication**: Required (can only access own addresses)

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/addresses/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response** (200 OK): Address object

---

#### 2.4 Update Address
**PUT/PATCH** `/api/cart/addresses/<id>/`

**Description**: Update address.

**Authentication**: Required

**Request**:
```http
PUT http://127.0.0.1:8000/api/cart/addresses/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  ...
}
```

**Response** (200 OK): Updated address object

---

#### 2.5 Delete Address
**DELETE** `/api/cart/addresses/<id>/`

**Description**: Delete address.

**Authentication**: Required

**Request**:
```http
DELETE http://127.0.0.1:8000/api/cart/addresses/1/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response** (204 No Content)

---

### 3. Order Management

#### 3.1 List User Orders
**GET** `/api/cart/orders/`

**Description**: List all finalized orders for authenticated user.

**Authentication**: Required

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/orders/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "reference_number": "2025-11-27-12345678",
    "ordered_date": "2025-11-27T10:30:00Z",
    "status": "O",
    "status_display": "Not shipped yet",
    "items": [...],
    "subtotal": "2599.98",
    "total": "2599.98",
    "ordered": true
  }
]
```

---

#### 3.2 Get Order Details
**GET** `/api/cart/orders/<reference_number>/`

**Description**: Get order details by reference number.

**Authentication**: Not required (public access by reference number)

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/orders/2025-11-27-12345678/
Content-Type: application/json
```

**Response** (200 OK): Complete order object with items, addresses, etc.

---

### 4. Coupon Operations

#### 4.1 Apply Coupon
**POST** `/api/cart/coupons/apply/`

**Description**: Apply coupon to cart.

**Authentication**: Not required (uses session)

**Request**:
```http
POST http://127.0.0.1:8000/api/cart/coupons/apply/
Content-Type: application/json

{
  "code": "SAVE10"
}
```

**Response** (200 OK):
```json
{
  "message": "Coupon applied successfully",
  "coupon_discount_amount": "259.99",
  "cart": {
    "id": 1,
    "coupon": 1,
    "subtotal": "2599.98",
    "total": "2339.99",
    ...
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Coupon code is invalid."
}
```

---

#### 4.2 Remove Coupon
**DELETE** `/api/cart/coupons/remove/`

**Description**: Remove coupon from cart.

**Authentication**: Not required (uses session)

**Request**:
```http
DELETE http://127.0.0.1:8000/api/cart/coupons/remove/
```

**Response** (200 OK):
```json
{
  "message": "Coupon removed successfully",
  "cart": {
    "id": 1,
    "coupon": null,
    "subtotal": "2599.98",
    "total": "2599.98",
    ...
  }
}
```

---

### 5. Admin Coupon Management

#### 5.1 List All Coupons (Admin)
**GET** `/api/cart/admin/coupons/`

**Description**: List all coupons (Admin only).

**Authentication**: Required (Admin)

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/admin/coupons/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json
```

**Response** (200 OK): Array of coupon objects

---

#### 5.2 Create Coupon (Admin)
**POST** `/api/cart/admin/coupons/`

**Description**: Create new coupon (Admin only).

**Authentication**: Required (Admin)

**Request**:
```http
POST http://127.0.0.1:8000/api/cart/admin/coupons/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "title": "10% Off Coupon",
  "description": "Get 10% off on orders above $100",
  "code": "SAVE10",
  "discount": "10.00",
  "discount_type": "percentage",
  "minimum_order_amount": "100.00",
  "single_use_per_user": false,
  "active": true
}
```

**Note**: `discount_type` - "fixed_amount" or "percentage"

**Response** (201 Created): Coupon object

---

#### 5.3 Get Coupon Detail (Admin)
**GET** `/api/cart/admin/coupons/<id>/`

**Description**: Get coupon details (Admin only).

**Authentication**: Required (Admin)

**Request**:
```http
GET http://127.0.0.1:8000/api/cart/admin/coupons/1/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

**Response** (200 OK): Coupon object

---

#### 5.4 Update Coupon (Admin)
**PUT/PATCH** `/api/cart/admin/coupons/<id>/`

**Description**: Update coupon (Admin only).

**Authentication**: Required (Admin)

**Request**:
```http
PUT http://127.0.0.1:8000/api/cart/admin/coupons/1/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "title": "Updated 10% Off Coupon",
  "code": "SAVE10",
  "discount": "15.00",
  "discount_type": "percentage",
  "minimum_order_amount": "100.00",
  "single_use_per_user": false,
  "active": true
}
```

**Response** (200 OK): Updated coupon object

---

#### 5.5 Delete Coupon (Admin)
**DELETE** `/api/cart/admin/coupons/<id>/`

**Description**: Delete coupon (Admin only).

**Authentication**: Required (Admin)

**Request**:
```http
DELETE http://127.0.0.1:8000/api/cart/admin/coupons/1/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

**Response** (204 No Content)

---

## 📝 Cart API Testing Workflow

### Complete Shopping Flow:

1. **Get Products** (Gallery APIs)
   - `GET /api/gallery/items/` - Browse products
   - `GET /api/gallery/variants/1/` - View variant details

2. **Add to Cart**
   - `POST /api/cart/cart/add-item/` - Add product to cart
   - `GET /api/cart/cart/` - View cart

3. **Manage Cart**
   - `PUT /api/cart/cart/update-item/<id>/` - Update quantities
   - `DELETE /api/cart/cart/remove-item/<id>/` - Remove items

4. **Apply Coupon** (Optional)
   - `POST /api/cart/coupons/apply/` - Apply discount code

5. **Add Address** (If authenticated)
   - `POST /api/cart/addresses/` - Add shipping address

6. **View Orders** (If authenticated)
   - `GET /api/cart/orders/` - View order history
   - `GET /api/cart/orders/<reference>/` - View order details

---

## 🔑 Cart API Key Points

1. **Session-based Cart**: Cart operations don't require authentication - cart is stored in session
2. **Address Management**: Requires authentication - users can only manage their own addresses
3. **Order History**: Requires authentication - users can only view their own orders
4. **Coupon Application**: No authentication required - uses session cart
5. **Admin Coupon Management**: Requires admin authentication
6. **Cart Persistence**: Cart persists across requests in the same browser session

---

**Happy Testing!** 🚀

