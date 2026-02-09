# Tuition Management Result System

Production-ready starter for a small tuition center to upload results, publish exams, and let parents view report cards.

## Stack

- **Backend:** Django + Django REST Framework + JWT
- **Database:** PostgreSQL
- **Frontend:** React (Vite) + Tailwind
- **Deployment:** Docker Compose
- **RBAC:** Custom Role/Permission tables

## Quick Start (Docker)

```bash
docker compose up --build
```

### Initial setup

```bash
# run migrations and create admin

docker compose exec backend python manage.py migrate

docker compose exec backend python manage.py createsuperuser

docker compose exec backend python manage.py seed_roles
```

## Environment

Copy `.env.example` to `.env` and adjust values if needed.

## Backend Features

- Role-based access control (Role, Permission, RolePermission, UserRole)
- Results upload (single + bulk)
- Publish exams (locks results)
- PDF report cards (ReportLab)
- Analytics endpoint

## API Endpoints

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET/POST /api/students`
- `GET/POST /api/classes`
- `GET/POST /api/subjects`
- `GET/POST /api/exams`
- `POST /api/exams/{id}/publish`
- `POST /api/results/upload`
- `POST /api/results/bulk-upload`
- `GET /api/results/student/{student_id}?exam_id=`
- `GET /api/results/class/{class_id}?exam_id=`
- `GET /api/report-card/{student_id}/{exam_id}/pdf`
- `GET /api/analytics/class/{class_id}?exam_id=`

## Frontend

Pages included:

- Login
- Dashboard
- Students CRUD
- Classes
- Subjects
- Upload Results
- Publish Results
- Parent Result View
- Class Result Sheet
- Analytics

## Development Notes

- Django settings are in `backend/tuition_management/settings.py`.
- Core API logic lives in `backend/core/`.
- React app lives in `frontend/`.
