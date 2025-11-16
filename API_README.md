# 🔐 Astrology AI - API Documentation

Complete API documentation with authentication, admin CRUD, and AI chat endpoints.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Admin User
```bash
python create_admin.py
```

### 3. Start API Server
```bash
python api.py
```

Server runs on: `http://localhost:5000`

---

## 📋 API Endpoints

### Base URL
```
http://localhost:5000/api
```

---

## 🔑 Authentication Endpoints

### 1. User Signup
**POST** `/api/signup`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }'
```

**Response (201):**
```json
{
  "message": "User created",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "65f1234567890abcdef12345",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

---

### 2. User Login
**POST** `/api/login`

Login with existing credentials.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Response (200):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "65f1234567890abcdef12345",
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}
```

---

### 3. Get Current User Profile
**GET** `/api/me`

Get logged-in user's profile.

**Headers:**
```
Authorization: Bearer <token>
```

**cURL:**
```bash
curl -X GET http://localhost:5000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response (200):**
```json
{
  "id": "65f1234567890abcdef12345",
  "email": "user@example.com",
  "name": "John Doe",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00"
}
```

---

## 👨‍💼 Admin Endpoints (Admin Only)

### 4. Get All Users
**GET** `/api/admin/users`

Get list of all users (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**cURL:**
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE"
```

**Response (200):**
```json
[
  {
    "id": "65f1234567890abcdef12345",
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false,
    "active": true,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": "65f1234567890abcdef12346",
    "email": "admin@astrology.ai",
    "name": "Admin",
    "is_admin": true,
    "active": true,
    "created_at": "2024-01-10T08:00:00"
  }
]
```

---

### 5. Get Single User
**GET** `/api/admin/users/<user_id>`

Get specific user details including password hash (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**cURL:**
```bash
curl -X GET http://localhost:5000/api/admin/users/65f1234567890abcdef12345 \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE"
```

**Response (200):**
```json
{
  "id": "65f1234567890abcdef12345",
  "email": "user@example.com",
  "name": "John Doe",
  "password": "$2b$12$abcdefghijklmnopqrstuvwxyz...",
  "is_admin": false,
  "active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 6. Create User (Admin)
**POST** `/api/admin/users`

Create a new user (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "name": "Jane Smith",
  "is_admin": false,
  "active": true
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "name": "Jane Smith",
    "is_admin": false,
    "active": true
  }'
```

**Response (201):**
```json
{
  "message": "User created",
  "id": "65f1234567890abcdef12347"
}
```

---

### 7. Update User
**PUT** `/api/admin/users/<user_id>`

Update user details (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body (all fields optional):**
```json
{
  "name": "John Updated",
  "email": "newemail@example.com",
  "password": "newpassword123",
  "is_admin": true,
  "active": false
}
```

**cURL:**
```bash
curl -X PUT http://localhost:5000/api/admin/users/65f1234567890abcdef12345 \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Updated",
    "password": "newpassword123"
  }'
```

**Response (200):**
```json
{
  "message": "User updated"
}
```

---

### 8. Delete User
**DELETE** `/api/admin/users/<user_id>`

Delete a user and all their chat history (admin only).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**cURL:**
```bash
curl -X DELETE http://localhost:5000/api/admin/users/65f1234567890abcdef12345 \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE"
```

**Response (200):**
```json
{
  "message": "User deleted"
}
```

---

## 🤖 AI Chat Endpoints (Authenticated Users)

### 9. Chat with AI
**POST** `/api/chat`

Ask astrology questions (authenticated users only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "question": "How will my spouse look?",
  "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn\n11th House: Saturn (Retrograde)\n\nNAVAMSA (D9):\n7th House: Saturn\nAscendant: Cancer\n\nCurrent Dasha: Venus-Saturn",
  "niche": "Love & Relationships"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will my spouse look?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn\n11th House: Saturn (Retrograde)\n\nNAVAMSA (D9):\n7th House: Saturn\nAscendant: Cancer\n\nCurrent Dasha: Venus-Saturn",
    "niche": "Love & Relationships"
  }'
```

**Response (200):**
```json
{
  "response": "Based on your chart analysis...\n\n**Physical Appearance:**\n- Venus in Capricorn in 7th house indicates...\n- Saturn's influence suggests...\n\n**Personality Traits:**\n- Mature and responsible nature...\n- Professional and ambitious...",
  "complexity": "medium",
  "passages_used": 8
}
```

---

### 10. Get Chat History
**GET** `/api/chat/history`

Get user's chat history (last 50 conversations).

**Headers:**
```
Authorization: Bearer <token>
```

**cURL:**
```bash
curl -X GET http://localhost:5000/api/chat/history \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response (200):**
```json
[
  {
    "id": "65f1234567890abcdef12348",
    "question": "How will my spouse look?",
    "response": "Based on your chart analysis...",
    "niche": "Love & Relationships",
    "timestamp": "2024-01-15T14:30:00"
  },
  {
    "id": "65f1234567890abcdef12349",
    "question": "What about career?",
    "response": "Your career analysis shows...",
    "niche": "Career & Professional",
    "timestamp": "2024-01-15T14:25:00"
  }
]
```

---

## 🏥 Health Check

### 11. Health Check
**GET** `/health`

Check if API is running.

**cURL:**
```bash
curl -X GET http://localhost:5000/health
```

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## 🔒 Authentication Flow

### Step 1: Login/Signup
```bash
# Signup
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123", "name": "John"}'

# Response includes token
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Step 2: Use Token in Requests
```bash
# Save token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use in requests
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "chart_data": "..."}'
```

---

## 👨‍💼 Admin Access

### Default Admin Credentials
```
Email: admin@astrology.ai
Password: admin123
```

### Login as Admin
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@astrology.ai",
    "password": "admin123"
  }'
```

### Use Admin Token
```bash
ADMIN_TOKEN="your_admin_token_here"

# Get all users
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Update user password
curl -X PUT http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "newpassword123"}'
```

---

## 📊 Available Niches

- `Love & Relationships`
- `Career & Professional`
- `Wealth & Finance`
- `Health & Wellness`
- `Spiritual Growth`

---

## ❌ Error Responses

### 400 Bad Request
```json
{
  "error": "Email and password required"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid token"
}
```

### 403 Forbidden
```json
{
  "error": "Admin access required"
}
```

### 404 Not Found
```json
{
  "error": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error message"
}
```

---

## 🔐 Security Notes

1. **JWT Token Expiry:** 24 hours
2. **Password Hashing:** bcrypt with salt
3. **CORS:** Enabled for all origins (configure for production)
4. **MongoDB:** Connection string in `database.py`
5. **Secret Key:** Change `JWT_SECRET` in production

---

## 🗄️ Database Collections

### users
```json
{
  "_id": ObjectId,
  "email": "string",
  "password": "hashed_string",
  "name": "string",
  "is_admin": boolean,
  "active": boolean,
  "created_at": datetime
}
```

### chats
```json
{
  "_id": ObjectId,
  "user_id": "string",
  "question": "string",
  "chart_data": "string",
  "niche": "string",
  "response": "string",
  "timestamp": datetime
}
```

---

## 🧪 Testing Examples

### Complete User Flow
```bash
# 1. Signup
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test123", "name": "Test User"}'

# Save the token from response
TOKEN="your_token_here"

# 2. Get profile
curl -X GET http://localhost:5000/api/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Ask AI question
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will my spouse look?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn",
    "niche": "Love & Relationships"
  }'

# 4. Get chat history
curl -X GET http://localhost:5000/api/chat/history \
  -H "Authorization: Bearer $TOKEN"
```

### Complete Admin Flow
```bash
# 1. Login as admin
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@astrology.ai", "password": "admin123"}'

# Save admin token
ADMIN_TOKEN="your_admin_token_here"

# 2. Get all users
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Create new user
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "new@test.com", "password": "pass123", "name": "New User"}'

# 4. Update user
curl -X PUT http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "password": "newpass123"}'

# 5. Delete user
curl -X DELETE http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🚀 Production Deployment

### Environment Variables
```bash
export JWT_SECRET="your-secret-key-here"
export OPENROUTER_API_KEY="your-openrouter-key"
export GCP_PROJECT_ID="your-gcp-project"
export RAG_CORPUS_ID="your-corpus-id"
```

### Run Production Server
```bash
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

---

## 📞 Support

For issues or questions, contact the development team.

**MongoDB Connection:** `mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/`

**Database:** `astrology_ai`

**Collections:** `users`, `chats`
