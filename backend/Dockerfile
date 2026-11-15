# Imagen del backend: Python + librerías geoespaciales (GDAL, GEOS, PROJ).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends gdal-bin libgdal-dev binutils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN useradd --create-home app && mkdir -p /app/media /app/staticfiles && chown -R app /app
USER app

EXPOSE 8000
# Al arrancar: aplica migraciones, recoge estáticos del panel y sirve con gunicorn.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
