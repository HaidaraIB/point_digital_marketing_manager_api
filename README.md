# Point Digital Marketing Manager – API

Point Digital Marketing Manager API is a Django REST Framework backend for managing a digital marketing agency. It provides JWT authentication, role-based access (ADMIN / ACCOUNTANT), and full CRUD for quotations, vouchers, contracts, freelancers, and agency settings, with optional SMS sending via Twilio. The API is designed to work with the **point-digital-marketing-manager-4** (v4) React frontend. Error messages and permission labels are partly in Arabic.

## Key Features

*   **User and Role Management**: Custom user model with roles **ADMIN** (مدير نظام) and **ACCOUNTANT** (محاسب). Endpoint `/api/users/me/` returns the current authenticated user for the frontend after JWT login.
*   **Agency Settings**: Single-record settings for the agency: name, logo (URL or base64), address, phone, email, quotation terms, Twilio configuration (Account SID, Auth Token, sender number/name, enabled flag), and default exchange rate (IQD/USD).
*   **Quotations**: Client name and phone, date, line items (description, price, quantity, optional currency), total, currency (IQD/USD), status (PENDING, ACCEPTED, REJECTED), and note. Custom action `set_status` to update status (ADMIN only).
*   **Vouchers (قبض / صرف)**: Type (RECEIPT/PAYMENT), amount, currency, date, party name and phone, and category (salary, daily, general, voucher, owner withdrawal, freelance). ACCOUNTANT cannot view or create owner-withdrawal vouchers; ADMIN has full CRUD.
*   **Contracts**: Two parties, subject, total value, currency, status (ACTIVE, ARCHIVED), and linked clauses. Full CRUD with clause ordering.
*   **Freelancers and Freelance Work**: Photographers and editors (مصور / مونتير) with linked work items (description, date, price, currency, paid flag). Custom action `mark-paid` to link selected works to a voucher when paying freelancers.
*   **SMS Sending (Twilio)**: Endpoint `POST /api/send-sms/` sends SMS using agency Twilio settings. Credentials stay on the server to avoid CORS and client exposure.
*   **SMS Logs**: Store each send attempt (recipient, body, status, timestamp, error) for auditing.
*   **Permissions**: Full read/write on Users and Settings for ADMIN only. Other resources: ACCOUNTANT can read and add; ADMIN has full CRUD. Accountant cannot update or delete quotations, vouchers, contracts, freelancers, or freelance works.
*   **API Documentation**: Interactive Swagger UI via drf-spectacular at `/api/docs/`.

## Technology Stack & Architecture

The API is built with Django and Django REST Framework and follows a standard ViewSet-based design.

*   **Framework**: Django + Django REST Framework (viewset-based CRUD, pagination).
*   **Authentication**: Simple JWT (access + refresh tokens, refresh rotation). Token obtain at `/api/auth/token/`, refresh at `/api/auth/refresh/`.
*   **Documentation**: drf-spectacular and drf-spectacular-sidecar for OpenAPI schema and Swagger UI.
*   **Database**: SQLite by default (PostgreSQL can be used in production; see DEPLOY.md).
*   **Configuration**: python-dotenv for `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `ALLOWED_API_KEYS`, and CORS-related variables. Do not commit `.env`.
*   **CORS**: django-cors-headers with support for `Authorization` and `X-API-Key` headers (for frontend and optional API-key middleware).
*   **SMS**: Twilio; credentials are stored in agency settings and used only on the server for `send-sms`.
*   **Deployment**: Gunicorn (see [DEPLOY.md](DEPLOY.md) for Linux/VPS setup with Nginx, systemd, and optional HTTPS).

## Project Structure

```
point_digital_marketing_manager_api/
├── api/                    # Main API application
│   ├── models.py           # User, AgencySettings, Quotation, Voucher, Contract, Freelancer, FreelanceWork, SMSLog
│   ├── views.py            # ViewSets and send_sms action
│   ├── serializers.py      # Serializers for all models
│   ├── urls.py             # Router registration and send-sms route
│   ├── permissions.py     # IsAdminUser, IsAccountantReadAddOrAdmin
│   ├── admin.py            # Django admin registration
│   ├── middleware.py       # Optional API key middleware
│   └── migrations/
├── point_digital_marketing_manager_api/
│   ├── settings.py         # Django, DRF, JWT, CORS settings
│   ├── urls.py             # admin, api/, auth/token, auth/refresh, schema, docs
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── requirements.txt
├── .env                    # Not committed: SECRET_KEY, DEBUG, ALLOWED_HOSTS, ALLOWED_API_KEYS, CORS_*
└── README.md
```

## Setup and Installation

1.  **Clone the repository** (if applicable):
    ```sh
    git clone <your-repo-url>
    cd point_digital_marketing_manager_api
    ```

2.  **Create a virtual environment and install dependencies**:
    ```sh
    python -m venv .venv
    .venv\Scripts\activate   # Windows
    # source .venv/bin/activate  # Linux/macOS
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file** in the project root (do not commit it). Example:
    ```
    SECRET_KEY=your-long-random-secret-key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    ALLOWED_API_KEYS=optional-comma-separated-keys
    CORS_ALLOW_ALL_ORIGINS=True
    CORS_ALLOW_CREDENTIALS=True
    ```
    Generate a secure `SECRET_KEY` with: `python -c "import secrets; print(secrets.token_urlsafe(50))"`

4.  **Database and superuser**:
    ```sh
    python manage.py makemigrations api
    python manage.py migrate
    python manage.py createsuperuser
    ```
    Use the superuser username and password for JWT login from the frontend. In Django admin, set the user's **role** to **ADMIN** if you need full access to users and settings.

5.  **Run the server**:
    ```sh
    python manage.py runserver
    ```
    *   API base: `http://localhost:8000/api/`
    *   Swagger UI: `http://localhost:8000/api/docs/`
    *   JWT token: `POST /api/auth/token/` with `{"username": "...", "password": "..."}`
    *   Refresh: `POST /api/auth/refresh/` with `{"refresh": "<refresh_token>"}`

6.  **Connect the React frontend (v4)**  
    In the **point-digital-marketing-manager-4** project root, create `.env` or `.env.local`:
    ```
    VITE_API_URL=http://localhost:8000
    ```
    Then run the frontend (`npm run dev`) and log in with the Django user credentials. If `VITE_API_URL` is not set, the app can run in local-only mode (e.g. localStorage).

## Endpoints

| Resource       | Path                      | Auth | Notes |
|----------------|---------------------------|------|--------|
| Users          | `/api/users/`             | JWT  | ADMIN: full CRUD; others: list, retrieve, create |
| Me             | `/api/users/me/`          | JWT  | Current user |
| Settings       | `/api/settings/`          | JWT  | ADMIN only |
| Quotations     | `/api/quotations/`        | JWT  | ACCOUNTANT: read + add; ADMIN: full CRUD; `set_status` admin only |
| Vouchers       | `/api/vouchers/`          | JWT  | ACCOUNTANT: read + add (no owner withdrawal); ADMIN: full CRUD |
| Contracts      | `/api/contracts/`         | JWT  | ACCOUNTANT: read + add; ADMIN: full CRUD |
| Freelancers    | `/api/freelancers/`       | JWT  | ACCOUNTANT: read + add; ADMIN: full CRUD |
| Freelance Works| `/api/freelance-works/`   | JWT  | ACCOUNTANT: read + add; ADMIN: full CRUD; `mark-paid` action |
| SMS Logs       | `/api/sms-logs/`          | JWT  | ACCOUNTANT: read + add; ADMIN: full CRUD |
| Send SMS       | `POST /api/send-sms/`     | JWT  | Body: `{"to": "+964...", "body": "text"}`; uses agency Twilio settings |

Write (create/update/delete) for **Users** and **Settings** is restricted to **ADMIN**. For quotations, vouchers, contracts, freelancers, freelance works, and SMS logs: **ACCOUNTANT** can read and create; **ADMIN** can also update and delete.

## Deployment

For production deployment on a Linux VPS (Gunicorn, Nginx, systemd, static files, optional HTTPS and PostgreSQL), see **[DEPLOY.md](DEPLOY.md)**.
