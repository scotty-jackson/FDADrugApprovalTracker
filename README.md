# FDA Drug Approval + Clinical Trials Pipeline Tracker

A comprehensive full-stack web application for tracking FDA drug approvals, clinical trial pipelines, upcoming PDUFA dates, and investment catalysts. Built with modern technologies and designed for investors, analysts, healthcare professionals, and patients to track the drug development pipeline from early trials to FDA approval.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)

## 🎯 Features

### FDA Drug Approvals
- **Recent Approvals Dashboard**: Browse and search FDA drug approvals with advanced filtering
- **Upcoming Events Calendar**: Track PDUFA dates and advisory committee meetings
- **Drug Detail Pages**: Comprehensive information including approval history and events
- **Email Subscriptions**: Subscribe to drug-specific email updates for approvals and events
- **Summary Analytics**: Charts and statistics showing approval trends
- **Advanced Filtering**: Filter by therapeutic area, FDA center, application type, sponsor, and ticker

### Clinical Trials Pipeline
- **Trials Explorer**: Search and filter 1000s of clinical trials from ClinicalTrials.gov
- **Trial Detail Pages**: Full trial information including conditions, interventions, outcomes
- **Company Pipeline Dashboards**: Complete pipeline view by phase, disease area, and geography
- **Disease Area Analysis**: Competitive landscape with trials by phase and top companies
- **Phase Filtering**: Filter trials by Early Phase 1, Phase 1, 2, 3, 4
- **Status Tracking**: Track recruiting, active, completed, and terminated trials

### Investment Catalysts
- **Catalyst Calendar**: Upcoming FDA decisions, trial readouts, and regulatory events grouped by month
- **Probability Scoring**: AI-driven probability bands (Very High, High, Medium, Low) for each catalyst
- **Multi-Source Integration**: Catalysts auto-generated from trial completion dates and FDA events
- **Company-Level View**: All upcoming catalysts for specific companies
- **Type Filtering**: Filter by PDUFA dates, AdCom meetings, topline readouts, primary completions

### Technology & UX
- **SEO Optimized**: Clean URLs and meta tags for search engine visibility
- **Email Notifications**: Passwordless subscription system with verification
- **Ad-Ready**: Pre-configured ad placement containers for monetization
- **Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- **Data Visualizations**: Charts and graphs using Recharts (pie, bar, sankey diagrams)
- **Real-time Search**: Instant filtering and search across all data types

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (modern, fast web framework)
- PostgreSQL (relational database)
- SQLAlchemy (ORM)
- Alembic (database migrations)

**Frontend:**
- React 18
- Vite (fast build tool)
- Material-UI (component library)
- Recharts (data visualization)
- React Router (client-side routing)

**Infrastructure:**
- Docker & Docker Compose (containerization)
- Nginx (web server for production)

### Project Structure

```
FDADrugApprovalTracker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connection
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── services.py     # Business logic layer
│   │   └── routers/        # API route handlers
│   ├── alembic/            # Database migrations
│   ├── tests/              # Unit tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container config
├── frontend/               # React frontend
│   ├── src/
│   │   ├── main.jsx        # Application entry point
│   │   ├── App.jsx         # Main app component
│   │   ├── config.js       # Frontend configuration
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client layer
│   │   └── hooks/          # Custom React hooks
│   ├── package.json        # Node dependencies
│   ├── vite.config.js      # Vite configuration
│   └── Dockerfile          # Frontend container config
├── scripts/                       # Utility scripts
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Seed sample data
│   ├── ingest_fda_data.py         # FDA data ingestion
│   ├── ingest_clinical_trials.py  # ClinicalTrials.gov data ingestion
│   ├── generate_catalysts.py      # Auto-generate investment catalysts
│   └── send_notifications.py      # Email notification background job
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 15 or higher
- Git

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd FDADrugApprovalTracker
```

#### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure your database credentials and other settings.

#### 3. Set Up PostgreSQL Database

Create a PostgreSQL database:

```bash
psql -U postgres
CREATE DATABASE fdatracker;
CREATE USER fdauser WITH PASSWORD 'fdapassword';
GRANT ALL PRIVILEGES ON DATABASE fdatracker TO fdauser;
\q
```

#### 4. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
cd ..
python scripts/init_db.py

# Load sample data
python scripts/seed_data.py

# Start backend server
cd backend
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

#### 5. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### 6. (Optional) Run Data Ingestion

```bash
python scripts/ingest_fda_data.py --verbose
```

**Note**: The included ingestion script is a template. In production, you'll need to implement actual FDA data source integration.

### Running with Docker

The easiest way to run the entire stack:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will start:
- PostgreSQL on port 5432
- Backend API on port 8000
- Frontend on port 80

## 📊 Data Sources

The application integrates data from multiple public sources:

### FDA Drug Approvals
1. **FDA Drugs@FDA Database**: https://www.accessdata.fda.gov/scripts/cder/daf/
2. **FDA CDER Approvals**: https://www.fda.gov/drugs/new-drugs-fda-cders-new-molecular-entities-and-new-therapeutic-biological-products
3. **FDA CBER Approvals**: https://www.fda.gov/vaccines-blood-biologics/approvals-clearances
4. **FDA Press Releases**: https://www.fda.gov/news-events/fda-newsroom/press-announcements

### Clinical Trials
5. **ClinicalTrials.gov API v2**: https://clinicaltrials.gov/api/v2/
   - Global clinical trial registry with 400,000+ trials
   - Structured data on phase, status, conditions, interventions, outcomes
   - Updated daily with new trial registrations

### Data Ingestion

#### FDA Drug Approvals

The `scripts/ingest_fda_data.py` script provides a framework for fetching FDA data:

```bash
# Manual run
python scripts/ingest_fda_data.py --verbose

# Incremental update (only new records)
python scripts/ingest_fda_data.py --incremental

# Schedule with cron (daily at 2 AM)
0 2 * * * cd /path/to/project && /path/to/venv/bin/python scripts/ingest_fda_data.py --incremental
```

#### Clinical Trials

The `scripts/ingest_clinical_trials.py` script fetches trial data from ClinicalTrials.gov API v2:

```bash
# Manual run - fetch all trials in a disease area
python scripts/ingest_clinical_trials.py --disease-area "Oncology" --limit 1000

# Incremental update (only trials updated in last 7 days)
python scripts/ingest_clinical_trials.py --incremental

# Filter by phase and status
python scripts/ingest_clinical_trials.py --phase "Phase 3" --status "Recruiting" --limit 500

# Schedule with cron (daily at 3 AM)
0 3 * * * cd /path/to/project && /path/to/venv/bin/python scripts/ingest_clinical_trials.py --incremental
```

#### Investment Catalysts

The `scripts/generate_catalysts.py` script auto-generates catalysts from trials and events:

```bash
# Generate all catalysts
python scripts/generate_catalysts.py

# Regenerate all catalysts (delete and recreate)
python scripts/generate_catalysts.py --regenerate

# Update probabilities based on current trial status
python scripts/generate_catalysts.py --update-probabilities

# Archive old catalysts
python scripts/generate_catalysts.py --archive-old

# Schedule with cron (daily at 4 AM)
0 4 * * * cd /path/to/project && /path/to/venv/bin/python scripts/generate_catalysts.py --update-probabilities
```

#### Email Notifications

The `scripts/send_notifications.py` script sends email notifications to subscribers:

```bash
# Send all pending notifications
python scripts/send_notifications.py

# Send only event reminders (7 days before)
python scripts/send_notifications.py --reminders-only

# Schedule with cron (daily at 8 AM)
0 8 * * * cd /path/to/project && /path/to/venv/bin/python scripts/send_notifications.py
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

**Database:**
- `DATABASE_URL`: PostgreSQL connection string
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection details

**Backend:**
- `BACKEND_HOST`: Backend server host (default: 0.0.0.0)
- `BACKEND_PORT`: Backend server port (default: 8000)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)

**Frontend:**
- `VITE_API_BASE_URL`: Backend API URL for frontend

**Data Ingestion:**
- `FDA_REQUEST_DELAY_SECONDS`: Delay between FDA API requests
- `FDA_MAX_RETRIES`: Maximum retry attempts for failed requests

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm run test  # If test script is configured
```

## 🚢 Deployment

### VPS Deployment (DigitalOcean, Linode, etc.)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv postgresql nginx certbot python3-certbot-nginx

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Deploy Application

```bash
# Clone repository
git clone <repository-url> /var/www/fdatracker
cd /var/www/fdatracker

# Set up environment
cp .env.example .env
nano .env  # Edit configuration

# Set up backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
cd ..
python scripts/init_db.py
python scripts/seed_data.py
```

#### 3. Configure systemd for Backend

Create `/etc/systemd/system/fdatracker-backend.service`:

```ini
[Unit]
Description=FDA Drug Approval Tracker Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/fdatracker/backend
Environment="PATH=/var/www/fdatracker/backend/venv/bin"
ExecStart=/var/www/fdatracker/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable fdatracker-backend
sudo systemctl start fdatracker-backend
sudo systemctl status fdatracker-backend
```

#### 4. Build and Deploy Frontend

```bash
cd /var/www/fdatracker/frontend
npm install
npm run build
```

#### 5. Configure Nginx

Create `/etc/nginx/sites-available/fdatracker`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/fdatracker/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/fdatracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Set Up SSL with Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com
```

### Docker Deployment

```bash
# Production deployment with Docker
docker-compose -f docker-compose.prod.yml up -d
```

## 💰 Monetization (AdSense Integration)

The application includes pre-configured ad placement containers:

1. **Top Banner Ad** (`#ad-top-banner`): 728x90 or responsive
2. **Sidebar Ad** (`#ad-sidebar`): 160x600 (hidden on mobile)
3. **In-Content Ad** (`#ad-in-content`): 336x280 or responsive

To integrate Google AdSense:

1. Sign up for Google AdSense
2. Get your AdSense code
3. Insert the code into the designated `<div>` elements in `frontend/src/components/Layout.jsx`

## 📈 Roadmap

### Completed ✅
- [x] FDA drug approval tracking and filtering
- [x] Clinical trial data integration (ClinicalTrials.gov API v2)
- [x] Email notification system with verification
- [x] Investment catalyst tracking and auto-generation
- [x] Company pipeline dashboards
- [x] Disease area competitive analysis
- [x] Passwordless subscription system
- [x] Data visualizations (charts, graphs)
- [x] Mobile-responsive design
- [x] SEO optimization

### Near-term Improvements

- [ ] Implement actual FDA Drugs@FDA dataset integration (CSV/XML downloads)
- [ ] Add EUCTR (European clinical trials) data integration
- [ ] Sankey diagram visualization for trial phase progression
- [ ] Trial detail page with full trial information
- [ ] Expand company-to-ticker mapping database
- [ ] Add user accounts and personalized watchlists
- [ ] Integrate adverse event data (FAERS)
- [ ] Implement full-text search with Elasticsearch
- [ ] Add email digest mode (daily/weekly summaries)
- [ ] Stock price integration for company dashboards

### Long-term Features

- [ ] Mobile app (React Native)
- [ ] Premium subscription tier with advanced analytics
- [ ] API access for third-party developers
- [ ] Machine learning predictions for approval likelihood and catalyst timing
- [ ] Integration with financial data (stock prices, market cap, analyst ratings)
- [ ] RSS feeds and webhooks for notifications
- [ ] Multilingual support
- [ ] Real-time notifications via WebSocket
- [ ] AI-powered disease area mapping and normalization
- [ ] Competitive intelligence dashboard (pipeline comparison across companies)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This application is for informational purposes only and is not medical or investment advice. Data accuracy is not guaranteed. This project is not affiliated with or endorsed by the U.S. Food and Drug Administration (FDA).

Always verify critical information with official FDA sources and consult qualified professionals for medical or investment decisions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

## 🙏 Acknowledgments

- FDA for providing public access to drug approval data
- The open-source community for the excellent tools and libraries used in this project
