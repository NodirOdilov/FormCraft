# FormCraft - Drag & Drop Form Builder SaaS

A production-grade drag-and-drop form builder SaaS application similar to Typeform and Google Forms. Build beautiful, interactive forms with conditional logic, analytics, submission management, webhooks, embeddable forms, and reusable templates.

## Features

- **Drag & Drop Form Builder** -- Visual form editor with a field palette, canvas, and configuration panel powered by react-dnd.
- **Custom Field Types** -- Text, email, number, textarea, select, multi-select, checkbox, radio, file upload, rating, date, phone, URL, and more.
- **Conditional Logic** -- Show or hide fields based on answers to previous questions using configurable rules.
- **Form Analytics** -- Track views, starts, completions, drop-off rates, average completion time, and per-field analytics.
- **Submission Management** -- View, filter, export, and manage form responses in a table with detail views.
- **Webhooks & Integrations** -- Send submission data to external services via configurable webhooks with retry logic.
- **Embeddable Forms** -- Embed forms on external websites via iframe or JavaScript snippet.
- **Form Templates** -- Browse and use pre-built form templates organized by category.
- **Workspaces & Plans** -- Multi-tenant workspaces with free, pro, and enterprise plan tiers.
- **Authentication** -- JWT-based authentication with registration, login, and token refresh.

## Tech Stack

| Layer         | Technology                                |
|---------------|-------------------------------------------|
| Backend       | Django 5.x, Django REST Framework         |
| Frontend      | React 18, Redux Toolkit, react-dnd        |
| Database      | PostgreSQL 16                             |
| Cache/Broker  | Redis 7                                   |
| Task Queue    | Celery 5                                  |
| Reverse Proxy | Nginx                                     |
| Containers    | Docker, Docker Compose                    |

## Project Structure

```
formcraft/
  backend/
    config/          # Django settings, URLs, WSGI, Celery
    apps/
      accounts/      # User, Workspace, Plan models
      forms/         # Form, FormField, ConditionalRule models
      submissions/   # Submission, SubmissionAnswer models
      templates_lib/ # FormTemplate, TemplateCategory models
      analytics/     # FormView, FormAnalytics models
      integrations/  # Webhook, Integration models
    utils/           # Pagination, exception handlers
  frontend/
    src/
      api/           # Axios API client modules
      components/    # React components (builder, fields, layout, etc.)
      pages/         # Page-level route components
      store/         # Redux store and slices
      hooks/         # Custom React hooks
      styles/        # Global CSS
  nginx/             # Nginx reverse proxy configuration
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed on your machine.

### 1. Clone and configure

```bash
git clone <repository-url> formcraft
cd formcraft
cp .env.example .env
# Edit .env with your own secrets and configuration
```

### 2. Build and run

```bash
docker compose up --build
```

This will start all services:

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost            |
| API      | http://localhost/api/       |
| Admin    | http://localhost/api/admin/ |

### 3. Create a superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

### 4. Run migrations (automatic on startup, but manual if needed)

```bash
docker compose exec backend python manage.py migrate
```

## Development

### Backend only

```bash
cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend only

```bash
cd frontend
npm install
npm start
```

### Running Celery worker

```bash
cd backend
celery -A config worker -l info
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` -- Register a new user
- `POST /api/auth/login/` -- Obtain JWT token pair
- `POST /api/auth/refresh/` -- Refresh access token

### Forms
- `GET/POST /api/forms/` -- List/create forms
- `GET/PUT/DELETE /api/forms/{id}/` -- Retrieve/update/delete a form
- `POST /api/forms/{id}/duplicate/` -- Duplicate a form
- `GET /api/forms/{slug}/public/` -- Public form endpoint (no auth)

### Submissions
- `GET /api/submissions/?form={id}` -- List submissions for a form
- `POST /api/submissions/` -- Create a submission (public)
- `GET /api/submissions/{id}/` -- Retrieve submission detail
- `GET /api/submissions/export/?form={id}` -- Export submissions as CSV

### Analytics
- `GET /api/analytics/{form_id}/` -- Get form analytics
- `POST /api/analytics/track-view/` -- Track a form view

### Templates
- `GET /api/templates/` -- List form templates
- `POST /api/templates/{id}/use/` -- Create a form from a template

### Integrations
- `GET/POST /api/integrations/webhooks/` -- List/create webhooks
- `POST /api/integrations/webhooks/{id}/test/` -- Send a test webhook

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT
