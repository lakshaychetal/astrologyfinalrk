
# 🌟 Vedic Astrology AI (RAG Engine)

Production-ready AI system for analyzing Vedic astrology birth charts using RAG Engine grounding.

## Features

- 📚 Classical Vedic astrology texts (BPHS, Phaladeepika, Brihat Jataka, Light on Life)
- 🤖 Gemini 2.5 Flash AI with RAG Engine
- 🎨 Gradio web interface
- ☁️ Google Cloud Run deployment
- 🔄 Automatic retry logic for rate limits
- 📊 Comprehensive astrological analysis

## Quick Start - Local Development

### Prerequisites
- Python 3.10+
- Google Cloud project with Vertex AI enabled
- RAG Engine corpus (ID: 2305843009213693952)
- Google Cloud API Key

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

# Run locally
python main.py
```

Open browser to: http://127.0.0.1:7860

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
RAG_CORPUS_ID=2305843009213693952
GOOGLE_CLOUD_API_KEY=your_key_here
MODEL_NAME=gemini-2.5-flash
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=8192
TOP_P=0.8
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

1. Enter your birth chart data (D1, D9, D10)
2. Ask your astrology question
3. Click "🔮 Analyze Chart"
4. Get detailed analysis with classical text citations

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

## Project Structure

```
astrology-ai/
├── Dockerfile              # Container configuration
├── cloudbuild.yaml         # Cloud Build configuration
├── requirements.txt        # Python dependencies
├── config.py              # Configuration management
├── astrology_rag.py       # RAG + Gemini integration
├── main.py                # Gradio web interface
├── .env.example           # Environment template
├── README.md              # This file
└── run_locally.sh         # Local run script
```

## License

Private project - For authorized users only
