
# 🌟 Vedic Astrology AI (RAG Engine)

Production-ready AI system for analyzing Vedic astrology birth charts using RAG Engine grounding.

> **📚 NEW:** Complete authentication system with admin panel! See [START_HERE.md](START_HERE.md) to get started.
> 
> **📖 Documentation:** See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete documentation guide.

## Features

- 📚 Classical Vedic astrology texts (BPHS, Phaladeepika, Brihat Jataka, Light on Life)
- 🤖 Gemini 2.5 Flash AI with RAG Engine
- 🎨 Gradio web interface
- 🔐 User authentication & authorization (JWT)
- 👨💼 Admin panel with full CRUD operations
- 💬 Authenticated AI chat API
- 🗄️ MongoDB database integration
- ☁️ Google Cloud Run deployment
- 🔄 Automatic retry logic for rate limits
- 📊 Comprehensive astrological analysis

## Quick Start - Local Development

### Prerequisites
- Python 3.10+
- Google Cloud project with Vertex AI enabled
- RAG Engine corpus (ID: 3379951520341557248)
- Google Cloud API Key
- MongoDB Atlas account (provided)

### Installation

```
# Clone or download repository
cd astrology-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_CLOUD_API_KEY

# Create admin user
python create_admin.py

# Run API server (for REST API)
python api.py
# API runs on: http://localhost:5000

# OR run Gradio interface (for web UI)
python main.py
# Gradio runs on: http://127.0.0.1:7860
```

## Deployment to Cloud Run

### Prerequisites
- GitHub account with repository
- Google Cloud project with:
  - Cloud Run enabled
  - Cloud Build enabled
  - Artifact Registry enabled
  - Proper IAM roles

### Steps

1. Create GitHub repository: https://github.com/new
   - Name: astrology-ai
   - Visibility: Public

2. Connect GitHub to Cloud Build:
   - Go to: https://console.cloud.google.com/cloud-build/triggers
   - Create trigger from GitHub repository

3. Set Cloud Build secrets:
   - Name: _GOOGLE_CLOUD_API_KEY
   - Value: Your API key

4. Push code to GitHub (Cloud Build auto-deploys)

```
git add .
git commit -m "Initial commit"
git push origin main
```

5. Monitor deployment:
   - Cloud Build: https://console.cloud.google.com/cloud-build
   - Cloud Run: https://console.cloud.google.com/run

## Configuration

Environment variables in `.env`:

```
GCP_PROJECT_ID=superb-analog-464304-s0
GCP_REGION=asia-south1
RAG_CORPUS_ID=3379951520341557248
GOOGLE_CLOUD_API_KEY=your_key_here
MODEL_NAME=gemini-1.5-flash
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=8192
TOP_P=0.8

# Authentication
JWT_SECRET=astro_secret_key_2024

# MongoDB
MONGO_URI=mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/
DB_NAME=astrology_ai
```

## Cloud Run Settings

- Memory: 2 GiB
- CPU: 2 vCPU
- Timeout: 600 seconds
- Concurrency: 10 requests/instance
- Execution: Second generation
- Min instances: 0
- Max instances: 10

## Usage

### Web Interface (Gradio)
1. Run `python main.py`
2. Enter your birth chart data (D1, D9, D10)
3. Ask your astrology question
4. Click "🔮 Analyze Chart"
5. Get detailed analysis with classical text citations

### REST API
1. Run `python api.py`
2. See `API_README.md` for complete API documentation
3. Use cURL or Postman to interact with endpoints

**Default Admin Credentials:**
- Email: `admin@astrology.ai`
- Password: `admin123`

## Cost Estimate

Per request: ~$0.0003
1000 requests: ~$0.30
10,000 requests: ~$3.00

With $25K GCP credit: Can handle 80+ million requests

## Troubleshooting

**ModuleNotFoundError**
```
pip install -r requirements.txt
```

**API Key Error**
- Ensure GOOGLE_CLOUD_API_KEY is correct
- Verify API key has Vertex AI permissions

**Connection Timeout**
- Check internet connection
- Verify RAG Corpus ID is correct
- Check region is asia-south1

## Future Enhancement

Add Google Search grounding for modern synthesis:
- Modify astrology_rag.py to include Google Search
- Update system instructions for synthesis
- Test locally, then deploy

## API Endpoints

See `API_README.md` for complete documentation with cURL examples.

### Authentication
- `POST /api/signup` - Create new user
- `POST /api/login` - Login user
- `GET /api/me` - Get current user profile

### Admin (Admin Only)
- `GET /api/admin/users` - Get all users
- `GET /api/admin/users/<id>` - Get user (with password)
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/<id>` - Update user
- `DELETE /api/admin/users/<id>` - Delete user

### AI Chat (Authenticated)
- `POST /api/chat` - Ask astrology question
- `GET /api/chat/history` - Get chat history

## Project Structure

```
astrology-ai/
├── Dockerfile              # Container configuration
├── cloudbuild.yaml         # Cloud Build configuration
├── requirements.txt        # Python dependencies
├── config.py              # Configuration management
├── main.py                # Gradio web interface
├── api.py                 # Flask REST API
├── auth.py                # JWT authentication
├── database.py            # MongoDB connection
├── create_admin.py        # Admin user creation
├── test_api.py            # API testing script
├── .env.example           # Environment template
├── README.md              # This file
├── API_README.md          # Complete API documentation
├── agents/                # AI agents
├── niche_instructions/    # Niche-specific prompts
├── utils/                 # Utilities
└── run_locally.sh         # Local run script
```

## Database

**MongoDB Connection:**
```
mongodb+srv://karmansingharora01:8813917626k@cluster0.pv8tb2q.mongodb.net/
```

**Database:** `astrology_ai`

**Collections:**
- `users` - User accounts with authentication
- `chats` - Chat history for all users

## Testing

```bash
# Test all API endpoints
python test_api.py
```

## License

Private project - For authorized users only
