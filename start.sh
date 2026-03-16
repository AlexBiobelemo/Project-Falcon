#!/bin/bash

# Blue Falcon - Startup Script for Render
# This ensures Daphne (ASGI) is used instead of Gunicorn (WSGI)

set -e  # Exit on any error

echo "========================================="
echo "Blue Falcon - Starting Deployment"
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

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Static files collected."
echo ""

# Check Django configuration
echo "Checking Django configuration..."
python manage.py check --deploy
echo ""

# Start Daphne
echo "Starting Daphne on port $PORT..."
echo "========================================="
exec daphne -b 0.0.0.0 -p $PORT airport_sim.asgi:application
