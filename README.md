# Foodgram

## Описание
Foodgram — веб-сервис для публикации и управления кулинарными рецептами. Возможности платформы включают:

Создание и сохранение авторских рецептов.

Просмотр и использование рецептов других пользователей.

Добавление понравившихся рецептов в избранное.

Формирование и скачивание списка необходимых продуктов для приготовления.

---

## Запуск

### Использование PostgreSQL (по умолчанию)
Для старта проекта с базой данных PostgreSQL выполните следующую команду:
```bash
docker compose up
```

### Использование SQLite
Если вы хотите использовать SQLite:

1. В файле .env укажите USE_SQLITE=1.
2. Запустите контейнеры с помощью:
   ```bash
   docker compose up
   ```

### Универсальные действия
1. Выполните миграции базы данных:
   ```bash
   docker exec foodgram-backend python manage.py migrate
   ```
2. Импортируйте список ингредиентов:
   ```bash
   docker exec foodgram-backend python manage.py import_ingredients_from_json
   ```
3. Добавьте данные вручную через административную панель по адресу localhost.
   
> **Важно:** Автоматическое применение миграций отключено, чтобы сохранить контроль над структурой БД.

### Запуск без Docker (тестовая среда)

Установите USE_SQLITE=1 в .env.

1. В каталоге backend (Python 3.10 должен быть установлен):
```bash
   python -m venv venv
   source venv/bin/activate # Linux
   venv\Scripts\activate # Windows
   pip install -r requirements.txt
   python manage.py migrate
   mkdir -p backend_static/static/
   python manage.py collectstatic --noinput
   python manage.py import_ingredients_from_json
   gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi
```

2. В каталоге frontend (требуется node версии 21.7.1):
```bash
   npm install
   npm run build
```
Создайте директорию и переместите туда статические файлы из backend и frontend. 

3. В директории nginx (nginx должен быть установлен):

Укажите в конфигурации localhost вместо имени контейнера и 
скорректируйте пути к статикам и медиафайлам согласно созданной структуре.

Для локального доступа к документации добавьте:

```
    location /docs/ {
        root /PATH TO PROJECT/foodgram-st;
        try_files $uri $uri/redoc.html;
    }
```

Затем выполните команды:

```bash
   cp nginx.conf /etc/nginx/conf.d/default.conf
   sudo systemctl restart nginx 
```

Сайт будет доступен по адресу - **http://localhost/**
Документация - **http://localhost/docs/**

---

Стек технологий
- Backend
  - Python 3.10
  - Django 5.1
  - Django REST Framework 3.15
  - PostgreSQL (по умолчанию) / SQLite (альтернативный режим)
  - Gunicorn
  - Djoser
- Frontend
  - React
  - Redux
  - TypeScript
- Docker, Docker Compose
- Nginx

---

Автор<br>
Шакиров Тимур<br>
Telegram @rixittt<br>
