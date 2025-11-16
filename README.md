# Sweetshop API

Sweetshop is a Django + Django REST Framework backend that manages user accounts and a sweets inventory with full CRUD, search, and inventory tracking. Customers can browse and purchase sweets, while admins can create, update, delete, and restock inventory with audit logs.

## Tech Stack

- Python 3.11+
- Django 5 + Django REST Framework
- SimpleJWT for authentication
- SQLite (default) – swap in Postgres/MySQL by updating `DATABASES` in `sweetshop/settings.py`.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd sweetshop
python manage.py migrate
python manage.py createsuperuser  # creates a user (role defaults to customer)
python manage.py shell <<'PY'
from accounts.models import User
User.create_admin_user(
	username="shop-admin",
	email="admin@example.com",
	password="supersecret",
)
PY
python manage.py runserver
```

> **Why the extra step?** Our custom `User` model defaults the `role` field to `customer`, even for superusers. The `User.create_admin_user` helper sets the role to `admin` while also toggling `is_staff`/`is_superuser` so DRF permissions recognise the account as an admin.

Environment variables (optional):

- `DJANGO_SECRET_KEY` – falls back to Django default, but set this in production.
- `DATABASE_URL` – use `django-environ` style URL if you move beyond SQLite.

## Running Tests

```bash
cd sweetshop
python manage.py test
```

## Authentication

The `accounts` app exposes registration/login endpoints under `/api/` and uses SimpleJWT access tokens. Include `Authorization: Bearer <token>` for any sweets endpoints.

Roles:

- `admin` – full CRUD + restock permissions.
- `customer` – list, retrieve, search, and purchase sweets.

## Sweets API Reference

All endpoints are prefixed with `/api/` and served by the `SweetViewSet`.

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| `POST` | `/api/sweets/` | Create a sweet | Admin only |
| `GET` | `/api/sweets/` | List sweets (supports `?category=` and `?search=`) | Authenticated users |
| `GET` | `/api/sweets/<id>/` | Retrieve single sweet | Authenticated users |
| `PUT/PATCH` | `/api/sweets/<id>/` | Update a sweet | Admin only |
| `DELETE` | `/api/sweets/<id>/` | Delete a sweet | Admin only |
| `GET` | `/api/sweets/search/?name=&category=&min_price=&max_price=` | Advanced search | Authenticated users |
| `POST` | `/api/sweets/<id>/purchase/` | Purchase a sweet (decrements stock, logs event) | Authenticated users |
| `POST` | `/api/sweets/<id>/restock/` | Restock a sweet (increments stock, logs event) | Admin only |

### Request + response contracts

| Endpoint | Expected request | Response shape |
| --- | --- | --- |
| `POST /api/sweets/` | JSON body<br>`{"name": "Nougat", "description": "Chewy", "price": "2.50", "category": "candy", "quantity_in_stock": 5}`<br>All fields required except `description`. | `201 Created` with the read-only `SweetSerializer` payload (id, name, description, price, category, quantity_in_stock). |
| `GET /api/sweets/` | Optional query params `?category=` or `?search=`. No body. | `200 OK` with list of sweets visible to the caller (customers only see items with stock). |
| `GET /api/sweets/<id>/` | No body. | `200 OK` with single sweet document; `404` if not found/authorized. |
| `PUT/PATCH /api/sweets/<id>/` | JSON body with any writable fields from the create payload. | `200 OK` with updated sweet. Validation errors return `400`. |
| `DELETE /api/sweets/<id>/` | No body. | `204 No Content` on success; `404` if missing. |
| `GET /api/sweets/search/` | Query params: `name`, `category`, `min_price`, `max_price`. All optional; numeric params must be valid decimals. | `200 OK` list of sweets matching filters. Bad decimal input returns `400` with `{"detail": "min_price and max_price must be valid numbers."}`. |
| `POST /api/sweets/<id>/purchase/` | JSON body `{"quantity": <positive int>}`. | `200 OK` with updated sweet. `400` if quantity invalid or exceeds stock. |
| `POST /api/sweets/<id>/restock/` | JSON body `{"quantity": <positive int>}`. Requires admin role. | `200 OK` with updated sweet. `400` for invalid quantity, `403` for non-admin. |

### Search Parameters

- `name` – fuzzy match on name/description.
- `category` – filters by enum value (e.g., `chocolate`, `candy`).
- `min_price` / `max_price` – decimal bounds.

Customers automatically see only sweets with `quantity_in_stock > 0`; admins see everything.

## Project Structure

```
requirements.txt
sweetshop/
├─ sweetshop/        # Django project configuration
├─ accounts/         # JWT auth, custom user model
└─ sweets/           # Inventory models, serializers, views, tests
```

## Inventory Events

Every purchase or restock creates an `InventoryEvent` record, giving admins a full audit trail of who changed stock, when, and by how much.

## Contributing

1. Fork/clone the repo
2. Create a feature branch
3. Add tests for new behavior
4. Run `python manage.py test`
5. Open a pull request describing your changes

---

## My AI Usage

This project used AI tools to accelerate development and improve productivity. Below is a short summary of which tools were used, how they were used, and reflections on their impact.

- Tools used:
	- GitHub Copilot — assisted with small code completions and boilerplate while editing views and serializers.
	- ChatGPT (OpenAI) — used interactively to draft and refactor the `SweetViewSet`, to design the API contract, to write tests, and to create README documentation.

- How AI was used:
	- I asked ChatGPT to propose a single unified `SweetViewSet` that handles customer and admin flows including purchase and restock actions.
	- Copilot suggested small, conventional snippets (e.g., serializer selection patterns, router usage) while authoring code in VS Code.
	- ChatGPT generated the README sections, including the API contract and the admin creation guidance.
	- I iterated on the AI-generated code, ran tests, and adjusted implementations to match project conventions and security checks.

- Reflection:
	- AI significantly reduced the time spent on repetitive boilerplate and helped surface common DRF patterns I might have otherwise reimplemented.
	- I treated AI outputs as suggestions: I reviewed, adapted, and tested everything before committing. This ensured correctness and alignment with existing project conventions.
    - I also use AI to learn about the framework and general information about how things works etc on the fly.
	- The combination of Copilot (inline completions) and ChatGPT (larger design + refactor suggestions) worked well: Copilot for small edits, ChatGPT for larger refactors and documentation drafts.

If you want me to expand this section with exact prompts or include a changelog of AI-assisted commits, I can add that as well.

## My AI Usage

Tools used
- GitHub Copilot (editor integration) — used to generate small code snippets, boilerplate, and quick patch suggestions.
- ChatGPT (conversational assistant) — used interactively to design the `SweetViewSet`, resolve routing decisions, craft tests, and produce documentation and README text.

How I used them
- I used Copilot for quick in-editor completions while writing serializers and small view helpers.
- I used ChatGPT to discuss design options (single viewset vs multiple views), to produce the consolidated `SweetViewSet` implementation, to refactor `sweets/urls.py` to a DRF router, and to write and improve tests and documentation.
- Where appropriate I asked the assistant to generate small patches that were applied to the repository and then ran the test suite locally to validate changes.

Reflection on impact
- AI sped up drafting and refactoring: it helped scaffold code and suggested concise patterns I could adapt. This reduced the initial boilerplate work and provided alternative implementations to consider.
- Human review remained essential: I reviewed and adjusted every AI suggestion to match project conventions and to ensure tests passed. The AI sometimes produced near-correct suggestions that required small corrections (naming, imports, or edge-case handling).
- Recommendation: Treat AI output as a capable assistant, not an authoritative source. Always run the test-suite and read through suggested changes before merging.
