FROM python:3.10

WORKDIR /app


COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN mkdir -p /backend_static/static/

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi"]