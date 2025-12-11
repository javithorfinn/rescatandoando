#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Ensure a specific superuser exists/updated using env vars
# Set ADMIN_USERNAME and ADMIN_PASSWORD in Render Environment, then Manual Deploy.
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
	python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u,created=User.objects.get_or_create(username='$ADMIN_USERNAME', defaults={'is_staff':True,'is_superuser':True,'email':'admin@example.com'}); u.is_staff=True; u.is_superuser=True; u.set_password('$ADMIN_PASSWORD'); u.save(); print('Superuser ensured:', u.username, 'created:', created)"
else
	echo "Skipping explicit superuser ensure: set ADMIN_USERNAME and ADMIN_PASSWORD to enable"
fi
