#!/bin/sh
# Arranque en Render: migraciones, estáticos, datos de demo opcionales y gunicorn.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# SEMBRAR_DEMO=1          -> carga el demo solo si la base está vacía
# SEMBRAR_DEMO=reiniciar  -> borra y recarga el demo (horas de reportes actualizadas)
case "$SEMBRAR_DEMO" in
  1|true|True) python manage.py sembrar_demo ;;
  reiniciar)   python manage.py sembrar_demo --reiniciar ;;
esac

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 60 --access-logfile -