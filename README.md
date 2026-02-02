# Point Digital Marketing Manager – API

Django REST Framework API with JWT auth, permissions, viewset-based CRUD, and Swagger docs.

## Setup

```bash
cd point_digital_marketing_manager_api
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Database & superuser

```bash
python manage.py makemigrations api
python manage.py migrate
python manage.py createsuperuser
```

Use the superuser username/password for JWT login from the React frontend. Set the user's **role** to `ADMIN` in Django admin if needed.

## Run server

```bash
python manage.py runserver
```

- API base: `http://localhost:8000/api/`
- Swagger UI: `http://localhost:8000/api/docs/`
- JWT token: `POST /api/auth/token/` with `{"username","password"}`
- Refresh: `POST /api/auth/refresh/` with `{"refresh": "<refresh_token>"}`

## Endpoints

| Resource    | Path               | Auth   |
|------------|--------------------|--------|
| Users      | `/api/users/`      | JWT    |
| Me         | `/api/users/me/`   | JWT    |
| Settings   | `/api/settings/`   | JWT    |
| Quotations | `/api/quotations/` | JWT    |
| Vouchers   | `/api/vouchers/`   | JWT    |
| Contracts  | `/api/contracts/`  | JWT    |
| SMS Logs   | `/api/sms-logs/`   | JWT    |

This API is built for the **point-digital-marketing-manager-4** frontend (v4). It supports currency (IQD/USD), Twilio settings, exchange rate, quotation/voucher phone fields, voucher categories, contract status ACTIVE/ARCHIVED, and SMS log storage.

Write (create/update/delete) is restricted to users with role **ADMIN** for users and settings; other resources allow authenticated users to write.

## Connect React frontend (v4)

In the **point-digital-marketing-manager-4** project root, create `.env` or `.env.local`:

```
VITE_API_URL=http://localhost:8000
```

Then run the frontend (`npm run dev`) and log in with the Django user credentials. If `VITE_API_URL` is not set, the app runs in local-only mode (localStorage).
