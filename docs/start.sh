#!/bin/bash

# Project Falcon - Startup Script for Render
# This ensures Daphne (ASGI) is used instead of Gunicorn (WSGI)

echo "Starting Project Falcon with Daphne (ASGI server)..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Daphne
echo "Starting Daphne on port $PORT..."
exec daphne -b 0.0.0.0 -p $PORT airport_sim.asgi:application
