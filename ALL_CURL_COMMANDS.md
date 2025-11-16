# 📋 All cURL Commands - Copy & Paste Ready

## Base URL
```
http://localhost:5000
```

---

## 🔐 Authentication

### 1. Signup (Create New User)
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }'
```

### 2. Login (Regular User)
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 3. Login (Admin)
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@astrology.ai",
    "password": "admin123"
  }'
```

### 4. Get Current User Profile
```bash
curl -X GET http://localhost:5000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 👨‍💼 Admin - User Management

### 5. Get All Users
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 6. Get Single User (with password hash)
```bash
curl -X GET http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 7. Create User (Admin)
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "name": "Jane Smith",
    "is_admin": false,
    "active": true
  }'
```

### 8. Update User (Change Name)
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name"
  }'
```

### 9. Update User Password
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newpassword123"
  }'
```

### 10. Update User Email
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }'
```

### 11. Make User Admin
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_admin": true
  }'
```

### 12. Disable User Account
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "active": false
  }'
```

### 13. Enable User Account
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "active": true
  }'
```

### 14. Update Multiple Fields
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Name",
    "email": "newemail@example.com",
    "password": "newpass123",
    "is_admin": true,
    "active": true
  }'
```

### 15. Delete User
```bash
curl -X DELETE http://localhost:5000/api/admin/users/USER_ID_HERE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## 🤖 AI Chat

### 16. Ask Astrology Question (Love & Relationships)
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will my spouse look?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn\n11th House: Saturn (Retrograde)\n\nNAVAMSA (D9):\n7th House: Saturn\nAscendant: Cancer\n\nCurrent Dasha: Venus-Saturn",
    "niche": "Love & Relationships"
  }'
```

### 17. Ask Career Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is my career path?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n10th House: Mars in Aries\n\nDASHAMAMSA (D10):\n10th Lord: Mars\n\nCurrent Dasha: Mars-Jupiter",
    "niche": "Career & Professional"
  }'
```

### 18. Ask Wealth Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "When will I get financial success?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n2nd House: Jupiter in Leo\n11th House: Venus in Taurus\n\nCurrent Dasha: Jupiter-Venus",
    "niche": "Wealth & Finance"
  }'
```

### 19. Ask Health Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Any health concerns I should be aware of?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n6th House: Saturn in Sagittarius\n8th House: Mars in Aquarius\n\nCurrent Dasha: Saturn-Mars",
    "niche": "Health & Wellness"
  }'
```

### 20. Ask Spiritual Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is my spiritual path?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n9th House: Jupiter in Pisces\n12th House: Ketu in Gemini\n\nCurrent Dasha: Jupiter-Ketu",
    "niche": "Spiritual Growth"
  }'
```

### 21. Get Chat History
```bash
curl -X GET http://localhost:5000/api/chat/history \
  -H "Authorization: Bearer YOUR_USER_TOKEN"
```

---

## 🏥 Health Check

### 22. API Health Check
```bash
curl -X GET http://localhost:5000/health
```

---

## 🔄 Complete User Flow Example

### Step 1: Create Account
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "test123",
    "name": "Test User"
  }'
```

**Save the token from response!**

### Step 2: Get Profile
```bash
curl -X GET http://localhost:5000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP1"
```

### Step 3: Ask AI Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP1" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will my spouse look?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn",
    "niche": "Love & Relationships"
  }'
```

### Step 4: Get Chat History
```bash
curl -X GET http://localhost:5000/api/chat/history \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP1"
```

---

## 🔄 Complete Admin Flow Example

### Step 1: Login as Admin
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@astrology.ai",
    "password": "admin123"
  }'
```

**Save the admin token!**

### Step 2: Get All Users
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Copy a user ID from the response!**

### Step 3: Get User Details (with password)
```bash
curl -X GET http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Step 4: Update User Password
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newpassword123"
  }'
```

### Step 5: Create New User
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "pass123",
    "name": "New User",
    "is_admin": false,
    "active": true
  }'
```

### Step 6: Delete User
```bash
curl -X DELETE http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## 💡 Tips

### Save Token as Variable (Linux/Mac)
```bash
TOKEN=$(curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@astrology.ai","password":"admin123"}' \
  | jq -r '.token')

# Use it
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

### Save Token as Variable (Windows PowerShell)
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"email":"admin@astrology.ai","password":"admin123"}'

$TOKEN = $response.token

# Use it
Invoke-RestMethod -Uri "http://localhost:5000/api/admin/users" `
  -Headers @{"Authorization"="Bearer $TOKEN"}
```

### Pretty Print JSON (with jq)
```bash
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 📊 Response Examples

### Successful Login
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

### Get All Users
```json
[
  {
    "id": "65f1234567890abcdef12345",
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false,
    "active": true,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### AI Chat Response
```json
{
  "response": "Based on your chart analysis...\n\n**Physical Appearance:**\n- Venus in Capricorn suggests...",
  "complexity": "medium",
  "passages_used": 8
}
```

### Error Response
```json
{
  "error": "Invalid credentials"
}
```

---

## 🔑 Default Credentials

```
Admin Email: admin@astrology.ai
Admin Password: admin123
```

---

## 📝 Notes

- Replace `YOUR_TOKEN_HERE` with actual token from login response
- Replace `YOUR_ADMIN_TOKEN` with admin token from admin login
- Replace `USER_ID_HERE` with actual user ID from get users response
- All requests return JSON
- Token expires after 24 hours

---

**API Base URL:** `http://localhost:5000`

**MongoDB:** `mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/`

**Database:** `astrology_ai`
