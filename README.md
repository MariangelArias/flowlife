# FlowLife

FlowLife is a Django application for personal task tracking, weekly mood tracking, and activity progress management.

## Features

- User authentication and registration
- Personal task dashboard
- Weekly mood tracking
- Activity progress tracking
- Admin-facing read-only overview of user tasks

## Requirements

- Python 3.11+
- Django and the packages listed in `requirements.txt`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from `.env.example` and fill in the values.
4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Start the development server:

   ```bash
   python manage.py runserver
   ```

## Environment variables

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DB_ENGINE`
- `DJANGO_DB_NAME`
- `DJANGO_DB_USER`
- `DJANGO_DB_PASSWORD`
- `DJANGO_DB_HOST`
- `DJANGO_DB_PORT`

## Security notes

- Do not commit `.env` files.
- Do not commit local database files such as `db.sqlite3`.
- Keep production secrets out of source control and inject them through environment variables.