# Django E-Commerce API

[CI](https://github.com/aliadde/DRF-E-Commers-API/actions/workflows/ci.yml) [Python](https://img.shields.io/badge/Python-3.13+-blue) [Django](https://img.shields.io/badge/Django-6.1+-092E20) [DRF](https://img.shields.io/badge/DRF-3.18+-red) [PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)

A RESTful e-commerce backend built with **Django** and **Django REST Framework**.
Users can register, browse products, fill a basket and place orders. Staff users manage the catalog.

The project is a portfolio backend with a strong focus on **correctness** (database transactions and row locking for stock), **testing** (400+ tests), **code quality** (Ruff, mypy, pre-commit, CI) and a **reproducible environment** (Docker Compose, uv).

> 🚧 **Status:** active development. The core shopping flow works end to end; see [Roadmap](#roadmap) for what is still missing.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Diagram](#database-diagram)
- [API Reference](#api-reference)
- [Architecture & Design Decisions](#architecture--design-decisions)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Development Commands](#development-commands)
- [Testing](#testing)
- [Code Quality & CI](#code-quality--ci)
- [Roadmap](#roadmap)

---

## Features

**Users & authentication**

- Custom user model (`AbstractBaseUser`) with unique username and email
- Registration, login and profile management (`/user/me/`)
- JWT authentication (SimpleJWT): 15-minute access token, 7-day refresh token with **rotation and blacklist**
- Password change (requires the current password)
- A basket is created automatically for every new user
- Delivery addresses (read endpoint implemented; create/update/delete are on the roadmap)

**Products & categories**

- Public product list and category list
- Staff-only create, update and delete
- Product list is **cached in Redis** (15 minutes) and invalidated on every write
- Categories are seeded by a data migration

**Basket**

- One basket per user
- Add an item, change its quantity, remove it
- Stock is validated against the available quantity

**Orders**

- Create an order from the basket in one atomic transaction
- Stock is deducted at order time; the basket is cleared afterwards
- Order statuses: `pending`, `paid`, `shipped`, `cancelled`
- Cancelling a pending order restores the stock
- Users can only see their own orders and addresses

**Admin**

- Django admin is enabled for all models
- `seed_admin` management command to create an admin user

---

## Tech Stack

| Area                 | Tools                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------- |
| Language / framework | Python 3.13+, Django 6.1+, Django REST Framework                                       |
| Authentication       | djangorestframework-simplejwt (with token blacklist)                                   |
| Database             | PostgreSQL 16 (production / Docker), SQLite (local development)                        |
| Cache                | Redis 7 via `django-redis`                                                             |
| Server               | Gunicorn                                                                               |
| Testing              | pytest, pytest-django, pytest-cov, httpx                                               |
| Quality              | Ruff (lint + format), mypy with django-stubs and djangorestframework-stubs, pre-commit |
| Tooling              | uv (dependencies), Just (task runner), Docker, Docker Compose, GitHub Actions          |

---

## Database Diagram

Database diagram

> The diagram is stored in `docs/database/diagram.jpeg`.
> The editable source is `docs/database/drawdb_file.ddb` (open it at [drawdb.vercel.app](https://www.drawdb.vercel.app/)).
> Table-by-table documentation: `docs/database/database_readme.md`.

**Main entities**

| Table          | Purpose                                       | Key relations                             |
| -------------- | --------------------------------------------- | ----------------------------------------- |
| `users`        | Accounts (custom user model)                  | has one basket, many addresses and orders |
| `addresses`    | Delivery addresses                            | belongs to a user                         |
| `categories`   | Product categories                            | has many products                         |
| `products`     | Catalog items with price and stock quantity   | belongs to a category                     |
| `baskets`      | One active basket per user                    | one-to-one with user                      |
| `basket_items` | Products and quantities in a basket           | basket → product                          |
| `orders`       | Placed orders with total and status           | belongs to a user and an address          |
| `order_items`  | Products, quantity and line total of an order | order → product                           |

---

## API Reference

Base URL (local): `http://localhost:8000`

Protected endpoints need the header `Authorization: Bearer <access_token>`.

### Users & auth

| Method | Endpoint                | Auth | Description                                          |
| ------ | ----------------------- | ---- | ---------------------------------------------------- |
| POST   | `/user/register/`       | –    | Register (`username`, `email`, `password`)           |
| POST   | `/user/login/`          | –    | Get `access` and `refresh` tokens                    |
| POST   | `/token/refresh/`       | –    | Get a new access token (refresh tokens rotate)       |
| GET    | `/user/me/`             | User | Current user profile                                 |
| PATCH  | `/user/me/`             | User | Update own profile                                   |
| POST   | `/user/reset_password/` | User | Change password (`current_password`, `new_password`) |
| GET    | `/user/address/<id>`    | User | Get one of your addresses                            |

### Products

| Method | Endpoint             | Auth  | Description            |
| ------ | -------------------- | ----- | ---------------------- |
| GET    | `/product/all/`      | –     | List products (cached) |
| GET    | `/product/category/` | –     | List categories        |
| POST   | `/product/`          | Staff | Create a product       |
| PATCH  | `/product/<id>/`     | Staff | Update a product       |
| DELETE | `/product/<id>/`     | Staff | Delete a product       |

### Basket

| Method | Endpoint             | Auth | Description                           |
| ------ | -------------------- | ---- | ------------------------------------- |
| GET    | `/basket/`           | User | Basket with its items                 |
| POST   | `/basket/`           | User | Add a product (`product`, `quantity`) |
| GET    | `/basket/items/<id>` | User | One basket item                       |
| PATCH  | `/basket/items/<id>` | User | Change an item's quantity             |
| DELETE | `/basket/items/<id>` | User | Remove an item                        |

### Orders

| Method | Endpoint      | Auth | Description                                              |
| ------ | ------------- | ---- | -------------------------------------------------------- |
| POST   | `/order/`     | User | Create an order from the basket (`address` = address id) |
| GET    | `/order/<id>` | User | Get one of your orders                                   |
| DELETE | `/order/<id>` | User | Cancel a pending order and restore stock                 |

### Example flow

```bash
# 1. Register
curl -X POST http://localhost:8000/user/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "email": "ali@example.com", "password": "S0me-strong-pass"}'

# 2. Log in
curl -X POST http://localhost:8000/user/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "password": "S0me-strong-pass"}'
# -> {"refresh": "...", "access": "..."}

# 3. Add a product to the basket
curl -X POST http://localhost:8000/basket/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"product": 1, "quantity": 2}'

# 4. Place the order
curl -X POST http://localhost:8000/order/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"address": 1}'
# -> {"detail": "Order created successfully.", "order_id": 1}
```

---

## Architecture & Design Decisions

- **Modular monolith.** Each domain (`users`, `products`, `baskets`, `orders`) is its own Django app with its own models, serializers, views, URLs, admin and tests.
- **Settings split by environment.** `config/settings/` has `base`, `development` and `production`. `DJANGO_ENV` selects which one is used.
- **Stock consistency under concurrency.** Order creation, basket updates and order cancellation run inside `transaction.atomic()` and lock the affected product rows with `select_for_update()`, so two simultaneous requests cannot oversell the same stock.
- **Ownership checks.** Basket, order and address queries are always filtered by the authenticated user.
- **Stateless auth with revocable refresh tokens.** Refresh tokens rotate and old ones are blacklisted.
- **Caching.** The public product list is cached and the cache key is deleted on create, update and delete.
- **Typed code.** mypy runs in CI with Django and DRF stubs.

---

## Project Structure

```
.
├── .github/workflows/ci.yml     # CI pipeline
├── docs/
│   ├── database/                # diagram, editable .ddb file, table docs
│   ├── development.md
│   └── project-describe.md
├── src/
│   ├── manage.py
│   ├── scripts/                 # helper scripts
│   ├── tests/integration/       # end-to-end API tests per domain
│   └── django_ecommers/
│       ├── config/              # settings (base/development/production), urls, wsgi, asgi
│       └── apps/
│           ├── users/           # auth, profile, addresses
│           ├── products/        # catalog and categories
│           ├── baskets/         # basket and basket items
│           └── orders/          # orders and order items
├── Dockerfile
├── compose.yml                  # api + postgres + redis
├── entrypoint.sh                # migrate + create superuser, then start the server
├── justfile                     # development commands
├── pyproject.toml / uv.lock
├── pytest.ini / mypy.ini / ruff.toml / .pre-commit-config.yaml
└── .env.example
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- [Just](https://github.com/casey/just)
- Docker and Docker Compose
- Git

### Option 1: Docker Compose (API + PostgreSQL + Redis)

```bash
git clone https://github.com/aliadde/DRF-E-Commers-API.git
cd DRF-E-Commers-API
cp .env.example .env
```

Edit `.env` for Docker:

```env
DJANGO_ENV=production
DB_HOST=db
```

> `DB_HOST` must be `db` (the Compose service name) inside Docker. `localhost` only works when you run Django on your own machine.

Then start everything:

```bash
docker compose up --build
```

On start, the container applies migrations and creates the superuser from the `DJANGO_SUPERUSER_*` variables. The API is available at `http://localhost:8000` and the admin at `http://localhost:8000/admin/`.

Useful commands:

```bash
docker compose up -d --build   # run in the background
docker compose down            # stop
docker compose down -v         # stop and delete the database volume
```

### Option 2: Run locally (SQLite + Redis)

In development mode (`DJANGO_ENV=development`, the default) Django uses SQLite and expects Redis on `127.0.0.1:6379` for caching.

```bash
cp .env.example .env
uv sync --dev
docker compose up -d redis      # Redis for the cache
just migrate
just manage seed_admin          # optional: create an admin user
just runserver
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

| Variable                                             | Description                                                  | Example                           |
| ---------------------------------------------------- | ------------------------------------------------------------ | --------------------------------- |
| `DJANGO_SETTINGS_MODULE`                             | Settings entry point                                         | `django_ecommers.config.settings` |
| `SECRET_KEY`                                         | Django secret key (use a long random value in production)    | –                                 |
| `DJANGO_ENV`                                         | `development` (SQLite) or `production` (PostgreSQL)          | `development`                     |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD`                | PostgreSQL credentials                                       | `mydb` / `myuser` / `mypass`      |
| `DB_HOST`                                            | `localhost` when running locally, `db` inside Docker Compose | `db`                              |
| `DB_PORT`                                            | PostgreSQL port                                              | `5432`                            |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | Admin created automatically in Docker                        | –                                 |

> Never commit a real `.env` file or real secrets.

---

## Development Commands

Commands are defined in the `justfile`:

| Command                  | Description                                          |
| ------------------------ | ---------------------------------------------------- |
| `just runserver`         | Start the development server                         |
| `just migrate`           | Apply migrations                                     |
| `just makemigration`     | Create migrations                                    |
| `just manage <cmd>`      | Run any `manage.py` command                          |
| `just django-shell`      | Open the Django shell                                |
| `just pytest`            | Run the tests                                        |
| `just coverage`          | Run tests with an HTML coverage report in `htmlcov/` |
| `just format`            | Format with Ruff                                     |
| `just lint`              | Lint with Ruff and apply safe fixes                  |
| `just pre-commit <args>` | Run pre-commit                                       |
| `just add <package>`     | Add a dependency with uv                             |
| `just cleaner`           | Remove cache files and folders                       |

---

## Testing

The test suite contains **400+ tests**, split into:

- **Unit tests** per app (models, serializers, services, views) in `apps/<app>/tests/`
- **Integration tests** for full API flows in `src/tests/integration/` (registration, login, JWT, profile, products, basket, orders, order cancellation)

```bash
just pytest                 # run everything
just pytest -k basket       # run a subset
just coverage               # coverage report -> htmlcov/index.html
```

Tests that exercise the product cache need Redis running (`docker compose up -d redis`).

---

## Code Quality & CI

Run locally:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pre-commit install        # run the checks automatically on commit
```

GitHub Actions (`.github/workflows/ci.yml`) runs on pushes to `main` and `dev` and on pull requests, with PostgreSQL and Redis service containers:

```
Checkout → Python 3.13 → uv sync → Ruff format → Ruff lint → mypy → pytest → Docker build
```

---

## Roadmap

**Next up**

- [ ] Address create, update and delete endpoints
- [ ] List a user's orders
- [ ] Admin endpoint to move orders through `paid` and `shipped`
- [ ] Payment integration (mock first, then a real provider)
- [ ] Interactive API docs (OpenAPI / Swagger via `drf-spectacular`)
- [ ] Pagination, filtering and search for products

**Later**

- [ ] Switch money fields to `DecimalField`
- [ ] Soft delete for products and price/name snapshot in order items
- [ ] Rate limiting for login and registration
- [ ] Product images
- [ ] Celery for background tasks (e.g. order emails)
- [ ] Production hardening: security headers, structured logging, health check endpoint

---

## License

This is a personal portfolio project. A license will be added if it is released for external use.
