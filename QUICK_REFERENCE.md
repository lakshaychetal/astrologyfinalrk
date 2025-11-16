# 🚀 Quick Reference Card

## Start Server
```bash
# Windows
start_api.bat

# Or manually
python create_admin.py
python api.py
```

## Default Admin
```
Email: admin@astrology.ai
Password: admin123
```

## Base URL
```
http://localhost:5000
```

---

## Quick cURL Commands

### 1. Login as Admin
```bash
curl -X POST http://localhost:5000/api/login -H "Content-Type: application/json" -d "{\"email\":\"admin@astrology.ai\",\"password\":\"admin123\"}"
```

### 2. Create User
```bash
curl -X POST http://localhost:5000/api/signup -H "Content-Type: application/json" -d "{\"email\":\"user@test.com\",\"password\":\"pass123\",\"name\":\"Test User\"}"
```

### 3. Get All Users (Admin)
```bash
curl -X GET http://localhost:5000/api/admin/users -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Update User Password (Admin)
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID -H "Authorization: Bearer ADMIN_TOKEN" -H "Content-Type: application/json" -d "{\"password\":\"newpass123\"}"
```

### 5. Chat with AI
```bash
curl -X POST http://localhost:5000/api/chat -H "Authorization: Bearer USER_TOKEN" -H "Content-Type: application/json" -d "{\"question\":\"How will my spouse look?\",\"chart_data\":\"RASHI CHART (D1):\\nAscendant: Cancer\\n7th House: Venus in Capricorn\",\"niche\":\"Love & Relationships\"}"
```

### 6. Get Chat History
```bash
curl -X GET http://localhost:5000/api/chat/history -H "Authorization: Bearer USER_TOKEN"
```

---

## Endpoints Cheat Sheet

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/signup | None | Create user |
| POST | /api/login | None | Login |
| GET | /api/me | User | Get profile |
| GET | /api/admin/users | Admin | List users |
| GET | /api/admin/users/:id | Admin | Get user + password |
| POST | /api/admin/users | Admin | Create user |
| PUT | /api/admin/users/:id | Admin | Update user |
| DELETE | /api/admin/users/:id | Admin | Delete user |
| POST | /api/chat | User | Ask AI |
| GET | /api/chat/history | User | Get history |
| GET | /health | None | Health check |

---

## Response Codes

- **200** - Success
- **201** - Created
- **400** - Bad request
- **401** - Unauthorized (invalid/missing token)
- **403** - Forbidden (not admin)
- **404** - Not found
- **500** - Server error

---

## Token Usage

```bash
# Save token after login
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use in requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/me
```

---

## MongoDB

**URI:** `mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/`

**Database:** `astrology_ai`

**Collections:**
- `users` - User accounts
- `chats` - Chat history

---

## Files to Read

1. **API_README.md** - Complete API docs
2. **SETUP_GUIDE.md** - Setup instructions
3. **IMPLEMENTATION_SUMMARY.md** - What was built
4. **README.md** - Project overview

---

## Testing

```bash
# Automated test
python test_api.py

# Or import Postman collection
Astrology_AI_API.postman_collection.json
```

---

## Admin Powers

✅ View all users
✅ See passwords (hashed)
✅ Create users
✅ Update passwords
✅ Delete users
✅ Enable/disable accounts

---

## Niches

- Love & Relationships
- Career & Professional
- Wealth & Finance
- Health & Wellness
- Spiritual Growth

---

## Need Help?

- **Full API docs:** API_README.md
- **Setup help:** SETUP_GUIDE.md
- **What was built:** IMPLEMENTATION_SUMMARY.md
