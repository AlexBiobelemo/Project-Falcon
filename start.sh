#!/bin/bash

# Project Falcon - Startup Script for Render
# This ensures Daphne (ASGI) is used instead of Gunicorn (WSGI)

set -e  # Exit on any error

echo "========================================="
echo "Project Falcon - Starting Deployment"
echo "========================================="
echo ""

# Show environment info
echo "Python version:"
python --version
echo ""

echo "Environment variables:"
echo "  DEBUG=$DEBUG"
echo "  PORT=$PORT"
echo "  DATABASE_ENGINE=$DATABASE_ENGINE"
echo "  DATABASE_NAME=$DATABASE_NAME"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput
echo "Migrations complete."
echo ""

# Collect static files with verbose output
echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity 2
echo "Static files collected."
echo ""

# Verify static files directory
echo "Static files directory contents:"
ls -la staticfiles/ || echo "Warning: staticfiles directory not found"
echo ""

# Check Django configuration
echo "Checking Django configuration..."
python manage.py check --deploy
echo ""

# Start Daphne
echo "Starting Daphne on port $PORT..."
echo "========================================="
exec daphne -b 0.0.0.0 -p $PORT airport_sim.asgi:application
