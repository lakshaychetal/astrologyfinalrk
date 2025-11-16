# 🚀 Quick Setup Guide

## Step-by-Step Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example env file
copy .env.example .env

# Edit .env if needed (MongoDB URI is already configured)
```

### 3. Create Admin User
```bash
python create_admin.py
```

**Output:**
```
✅ Admin user created: admin@astrology.ai / admin123
```

### 4. Start the API Server
```bash
python api.py
```

**Output:**
```
✅ AI components initialized
 * Running on http://0.0.0.0:5000
```

### 5. Test the API
Open a new terminal and run:
```bash
python test_api.py
```

---

## Quick Test with cURL

### 1. Login as Admin
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"admin@astrology.ai\", \"password\": \"admin123\"}"
```

**Save the token from response!**

### 2. Create a Regular User
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"user@test.com\", \"password\": \"user123\", \"name\": \"Test User\"}"
```

### 3. Ask AI a Question
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"How will my spouse look?\",
    \"chart_data\": \"RASHI CHART (D1):\\nAscendant: Cancer\\n7th House: Venus in Capricorn\",
    \"niche\": \"Love & Relationships\"
  }"
```

---

## Common Issues

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" to MongoDB
**Solution:** MongoDB URI is already configured. Check your internet connection.

### Issue: "AI not initialized"
**Solution:** Make sure you have valid GCP credentials and API keys in `.env`

---

## What's Next?

1. Read `API_README.md` for complete API documentation
2. Test all endpoints using the cURL examples
3. Build your frontend application
4. Deploy to production

---

## Admin Panel Features

As admin, you can:
- ✅ View all users
- ✅ Create new users
- ✅ Update user details (including passwords)
- ✅ Delete users
- ✅ See user passwords (hashed)
- ✅ Enable/disable user accounts

---

## User Features

Regular users can:
- ✅ Signup and login
- ✅ Chat with AI astrologer
- ✅ View their chat history
- ✅ Get personalized astrology readings

---

## Security Notes

1. **Change JWT_SECRET in production!**
2. **Change admin password after first login**
3. **Use HTTPS in production**
4. **Configure CORS properly for your domain**

---

## Support

For complete API documentation with all cURL examples, see:
- `API_README.md` - Complete API reference
- `README.md` - Project overview

**MongoDB Database:** `astrology_ai`
**Collections:** `users`, `chats`
