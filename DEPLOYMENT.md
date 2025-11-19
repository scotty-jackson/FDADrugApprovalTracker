# Deployment Guide

This guide provides detailed instructions for deploying the FDA Drug Approval Tracker to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 22.04 LTS or similar Linux distribution
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB
- **CPU**: 2+ cores recommended

### Software Requirements

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+
- Nginx
- Git

## Environment Configuration

### 1. Create Environment File

```bash
cd /var/www/fdatracker
cp .env.example .env
nano .env
```

### 2. Configure Environment Variables

```bash
# Database
DATABASE_URL=postgresql://fdauser:STRONG_PASSWORD@localhost:5432/fdatracker
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fdatracker
DB_USER=fdauser
DB_PASSWORD=STRONG_PASSWORD

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com

# Frontend
VITE_API_BASE_URL=https://yourdomain.com/api
```

## Database Setup

### 1. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database and User

```bash
sudo -u postgres psql

CREATE DATABASE fdatracker;
CREATE USER fdauser WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE fdatracker TO fdauser;
\q
```

### 3. Secure PostgreSQL

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# Change from 'peer' to 'md5' for local connections
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 4. Initialize Database Schema

```bash
cd /var/www/fdatracker
source backend/venv/bin/activate
python scripts/init_db.py
python scripts/seed_data.py
```

## Backend Deployment

### 1. Install Python Dependencies

```bash
cd /var/www/fdatracker/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Create systemd Service

Create `/etc/systemd/system/fdatracker-backend.service`:

```ini
[Unit]
Description=FDA Drug Approval Tracker Backend API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/fdatracker/backend
Environment="PATH=/var/www/fdatracker/backend/venv/bin"
Environment="PYTHONPATH=/var/www/fdatracker/backend"
EnvironmentFile=/var/www/fdatracker/.env
ExecStart=/var/www/fdatracker/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fdatracker-backend

[Install]
WantedBy=multi-user.target
```

### 3. Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/fdatracker
sudo chmod -R 755 /var/www/fdatracker
```

### 4. Start Backend Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable fdatracker-backend
sudo systemctl start fdatracker-backend
sudo systemctl status fdatracker-backend
```

### 5. View Logs

```bash
sudo journalctl -u fdatracker-backend -f
```

## Frontend Deployment

### 1. Install Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Build Frontend

```bash
cd /var/www/fdatracker/frontend
npm install
npm run build
```

The built files will be in `frontend/dist/`.

## Nginx Configuration

### 1. Install Nginx

```bash
sudo apt install nginx
```

### 2. Create Site Configuration

Create `/etc/nginx/sites-available/fdatracker`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Upstream backend
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/fdatracker_access.log;
    error_log /var/log/nginx/fdatracker_error.log;

    # Root directory for frontend
    root /var/www/fdatracker/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        image/svg+xml;

    # Frontend - SPA routing
    location / {
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API Documentation
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/fdatracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/HTTPS Setup

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Auto-renewal

Certbot automatically sets up renewal. Test it:

```bash
sudo certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. Set Up Log Rotation

Create `/etc/logrotate.d/fdatracker`:

```
/var/log/nginx/fdatracker_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 2. Database Backups

Create `/usr/local/bin/backup-fdatracker-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/fdatracker"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U fdauser fdatracker > $BACKUP_DIR/fdatracker_$DATE.sql

# Compress
gzip $BACKUP_DIR/fdatracker_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "fdatracker_*.sql.gz" -mtime +7 -delete

echo "Backup completed: fdatracker_$DATE.sql.gz"
```

Make executable and schedule:

```bash
sudo chmod +x /usr/local/bin/backup-fdatracker-db.sh
sudo crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /usr/local/bin/backup-fdatracker-db.sh
```

### 3. Schedule Data Ingestion

```bash
crontab -e

# Run data ingestion daily at 3 AM
0 3 * * * cd /var/www/fdatracker && /var/www/fdatracker/backend/venv/bin/python scripts/ingest_fda_data.py >> /var/log/fdatracker-ingestion.log 2>&1
```

### 4. Monitoring with systemd

Check service status:

```bash
sudo systemctl status fdatracker-backend
sudo systemctl status nginx
sudo systemctl status postgresql
```

View logs:

```bash
# Backend logs
sudo journalctl -u fdatracker-backend -n 100 -f

# Nginx logs
sudo tail -f /var/log/nginx/fdatracker_error.log
sudo tail -f /var/log/nginx/fdatracker_access.log
```

## Troubleshooting

### Backend Not Starting

1. Check logs:
   ```bash
   sudo journalctl -u fdatracker-backend -n 50
   ```

2. Verify database connection:
   ```bash
   psql -U fdauser -d fdatracker -h localhost
   ```

3. Check environment variables:
   ```bash
   sudo systemctl show fdatracker-backend | grep Environment
   ```

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check PostgreSQL logs:
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-15-main.log
   ```

3. Test connection:
   ```bash
   psql -U fdauser -d fdatracker -h localhost -W
   ```

### Nginx Issues

1. Test configuration:
   ```bash
   sudo nginx -t
   ```

2. Check error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Verify backend is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

### Frontend Not Loading

1. Verify files exist:
   ```bash
   ls -la /var/www/fdatracker/frontend/dist/
   ```

2. Check nginx access:
   ```bash
   sudo -u www-data cat /var/www/fdatracker/frontend/dist/index.html
   ```

3. Rebuild frontend:
   ```bash
   cd /var/www/fdatracker/frontend
   npm run build
   ```

### Performance Issues

1. Increase backend workers in systemd service
2. Enable PostgreSQL query logging and optimize slow queries
3. Add database indexes for frequently queried fields
4. Enable Nginx caching for API responses
5. Consider adding Redis for caching

## Updates and Deployment

### Update Application

```bash
cd /var/www/fdatracker

# Pull latest code
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fdatracker-backend

# Update frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### Database Migrations

```bash
cd /var/www/fdatracker/backend
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

## Security Best Practices

1. **Keep software updated**: Regularly update OS, Python, Node.js, PostgreSQL, Nginx
2. **Use strong passwords**: For database and any admin interfaces
3. **Firewall**: Configure UFW to only allow necessary ports
4. **Regular backups**: Automate database and file backups
5. **Monitor logs**: Set up alerts for suspicious activity
6. **Rate limiting**: Already configured in Nginx
7. **Environment variables**: Never commit .env files to git

## Performance Optimization

1. **Database indexing**: Add indexes on frequently queried columns
2. **Connection pooling**: Already configured in SQLAlchemy
3. **Caching**: Consider adding Redis for API caching
4. **CDN**: Use CloudFlare or similar for static assets
5. **Compression**: Already enabled in Nginx
6. **HTTP/2**: Enable in Nginx for better performance

## Scaling

For high traffic, consider:

1. **Load balancing**: Multiple backend instances behind load balancer
2. **Database replication**: PostgreSQL read replicas
3. **Caching layer**: Redis or Memcached
4. **CDN**: For static assets and API responses
5. **Horizontal scaling**: Multiple application servers
