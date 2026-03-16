# Deployment Guide

> **Project:** Blue Falcon - Airport Operations Management System  
> **Version:** 1.0  
> **Last Updated:** March 15, 2026  

---

## Table of Contents

1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [Render.com Deployment (Recommended)](#rendercom-deployment)
4. [Traditional VPS Deployment](#traditional-vps-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Database Configuration](#database-configuration)
7. [Environment Variables](#environment-variables)
8. [Static Files](#static-files)
9. [Background Tasks](#background-tasks)
10. [SSL/HTTPS Configuration](#sslhttps-configuration)
11. [Monitoring & Logging](#monitoring--logging)
12. [Backup & Recovery](#backup--recovery)
13. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers production deployment of the Blue Falcon Airport Operations Management System. The application supports multiple deployment scenarios from managed cloud platforms to traditional VPS setups.

### Deployment Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **CPU** | 1 core | 2+ cores |
| **RAM** | 512 MB | 2+ GB |
| **Storage** | 1 GB | 10+ GB |
| **Python** | 3.12 | 3.12+ |
| **Database** | SQLite | PostgreSQL 12+ |
| **Cache** | LocMem | Redis |

---

## Deployment Options

### Option 1: Render.com (Recommended)

**Best for:** Quick deployment, managed infrastructure, automatic SSL

**Pros:**
- One-click deployment
- Managed PostgreSQL and Redis
- Automatic SSL certificates
- Automatic deployments on git push
- Free tier available

**Cons:**
- Less control over infrastructure
- Vendor lock-in

### Option 2: Traditional VPS

**Best for:** Full control, cost optimization at scale

**Pros:**
- Complete control over server configuration
- Cost-effective at scale
- No vendor lock-in

**Cons:**
- Requires server administration
- Manual SSL management
- More setup time

### Option 3: Docker

**Best for:** Containerized deployments, Kubernetes

**Pros:**
- Consistent environments
- Easy scaling
- Portable

**Cons:**
- Docker expertise required
- Additional complexity

---

## Render.com Deployment

### Step 1: Prepare Your Repository

Ensure your repository contains:
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `.gitignore` - Exclude unnecessary files

### Step 2: Create Render Account

1. Visit [render.com](https://render.com)
2. Sign up for an account
3. Connect your GitHub repository

### Step 3: Configure render.yaml

The `render.yaml` file defines your infrastructure:

```yaml
services:
  - type: web
    name: blue-falcon
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: daphne -b 0.0.0.0 -p $PORT airport_sim.asgi:application
    envVars:
      - key: PYTHON_VERSION
        value: "3.12.0"
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DATABASE_ENGINE
        value: django.db.backends.postgresql
      - key: DATABASE_HOST
        fromDatabase:
          name: blue-falcon-db
          property: host
      - key: DATABASE_PORT
        fromDatabase:
          name: blue-falcon-db
          property: port
      - key: DATABASE_NAME
        fromDatabase:
          name: blue-falcon-db
          property: database
      - key: DATABASE_USER
        fromDatabase:
          name: blue-falcon-db
          property: user
      - key: DATABASE_PASSWORD
        fromDatabase:
          name: blue-falcon-db
          property: password
      - key: ALLOWED_HOSTS
        value: "blue-falcon.onrender.com,your-domain.com"
      - key: REDIS_URL
        fromService:
          type: redis
          name: blue-falcon-redis
          property: connectionString

databases:
  - name: blue-falcon-db
    databaseName: blue_falcon
    user: blue_falcon_user
    plan: starter

redis:
  - name: blue-falcon-redis
    plan: starter
    maxmemoryPolicy: noeviction
```

### Step 4: Deploy

1. In Render dashboard, click "New +"
2. Select "Blueprint"
3. Connect your GitHub repository
4. Render will read `render.yaml` and create services
5. Wait for deployment to complete (~5 minutes)

### Step 5: Run Migrations

After initial deployment:

```bash
# In Render dashboard, go to your web service
# Click "Shell" to open a terminal
python manage.py migrate
python manage.py createcachetable
python manage.py populate_demo_data  # Optional
```

### Step 6: Create Superuser

```bash
# In Render shell
python manage.py createsuperuser
```

### Step 7: Configure Domain (Optional)

1. Go to your web service settings
2. Click "Add Custom Domain"
3. Follow DNS configuration instructions
4. Update `ALLOWED_HOSTS` environment variable

### Step 8: Verify Deployment

Visit your deployed URL:
- Dashboard: `https://blue-falcon.onrender.com/`
- Admin: `https://blue-falcon.onrender.com/admin/`
- API: `https://blue-falcon.onrender.com/api/v1/`

---

## Traditional VPS Deployment

### Prerequisites

- Ubuntu 22.04 LTS server
- Root or sudo access
- Domain name pointing to server IP

### Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    nginx supervisor git curl
```

### Step 2: Create Application User

```bash
sudo useradd -m -s /bin/bash bluefalcon
sudo su - bluefalcon
```

### Step 3: Clone Repository

```bash
cd /home/bluefalcon
git clone <your-repository-url> blue-falcon
cd blue-falcon
```

### Step 4: Set Up Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure PostgreSQL

```bash
# Exit to root
exit

sudo -u postgres psql
```

```sql
CREATE DATABASE blue_falcon;
CREATE USER blue_falcon_user WITH PASSWORD 'secure-password-here';
ALTER ROLE blue_falcon_user SET client_encoding TO 'utf8';
ALTER ROLE blue_falcon_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE blue_falcon_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE blue_falcon TO blue_falcon_user;
\q
```

### Step 6: Configure Environment Variables

```bash
cd /home/bluefalcon/blue-falcon
nano .env
```

```env
SECRET_KEY=your-secret-key-here-use-django-get-secret-key
DEBUG=False
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=blue_falcon
DATABASE_USER=blue_falcon_user
DATABASE_PASSWORD=secure-password-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,<server-ip>
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email-user
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

Generate a secure SECRET_KEY:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Step 7: Run Migrations

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createcachetable
```

### Step 8: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 9: Configure Supervisor

Create `/etc/supervisor/conf.d/blue-falcon.conf`:

```ini
[program:blue-falcon-web]
command=/home/bluefalcon/blue-falcon/venv/bin/daphne -b 0.0.0.0 -p 8000 airport_sim.asgi:application
directory=/home/bluefalcon/blue-falcon
user=bluefalcon
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/blue-falcon/web.log
stderr_logfile=/var/log/blue-falcon/web-error.log
environment=DJANGO_SETTINGS_MODULE="airport_sim.settings"

[program:blue-falcon-qcluster]
command=/home/bluefalcon/blue-falcon/venv/bin/python manage.py qcluster
directory=/home/bluefalcon/blue-falcon
user=bluefalcon
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/blue-falcon/qcluster.log
stderr_logfile=/var/log/blue-falcon/qcluster-error.log
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start blue-falcon-web
sudo supervisorctl start blue-falcon-qcluster
```

### Step 10: Configure Nginx

Create `/etc/nginx/sites-available/blue-falcon`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Static files
    location /static/ {
        alias /home/bluefalcon/blue-falcon/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Daphne
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        limit_req zone=api burst=20 nodelay;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/blue-falcon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 11: Configure SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Auto-renewal is configured automatically. Test:
```bash
sudo certbot renew --dry-run
```

### Step 12: Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## Docker Deployment

### Step 1: Create Dockerfile

```dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "airport_sim.asgi:application"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 airport_sim.asgi:application
    volumes:
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=blue_falcon
      - POSTGRES_USER=blue_falcon
      - POSTGRES_PASSWORD=secure-password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U blue_falcon"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qcluster:
    build: .
    command: python manage.py qcluster
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

### Step 3: Create nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server web:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location /static/ {
            alias /app/staticfiles/;
        }

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### Step 4: Build and Run

```bash
# Build images
docker-compose build

# Run migrations
docker-compose run web python manage.py migrate

# Create superuser
docker-compose run web python manage.py createsuperuser

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Database Configuration

### PostgreSQL Settings

Add to `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
        'NAME': os.environ.get('DATABASE_NAME', 'blue_falcon'),
        'USER': os.environ.get('DATABASE_USER', 'blue_falcon'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'CONN_MAX_AGE': 600,  # Persistent connections
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

### Database Optimization

```sql
-- Run after deployment for better performance
ANALYZE;

-- Create additional indexes if needed
CREATE INDEX CONCURRENTLY idx_flight_status_date ON core_flight(status, scheduled_departure);
CREATE INDEX CONCURRENTLY idx_event_airport_timestamp ON core_eventlog(airport_id, timestamp);
```

### Database Backup

```bash
# PostgreSQL backup
pg_dump -h localhost -U blue_falcon_user blue_falcon > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U blue_falcon_user blue_falcon < backup_20260315.sql
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_ENGINE` | Database backend | `django.db.backends.postgresql` |
| `DATABASE_HOST` | Database host | `localhost` or RDS endpoint |
| `DATABASE_NAME` | Database name | `blue_falcon` |
| `DATABASE_USER` | Database user | `blue_falcon_user` |
| `DATABASE_PASSWORD` | Database password | `secure-password` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `example.com,www.example.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `EMAIL_HOST` | SMTP server | `None` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | `None` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `None` |
| `DEFAULT_FROM_EMAIL` | From address | `noreply@localhost` |
| `WEBSOCKET_MAX_CONNECTIONS_PER_USER` | WS connection limit | `10` |
| `WEBSOCKET_RATE_LIMIT` | WS message rate | `100/s` |

---

## Static Files

### WhiteNoise Configuration

WhiteNoise serves static files without needing a CDN:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### CDN Integration (Optional)

For better performance, use a CDN:

```python
# settings.py
STATIC_URL = 'https://cdn.your-domain.com/static/'

# Upload static files to CDN
aws s3 sync staticfiles/ s3://your-bucket/static/
```

---

## Background Tasks

### Django-Q2 Configuration

```python
# settings.py
Q_CLUSTER = {
    'name': 'BlueFalcon',
    'workers': 4,
    'recycle': 500,
    'timeout': 60,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'redis': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'schedules': {
        'check_scheduled_reports': {
            'func': 'core.tasks.check_scheduled_reports',
            'schedule': 3600,
        },
        'fetch_weather_data': {
            'func': 'core.weather_service.fetch_weather_for_all_airports',
            'schedule': 900,
        },
        'warm_cache': {
            'func': 'core.tasks.warm_cache',
            'schedule': 1800,
        },
    },
}
```

### Start Q Cluster

```bash
# Manual
python manage.py qcluster

# Supervisor (recommended)
sudo supervisorctl start blue-falcon-qcluster

# Docker
docker-compose up -d qcluster
```

### Monitor Tasks

Access Django-Q2 admin at `/admin/django_q/`

---

## SSL/HTTPS Configuration

### Render.com

SSL is automatic. Just configure your custom domain.

### Traditional VPS

Use Let's Encrypt:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

### Force HTTPS

```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## Monitoring & Logging

### Application Logs

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/application.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Health Check Endpoint

Create `core/views.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring."""
    try:
        # Check database
        connection.ensure_connection()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return JsonResponse({
        'status': 'healthy',
        'database': db_status,
        'timestamp': timezone.now().isoformat(),
    })
```

Add to `urls.py`:
```python
path('health/', health_check, name='health_check'),
```

### Uptime Monitoring

Configure external monitoring:
- **UptimeRobot:** Free tier, 5-minute checks
- **Pingdom:** Paid, advanced features
- **StatusCake:** Free tier available

---

## Backup & Recovery

### Automated Backups

#### Database Backup Script

Create `scripts/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="blue_falcon"
DB_USER="blue_falcon_user"

# Create backup
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Delete backups older than 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

#### Cron Job

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/bluefalcon/blue-falcon/scripts/backup_db.sh
```

### Backup Verification

```bash
# Test restore
gunzip -c db_backup_20260315.sql.gz | psql -h localhost -U blue_falcon_user blue_falcon_test
```

### Disaster Recovery Plan

1. **Database Failure:**
   - Restore from latest backup
   - Run migrations if needed

2. **Application Failure:**
   - Check logs
   - Restart services
   - Rollback to previous version

3. **Complete System Failure:**
   - Provision new server
   - Clone repository
   - Restore database
   - Configure environment
   - Start services

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Check logs:**
```bash
sudo supervisorctl status
sudo tail -f /var/log/blue-falcon/web.log
```

**Common causes:**
- Missing environment variables
- Database connection issues
- Port already in use

#### 2. Database Connection Errors

**Test connection:**
```bash
psql -h localhost -U blue_falcon_user blue_falcon
```

**Check PostgreSQL:**
```bash
sudo systemctl status postgresql
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Static Files Not Loading

**Collect static files:**
```bash
python manage.py collectstatic --noinput
```

**Check Nginx configuration:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. WebSocket Not Connecting

**Check Daphne is running:**
```bash
sudo supervisorctl status blue-falcon-web
```

**Check Nginx WebSocket proxy:**
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

#### 5. Background Tasks Not Running

**Check Q cluster:**
```bash
sudo supervisorctl status blue-falcon-qcluster
sudo tail -f /var/log/blue-falcon/qcluster.log
```

**Check Redis:**
```bash
redis-cli ping
sudo systemctl status redis
```

### Performance Issues

#### Slow Queries

```bash
# Enable query logging in settings.py
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['file'],
}

# Check logs
tail -f logs/application.log | grep "duration"
```

#### High Memory Usage

```bash
# Check memory
free -h

# Check process memory
ps aux --sort=-%mem | head
```

#### High CPU Usage

```bash
# Check CPU
top

# Check process CPU
ps aux --sort=-%cpu | head
```

---

*Last Updated: March 15, 2026*  
*Version: 1.0*
