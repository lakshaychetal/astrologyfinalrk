# Deployment Guide for AstroAirk API

## 🚀 Deployment Options

### Option 1: Google Cloud Run (Recommended)

**Benefits:**
- ✅ Auto-scaling
- ✅ Pay-per-use
- ✅ Built-in HTTPS
- ✅ No server management
- ✅ Global CDN

**Steps:**

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Deploy**
   ```bash
   cd /path/to/astroairk
   
   gcloud run deploy astroairk-api \
     --source . \
     --region asia-south1 \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300s \
     --max-instances 10 \
     --min-instances 0 \
     --allow-unauthenticated \
     --set-env-vars="ENV=production,USE_REAL_RAG=true"
   ```

4. **Set Environment Variables**
   ```bash
   gcloud run services update astroairk-api \
     --region asia-south1 \
     --update-env-vars \
       GCP_PROJECT_ID=your-project-id,\
       GCP_REGION=asia-south1,\
       RAG_CORPUS_ID=your-corpus-id,\
       OPENROUTER_API_KEY=sk-or-v1-your-key,\
       GOOGLE_CLOUD_API_KEY=your-gcp-key
   ```

5. **Get URL**
   ```bash
   gcloud run services describe astroairk-api \
     --region asia-south1 \
     --format 'value(status.url)'
   ```

**Your API will be available at:**
`https://astroairk-api-xxx-asia-south1.run.app`

---

### Option 2: Docker (Any Cloud/VPS)

**Steps:**

1. **Build Image**
   ```bash
   docker build -t astroairk-api .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name astroairk-api \
     -p 8080:8080 \
     --env-file .env \
     --restart unless-stopped \
     astroairk-api
   ```

3. **Check Logs**
   ```bash
   docker logs -f astroairk-api
   ```

4. **Stop/Start**
   ```bash
   docker stop astroairk-api
   docker start astroairk-api
   ```

---

### Option 3: VPS (Ubuntu/Debian)

**Steps:**

1. **Install Dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python 3.9+
   sudo apt install python3 python3-pip python3-venv -y
   
   # Install system packages
   sudo apt install gcc g++ curl -y
   ```

2. **Clone Repository**
   ```bash
   cd /opt
   sudo git clone <your-repo-url> astroairk
   cd astroairk
   ```

3. **Setup Environment**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy and edit .env
   cp .env.example .env
   nano .env  # Edit with your keys
   ```

5. **Create Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/astroairk.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=AstroAirk API
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/astroairk
   Environment="PATH=/opt/astroairk/.venv/bin"
   ExecStart=/opt/astroairk/.venv/bin/python api_main.py
   Restart=always
   RestartSec=3
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable astroairk
   sudo systemctl start astroairk
   sudo systemctl status astroairk
   ```

7. **Setup Nginx Reverse Proxy**
   ```bash
   sudo apt install nginx -y
   sudo nano /etc/nginx/sites-available/astroairk
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   Enable:
   ```bash
   sudo ln -s /etc/nginx/sites-available/astroairk /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

8. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

---

## 🔒 Production Security Checklist

### Before Going Live

- [ ] **Environment Variables**
  - [ ] All API keys in environment (not hardcoded)
  - [ ] `.env` file in `.gitignore`
  - [ ] Strong secrets (minimum 32 characters)

- [ ] **API Security**
  - [ ] API key authentication enabled
  - [ ] CORS whitelist (specific domains only)
  - [ ] Rate limiting (100 req/hour per user)
  - [ ] Input validation on all endpoints
  - [ ] Request size limits (1MB max)

- [ ] **Infrastructure**
  - [ ] HTTPS enabled (SSL certificate)
  - [ ] Firewall configured (only ports 80, 443 open)
  - [ ] DDoS protection enabled
  - [ ] Automatic backups configured
  - [ ] Monitoring and alerting setup

- [ ] **Code**
  - [ ] All debug logs disabled in production
  - [ ] Error messages don't expose internal details
  - [ ] SQL injection prevention (N/A for this API)
  - [ ] XSS prevention (JSON responses only)

---

## 📊 Monitoring Setup

### Google Cloud Monitoring (Cloud Run)

```bash
# View logs
gcloud run services logs read astroairk-api \
  --region asia-south1 \
  --limit 100

# Follow logs in real-time
gcloud run services logs tail astroairk-api \
  --region asia-south1
```

### Uptime Monitoring

Add health check monitor:

```bash
# Cloud Monitoring uptime check
gcloud monitoring uptime-checks create \
  --display-name="AstroAirk API Health" \
  --resource-type=uptime-url \
  --host=astroairk-api-xxx-asia-south1.run.app \
  --path=/health
```

### Performance Monitoring

Log important metrics:

```python
# Already built into api_main.py
logger.info(f"✅ Answer generated in {total_latency}ms")
logger.info(f"📥 Session init request from user: {request.user_id}")
logger.info(f"❓ Query: {request.question[:60]}...")
```

---

## 🔄 Update/Rollback

### Update to New Version

```bash
# Google Cloud Run
gcloud run deploy astroairk-api \
  --source . \
  --region asia-south1

# Docker
docker pull astroairk-api:latest
docker stop astroairk-api
docker rm astroairk-api
docker run -d --name astroairk-api -p 8080:8080 --env-file .env astroairk-api:latest

# VPS
cd /opt/astroairk
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart astroairk
```

### Rollback

```bash
# Google Cloud Run - rollback to previous revision
gcloud run services update-traffic astroairk-api \
  --to-revisions=astroairk-api-00002-xxx=100 \
  --region asia-south1

# Docker - use specific tag
docker run -d --name astroairk-api -p 8080:8080 --env-file .env astroairk-api:v1.0.0

# VPS - git checkout
cd /opt/astroairk
git checkout v1.0.0
sudo systemctl restart astroairk
```

---

## 💰 Cost Estimation (Google Cloud Run)

### Free Tier
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

### Paid Tier (After Free Tier)
- **Requests:** $0.40 per million
- **Memory:** $0.0000025 per GB-second
- **CPU:** $0.00001 per vCPU-second

### Example Monthly Cost

**Scenario:** 50,000 requests/month, avg 3s response time, 2GB memory, 2 vCPU

```
Requests: 50,000 * $0.40 / 1,000,000 = $0.02
Memory: 50,000 * 3s * 2GB * $0.0000025 = $0.75
CPU: 50,000 * 3s * 2 vCPU * $0.00001 = $3.00

Total: ~$3.77/month
```

**With free tier:** First 2M requests are free, so likely $0-5/month for small usage.

---

## 🐛 Troubleshooting Deployment

### Issue: "Permission denied" on Cloud Run

```bash
# Enable necessary APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Add IAM permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@gmail.com" \
  --role="roles/run.admin"
```

### Issue: "Service unavailable" after deployment

```bash
# Check logs for errors
gcloud run services logs read astroairk-api --region asia-south1 --limit 100

# Common issues:
# 1. Missing environment variables → Set them with --update-env-vars
# 2. Memory limit too low → Increase with --memory 2Gi
# 3. Timeout too short → Increase with --timeout 300s
```

### Issue: Docker container crashes

```bash
# Check logs
docker logs astroairk-api

# Common issues:
# 1. Missing .env file → Create .env with proper keys
# 2. Port conflict → Use different port: -p 8081:8080
# 3. Permission issues → Run with correct user
```

### Issue: Slow response times

```bash
# Check if RAG cache is loaded
curl http://your-api-url/api/v1/session/{session-id}/status

# Solutions:
# 1. Wait for cache to load (cache_loaded: true)
# 2. Increase memory: --memory 4Gi
# 3. Increase CPU: --cpu 4
# 4. Check RAG corpus connectivity
```

---

## 📞 Support

- **Issues:** GitHub repository
- **Email:** [Your email]
- **Logs:** Check Cloud Run/Docker/systemd logs

---

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] `/health` endpoint returns 200 OK
- [ ] `/docs` shows API documentation
- [ ] Can create session successfully
- [ ] Can ask questions and get responses
- [ ] Latency is acceptable (draft <2s, expand <6s)
- [ ] Logs are being captured
- [ ] Monitoring/alerts are working
- [ ] HTTPS is enabled
- [ ] CORS allows your frontend domain
- [ ] Rate limiting is working (if enabled)

---

**You're ready to deploy!** 🚀

Choose your deployment option and follow the steps above.
