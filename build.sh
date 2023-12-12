#!/bin/bash

echo "Building Project..."
python -m pip install -r requirements.txt

echo "Make migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collect static files..."
python manage.py collectstatic --noinput --clear