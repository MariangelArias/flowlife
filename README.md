# FlowLife

FlowLife es una aplicación Django para gestión de tareas personales, seguimiento semanal del estado de ánimo y control del progreso de actividades.

## Funcionalidades

- Registro e inicio de sesión de usuarios
- Panel personal de tareas
- Seguimiento semanal del estado de ánimo
- Seguimiento del progreso de actividades
- Vista de solo lectura para administradores sobre las tareas de los usuarios

## Requisitos

- Python 3.11 o superior
- Django y los paquetes listados en `requirements.txt`

## Instalación

1. Crea y activa un entorno virtual.
2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Crea un archivo `.env` a partir de `.env.example` y completa los valores.
4. Ejecuta las migraciones:

   ```bash
   python manage.py migrate
   ```

5. Inicia el servidor de desarrollo:

   ```bash
   python manage.py runserver
   ```

## Variables de entorno

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DB_ENGINE`
- `DJANGO_DB_NAME`
- `DJANGO_DB_USER`
- `DJANGO_DB_PASSWORD`
- `DJANGO_DB_HOST`
- `DJANGO_DB_PORT`

## Notas de seguridad

- No subas archivos `.env`.
- No subas bases de datos locales como `db.sqlite3`.
- Mantén los secretos de producción fuera del control de versiones y cárgalos mediante variables de entorno.