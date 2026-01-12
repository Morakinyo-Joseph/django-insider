# django-insider (MVP with Celery, React)


- `backend/`: Django example project + `insider` reusable app
- `frontend/`: React + Vite admin UI that builds into the Django app's static files

## Quick start

1. Create and activate a virtualenv, then install backend deps:

   ```bash
   cd backend
   pip install -e .
   # or: pip install Django djangorestframework channels channels-redis celery redis
   ```

2. Run migrations and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. Optional: Start Redis (for Channels + Celery) and Celery worker: 

   ```bash
   redis-server
   celery -A config worker -l INFO
   ```

4. Build the React frontend:

   ```bash
   cd ../frontend
   npm install
   npm run build
   ```

5. Run Django dev server:

   ```bash
   cd ../backend
   python manage.py runserver
   ```

6. Log in to Django admin as a staff user, ensure you are logged in on the same origin.

7. Open the React UI at `/insider`
