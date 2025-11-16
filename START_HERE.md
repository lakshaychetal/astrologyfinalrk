# 🌟 START HERE - Astrology AI with Authentication

Welcome! This guide will get you up and running in 5 minutes.

---

## 📋 What You Have

✅ **Complete REST API** with authentication
✅ **User signup/login** system
✅ **Admin panel** with full CRUD operations
✅ **AI-powered astrology chat** (authenticated)
✅ **MongoDB database** integration
✅ **Complete documentation** with cURL examples

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Admin User
```bash
python create_admin.py
```

### Step 3: Start API Server
```bash
# Windows
start_api.bat

# Or manually
python api.py
```

**✅ Done! API is running on http://localhost:5000**

---

## 🧪 Test It (30 seconds)

### Test 1: Login as Admin
```bash
curl -X POST http://localhost:5000/api/login -H "Content-Type: application/json" -d "{\"email\":\"admin@astrology.ai\",\"password\":\"admin123\"}"
```

**Copy the token from response!**

### Test 2: Get All Users
```bash
curl -X GET http://localhost:5000/api/admin/users -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test 3: Create a User
```bash
curl -X POST http://localhost:5000/api/signup -H "Content-Type: application/json" -d "{\"email\":\"test@test.com\",\"password\":\"test123\",\"name\":\"Test User\"}"
```

---

## 📚 Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| **QUICK_REFERENCE.md** | Quick commands & cheat sheet | Read first! |
| **API_README.md** | Complete API documentation | For all endpoints |
| **SETUP_GUIDE.md** | Detailed setup instructions | If you have issues |
| **IMPLEMENTATION_SUMMARY.md** | What was built | To understand features |
| **ARCHITECTURE.md** | System architecture | For technical details |
| **README.md** | Project overview | For general info |

---

## 🎯 What Can You Do?

### As Admin (admin@astrology.ai / admin123)
- ✅ View all users
- ✅ Create new users
- ✅ Update user details
- ✅ Change user passwords
- ✅ Delete users
- ✅ Enable/disable accounts
- ✅ See password hashes

### As Regular User
- ✅ Sign up for account
- ✅ Login with credentials
- ✅ Chat with AI astrologer
- ✅ View chat history
- ✅ Get personalized readings

---

## 🔑 Default Credentials

```
Email: admin@astrology.ai
Password: admin123
```

**⚠️ Change this in production!**

---

## 📡 API Endpoints

### Public (No Auth)
```
POST /api/signup          - Create account
POST /api/login           - Login
GET  /health              - Health check
```

### User (Token Required)
```
GET  /api/me              - Get profile
POST /api/chat            - Ask AI question
GET  /api/chat/history    - Get chat history
```

### Admin (Admin Token Required)
```
GET    /api/admin/users           - List all users
GET    /api/admin/users/:id       - Get user (with password)
POST   /api/admin/users           - Create user
PUT    /api/admin/users/:id       - Update user
DELETE /api/admin/users/:id       - Delete user
```

---

## 🧪 Testing Options

### Option 1: Automated Test Script
```bash
python test_api.py
```

### Option 2: Postman
1. Import `Astrology_AI_API.postman_collection.json`
2. Set base_url to `http://localhost:5000`
3. Run requests

### Option 3: cURL
See **QUICK_REFERENCE.md** for all commands

---

## 💡 Common Tasks

### Create a New User (as admin)
```bash
# 1. Login as admin
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@astrology.ai","password":"admin123"}'

# 2. Save token, then create user
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"new@user.com","password":"pass123","name":"New User"}'
```

### Change User Password (as admin)
```bash
curl -X PUT http://localhost:5000/api/admin/users/USER_ID \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"newpassword123"}'
```

### Chat with AI (as user)
```bash
# 1. Login as user
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass123"}'

# 2. Ask question
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How will my spouse look?",
    "chart_data": "RASHI CHART (D1):\nAscendant: Cancer\n7th House: Venus in Capricorn",
    "niche": "Love & Relationships"
  }'
```

---

## 🗄️ Database

**Connection:** Already configured in `database.py`
```
mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/
```

**Database:** `astrology_ai`

**Collections:**
- `users` - User accounts
- `chats` - Chat history

---

## 🎓 Learning Path

### Beginner
1. Read **QUICK_REFERENCE.md**
2. Run `python test_api.py`
3. Try cURL commands from **QUICK_REFERENCE.md**

### Intermediate
1. Read **API_README.md** (complete docs)
2. Import Postman collection
3. Test all endpoints

### Advanced
1. Read **ARCHITECTURE.md** (system design)
2. Read **IMPLEMENTATION_SUMMARY.md** (what was built)
3. Modify and extend the API

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Connection refused" (MongoDB)
Check your internet connection. MongoDB URI is already configured.

### "AI not initialized"
Make sure you have valid GCP credentials in `.env` file.

### "Port already in use"
Change port in `api.py` or kill the process using port 5000.

---

## 📞 Need Help?

1. **Quick commands?** → Read **QUICK_REFERENCE.md**
2. **API details?** → Read **API_README.md**
3. **Setup issues?** → Read **SETUP_GUIDE.md**
4. **Architecture?** → Read **ARCHITECTURE.md**
5. **What was built?** → Read **IMPLEMENTATION_SUMMARY.md**

---

## 🎯 Next Steps

### For Development
1. ✅ Test all endpoints
2. ✅ Build frontend application
3. ✅ Integrate with your UI

### For Production
1. ⚠️ Change `JWT_SECRET` in `.env`
2. ⚠️ Change admin password
3. ⚠️ Configure CORS for your domain
4. ⚠️ Use HTTPS
5. ⚠️ Add rate limiting
6. ⚠️ Deploy to Cloud Run

---

## 📦 What's Included

```
✅ User authentication (JWT)
✅ Password hashing (bcrypt)
✅ Admin CRUD operations
✅ AI chat integration
✅ Chat history storage
✅ MongoDB integration
✅ Complete API documentation
✅ cURL examples for all endpoints
✅ Postman collection
✅ Automated tests
✅ Setup scripts
✅ Architecture diagrams
```

---

## 🚀 Ready to Start?

### Quick Test Flow
```bash
# 1. Start server
python api.py

# 2. In another terminal, run tests
python test_api.py

# 3. Check output - should see ✅ for all tests
```

### Production Flow
```bash
# 1. Update .env with production values
# 2. Change admin password
# 3. Deploy to Cloud Run
# 4. Configure domain and HTTPS
```

---

## 📊 Features Summary

| Feature | Status | File |
|---------|--------|------|
| User Signup | ✅ | api.py |
| User Login | ✅ | api.py |
| JWT Auth | ✅ | auth.py |
| Admin CRUD | ✅ | api.py |
| Password Management | ✅ | auth.py |
| AI Chat | ✅ | api.py |
| Chat History | ✅ | api.py |
| MongoDB | ✅ | database.py |
| Documentation | ✅ | Multiple .md files |
| Tests | ✅ | test_api.py |

---

## 🎉 You're All Set!

Everything is ready to use. Start with:

1. **Run:** `python api.py`
2. **Test:** `python test_api.py`
3. **Read:** `QUICK_REFERENCE.md`

**Happy coding! 🚀**

---

**MongoDB:** `mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/`

**Admin:** `admin@astrology.ai / admin123`

**API:** `http://localhost:5000`
