# Django E-Commerce API

A RESTful e-commerce backend built with **Django** and **Django REST Framework**.

This project is being developed as a portfolio backend project with a focus on clean project structure, API development, authentication, database integration, automated testing, type checking, code quality, and containerized development.

> 🚧 **Project Status:** This project is currently under active development.

---

## Tech Stack

### Backend

* **Python 3.13+**
* **Django 6.1+**
* **Django REST Framework**
* **Django REST Framework SimpleJWT**
* **PostgreSQL 16**

### Development & Quality

* **pytest**
* **pytest-django**
* **pytest-cov**
* **mypy**
* **django-stubs**
* **djangorestframework-stubs**
* **Ruff**
* **pre-commit**

### Tooling & Infrastructure

* **uv** — Python package and project management
* **Docker**
* **Docker Compose**
* **Just** — development command runner
* **GitHub Actions** — Continuous Integration

---

## Features

The project is currently being developed around the following backend capabilities:

* RESTful API development with Django REST Framework
* User authentication and authorization
* JWT-based authentication
* PostgreSQL database integration
* Environment-based configuration
* Automated testing with pytest
* Code coverage reporting
* Static type checking with mypy
* Linting and formatting with Ruff
* Pre-commit hooks
* Dockerized development environment
* Continuous Integration with GitHub Actions

Additional e-commerce functionality is being implemented as the project progresses.

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .vscode/
│
├── docs/
│
├── src/
│   ├── django_ecommers/
│   ├── scripts/
│   └── manage.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── Dockerfile
├── compose.yml
├── justfile
├── mypy.ini
├── pyproject.toml
├── pytest.ini
├── ruff.toml
└── uv.lock
```

The application source code is kept under `src/`, while project documentation, CI configuration, and development tooling are maintained separately.

---

## Authentication

The API uses **JSON Web Tokens (JWT)** through Django REST Framework SimpleJWT.

JWT authentication is used to provide stateless authentication for API clients.

Authentication-related functionality is being developed as part of the project's user management system.

---

## Database

The project uses **PostgreSQL 16** as its primary database.

For local development, PostgreSQL is provided through Docker Compose.

The database configuration is controlled through environment variables:

```env
DB_NAME=mydb
DB_USER=myuser
DB_PASSWORD=mypass
DB_HOST=localhost
DB_PORT=5432
```

The PostgreSQL data directory is persisted through a Docker volume.

---

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
DJANGO_SETTINGS_MODULE=django_ecommers.config.settings
SECRET_KEY=django-ecommers-secret-key
DJANGO_ENV=development OR production
DB_NAME=mydb
DB_USER=myuser
DB_PASSWORD=mypass
DB_HOST=localhost
DB_PORT=5432
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password
```

> Do not commit real credentials or secret keys to version control.

> **Note:** The production environment uses a PostgreSQL database. Be sure to set the correct variables in the `.env` file.

---

## Getting Started

### Prerequisites

Make sure the following tools are installed:

* Python 3.13+
* Docker
* Docker Compose
* Git
* uv
* Just

### Clone the repository

```bash
git clone https://github.com/aliadde/DRF-E-Commers-API.git
cd DRF-E-Commers-API
```

### Create the environment file

```bash
cp .env.example .env
```

Update the values in `.env` if necessary.

---

## Install Dependencies

The project uses **uv** for dependency management.

Install the project dependencies with:

```bash
uv sync
```

For development dependencies:

```bash
uv sync --dev
```

---

## Run with Docker Compose

Start the application and PostgreSQL:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

To run the containers in the background:

```bash
docker compose up -d --build
```

To stop the services:

```bash
docker compose down
```

---

## Run Locally

Run Django's development server:

```bash
just runserver
```

Or directly:

```bash
uv run python src/manage.py runserver
```

---

## Database Migrations

Create migrations:

```bash
just makemigration
```

Apply migrations:

```bash
just migrate
```

Create admin user:

```bash
just manage seed_admin
```

You can also use Django's management command directly:

```bash
just manage migrate
```

---

## Testing

The project uses **pytest** and **pytest-django** for automated testing.

Run the test suite:

```bash
just pytest
```

or:

```bash
uv run pytest
```

### Test Coverage

Generate an HTML coverage report:

```bash
just coverage
```

The coverage report will be generated in:

```text
htmlcov/
```

---

## Code Quality

### Ruff

Format the project:

```bash
just format
```

Run Ruff directly:

```bash
uv run ruff check .
```

### Type Checking

The project uses **mypy** together with Django and Django REST Framework type stubs.

Run:

```bash
uv run mypy .
```

### Pre-commit

Install the pre-commit hooks:

```bash
uv run pre-commit install
```

Run them manually:

```bash
just pre-commit run --all-files
```

---

## Continuous Integration

The project uses **GitHub Actions** for CI.

The CI pipeline runs on pushes to `main` and `dev`, as well as pull requests.

The current pipeline performs:

```text
Checkout
   ↓
Set up Python 3.13
   ↓
Install dependencies with uv
   ↓
Ruff formatting
   ↓
Ruff linting
   ↓
mypy type checking
   ↓
pytest
   ↓
Docker image build
```

This helps ensure that formatting, linting, type checking, tests, and Docker builds are checked automatically before changes are integrated.

---

## Development Commands

The project uses **Just** to provide convenient development commands.

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `just runserver`        | Start the Django development server |
| `just migrate`          | Apply database migrations           |
| `just makemigration`    | Create migrations                   |
| `just django-shell`     | Open the Django shell               |
| `just pytest`           | Run tests                           |
| `just coverage`         | Run tests with coverage             |
| `just format`           | Format code with Ruff               |
| `just pre-commit`       | Run pre-commit                      |
| `just manage <command>` | Run a Django management command     |
| `just add <package>`    | Add a dependency using uv           |

---

## Docker

The application has a dedicated Docker image based on:

```text
python:3.13-slim
```

The Docker environment uses `uv` for dependency installation and runs Django inside the container.

Docker Compose provides the application and PostgreSQL services:

```text
┌──────────────────────┐
│      API Service     │
│  Django + DRF        │
│      :8000           │
└──────────┬───────────┘
           │
           │ PostgreSQL
           ▼
┌──────────────────────┐
│     PostgreSQL 16    │
│       :5432          │
└──────────────────────┘
```

---

## Architecture

The project follows a modular Django application structure under `src/`.

The main goals of the architecture are:

* Separation of Django applications
* Clear separation between configuration and application code
* Environment-based configuration
* Database-backed REST APIs
* Testable application components
* Static type checking
* Automated code quality checks
* Reproducible development environments

The architecture will continue to evolve as additional e-commerce functionality is implemented.

---

## Project Status

🚧 **Active Development**

The project is not yet considered feature-complete.

Current development focuses on building the core e-commerce backend and establishing a production-oriented development workflow.

### Implemented

* Django project setup
* Django REST Framework integration
* PostgreSQL integration
* JWT authentication infrastructure
* Docker development environment
* Docker Compose
* pytest / pytest-django
* Ruff
* mypy
* pre-commit
* GitHub Actions CI
* uv-based dependency management
* Just development commands

### In Progress

* E-commerce domain functionality
* User-related functionality
* Product-related functionality
* API expansion
* Additional automated tests
* Further backend infrastructure

### Planned

The roadmap will evolve as the core functionality is completed.

Potential future improvements include:

* Redis integration
* Background task processing (celery)
* Caching
* More advanced e-commerce workflows
* Improved API documentation
* Production deployment configuration
* Additional integration tests
* Performance and database optimization

---

## Why This Project?

This project is being developed to explore and practice real-world backend engineering concepts with Django and Django REST Framework.

The focus is not only on implementing API endpoints, but also on building a maintainable development workflow around the application, including:

* Automated testing
* Type checking
* Code quality enforcement
* Containerization
* Dependency management
* Continuous Integration
* Database-backed application development
* Authentication and authorization

---

## License

This project is currently a personal portfolio project.

A formal open-source license will be added if the project is released for external use.
