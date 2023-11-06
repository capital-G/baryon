#!/bin/sh

#!/bin/sh

echo "Apply database migrations";
python manage.py migrate;

echo "Check if SuperUser exists";
if [ -z "$DJANGO_SU_USER" ];
then
    echo "No Superuser given";
else
    python_script="from django.contrib.auth import get_user_model; User = get_user_model();  User.objects.create_superuser('"$DJANGO_SU_USER"', '', '"$DJANGO_SU_PASS"') if not User.objects.filter(username='"$DJANGO_SU_USER"').exists() else print('Superuser exists already')";
    python manage.py shell --command "$python_script";
fi;

echo "Collect static files"

python manage.py collectstatic --noinput > /dev/null

echo "Starting uvicorn production server";
uvicorn \
    baryon.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
