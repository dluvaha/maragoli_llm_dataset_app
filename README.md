# Maragoli LLM Dataset Collection System

A production-ready Django web application for collecting, managing, and exporting Maragoli-English parallel corpus data for training a Maragoli Large Language Model (LLM).

## Features

- **Side-by-side Display**: Maragoli text and English translations displayed side-by-side
- **Excel Bulk Import**: Upload `.xlsx` files with preview and validation before import
- **Duplicate Detection**: SHA-256 hash-based duplicate prevention
- **JSON Export**: Three export formats optimized for different LLM training pipelines
- **Validation Workflow**: Mark entries as validated for quality control
- **Category Organization**: Organize datasets by topic (Greetings, Proverbs, etc.)
- **Search & Filter**: Full-text search, category filter, validation status filter
- **Import History**: Full audit trail of all import operations

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/dluvaha/maragoli_llm_dataset_app.git
cd maragoli_llm_dataset_app

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations (creates all database tables)
python manage.py migrate

# 5. Load sample data (41 Maragoli translations + admin user)
#    Admin login: admin / admin123
python manage.py loaddata datasets/fixtures/initial_data.json
python manage.py loaddata datasets/fixtures/admin_user.json

# 6. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` and log in with your superuser credentials.

## Project Structure

```
maragoli_dataset/
├── maragoli_llm/            # Django project settings
│   ├── settings.py          # Configuration (database, static files, etc.)
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI entry point
├── datasets/                # Main application
│   ├── models.py            # Database models (MaragoliDataset, DatasetCategory, ImportHistory)
│   ├── views.py             # Views (CRUD, import/export, statistics)
│   ├── forms.py             # Django forms
│   ├── admin.py             # Django admin configuration
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py # Database seeder
│   └── migrations/
├── templates/
│   ├── base.html            # Base template with Tailwind CSS + navigation
│   └── datasets/
│       ├── dashboard.html   # Dashboard with statistics
│       ├── dataset_list.html        # Side-by-side dataset listing
│       ├── dataset_form.html        # Create/Edit form
│       ├── import_upload.html       # Excel upload page
│       ├── import_preview.html      # Import preview with validation
│       ├── export_page.html         # Export options (3 formats)
│       ├── category_list.html       # Category management
│       └── category_form.html       # Category create/edit
├── static/
│   ├── css/
│   └── js/
├── media/                   # Uploaded files
├── logs/                    # Application logs
├── db.sqlite3               # SQLite database (development)
├── manage.py
├── requirements.txt
└── sample_import.xlsx       # Sample Excel file for testing import
```

## Excel Import Format

Your Excel file must have these columns:

| maragoli_text | english_text | category (optional) | source (optional) | confidence_score (optional) |
|---|---|---|---|---|
| Murembe | How are you? | Greetings | Community elder | 1.0 |
| Igulu riamabwerere | The sky is cloudy | Nature | Field researcher | 0.9 |

- `maragoli_text` and `english_text` are **required**
- Column names are case-insensitive; spaces are handled automatically
- Duplicates are detected via SHA-256 hashing and skipped

## JSON Export Formats

### 1. Standard Parallel Corpus (default)
```json
{
  "metadata": {"language_pair": "maragoli-english"},
  "translations": [
    {"maragoli": "...", "english": "...", "category": "...", "confidence": 1.0}
  ]
}
```
**Best for**: General NLP tasks, machine translation baseline, LM pre-training.

### 2. Instruction-Response (Alpaca-style)
```json
{
  "data": [
    {
      "instruction": "Translate the following Maragoli text to English: ...",
      "input": "",
      "output": "..."
    }
  ]
}
```
**Best for**: Supervised fine-tuning (SFT) of instruction-following models.

### 3. Conversational (ChatML)
```json
{
  "conversations": [
    {
      "messages": [
        {"role": "system", "content": "You are a Maragoli-English translator."},
        {"role": "user", "content": "Murembe"},
        {"role": "assistant", "content": "How are you?"}
      ]
    }
  ]
}
```
**Best for**: Chat/conversational model training, OpenAI fine-tuning API.

## Industry Best Practices for Production Deployment

### 1. Database
- **Development**: SQLite (included, zero config)
- **Production**: PostgreSQL (recommended) or MySQL
- Set via environment variable: `DB_ENGINE=django.db.backends.postgresql`
- Enable connection pooling with `CONN_MAX_AGE=60`
- Use `django-db-geventpool` for async deployments

### 2. Security
```python
# In production settings:
DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Never hardcode
ALLOWED_HOSTS = ['yourdomain.com']

# HTTPS only
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com")
```

### 3. Deployment with Gunicorn + Nginx
```bash
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn maragoli_llm.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    client_max_body_size 10M;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
EXPOSE 8000
CMD ["gunicorn", "maragoli_llm.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 5. Environment Variables
```bash
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=maragoli_llm
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Recommended Project Enhancements

| Enhancement | Tool/Library | Purpose |
|---|---|---|
| API Layer | Django REST Framework | REST API for mobile apps and integrations |
| Background Tasks | Celery + Redis | Async import processing for large files |
| Real-time Updates | Django Channels | WebSocket notifications on import completion |
| Caching | Redis | Cache dashboard stats and frequent queries |
| Monitoring | Sentry | Error tracking and performance monitoring |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Testing | pytest + factory_boy | Unit and integration tests |
| Code Quality | Ruff / Black | Linting and code formatting |
| Rate Limiting | django-ratelimit | Protect import/export endpoints |

### 7. For LLM Training Pipeline
- Export validated data only for highest quality training
- Use instruction-response format for fine-tuning on models like LLaMA, Mistral
- Consider using [HuggingFace Datasets](https://huggingface.co/docs/datasets/) format for wider compatibility
- Minimum 10,000+ translation pairs recommended for meaningful LLM training
- Blend with back-translation and synthetic data augmentation

## Default Login

- **Username**: `admin`
- **Password**: `admin123`
- **URL**: `http://127.0.0.1:8000/admin/`

## License

MIT License - Free for personal, educational, and commercial use.
