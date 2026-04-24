# SmartSeason — Field Monitoring System

A Django REST Framework backend for tracking crop progress across multiple fields during a growing season. The system supports two user roles — **Admin (Coordinator)** and **Field Agent** — with JWT-based authentication and role-based access control on every endpoint.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Create the PostgreSQL Database](#5-create-the-postgresql-database)
  - [6. Run Migrations](#6-run-migrations)
  - [7. Create a Django Superuser](#7-create-a-django-superuser)
  - [8. Start the Development Server](#8-start-the-development-server)
- [Role Configuration via Django Admin](#role-configuration-via-django-admin)
  - [Why Roles Are Manual](#why-roles-are-manual)
  - [Creating the Admin Role](#creating-the-admin-role)
  - [Creating the Field Agent Role](#creating-the-field-agent-role)
  - [Verifying User Emails During Development](#verifying-user-emails-during-development)
- [App Breakdown](#app-breakdown)
  - [core](#1-core)
  - [authentication](#2-authentication)
  - [fields](#3-fields)
- [API Reference](#api-reference)
  - [Authentication Endpoints](#authentication-endpoints)
  - [Field Endpoints](#field-endpoints)
  - [Dashboard Endpoints](#dashboard-endpoints)
- [Field Status Logic](#field-status-logic)
- [Design Decisions](#design-decisions)
- [Assumptions](#assumptions)
- [Demo Credentials](#demo-credentials)

---

## Tech Stack

| Layer          | Technology                           |
|----------------|--------------------------------------|
| Backend        | Django 4.x + Django REST Framework  |
| Authentication | SimpleJWT (access + refresh tokens) |
| Database       | PostgreSQL                           |
| Language       | Python 3.11+                         |

---

## Project Structure

```
smartseason/
│
├── core/                          # Shared base model (UUID pk, timestamps)
│   └── models.py
│
├── authentication/                # Users, roles, JWT auth, permissions
│   ├── models.py                  # Role, User, OTPRecord
│   ├── serializer.py              # Signup, login, profile serializers
│   ├── views.py                   # UserSignupView, UserLoginView
│   ├── permissions.py             # IsAdminUser, IsFieldAgent
│   ├── manager.py                 # CustomUserManager
│   ├── utility.py                 # Password strength validator
│   └── services/
│       └── signup_service.py      # build_user() factory function
│
├── fields/                        # Field management, assignment, updates
│   ├── models.py                  # FieldManagement, Agents
│   ├── serializer.py              # Field serializers
│   ├── views.py                   # All field-related API views
│   └── urls.py
│
├── smartseason/                   # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smartseason
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True

DB_NAME=smartseason_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

> Make sure your `settings.py` reads these values using `python-decouple` or `os.environ`.

### 5. Create the PostgreSQL Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE smartseason_db;
\q
```

### 6. Run Migrations

```bash
python manage.py makemigrations core
python manage.py makemigrations authentication
python manage.py makemigrations fields
python manage.py migrate
```

> Always run `makemigrations` for `core` first since other apps depend on `BaseModel` from it.

### 7. Create a Django Superuser

A superuser is required to access the Django Admin panel, where you will create the roles that the application depends on.

```bash
python manage.py createsuperuser
```

You will be prompted for an email and password. This account is separate from the API users.

### 8. Start the Development Server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`  
The Django Admin panel is at `http://127.0.0.1:8000/admin/`

---

## Role Configuration via Django Admin

### Why Roles Are Manual

Roles are **not seeded automatically by migrations**. They are created once through the Django Admin panel by the system operator. This is intentional — it gives the operator full control over which roles are active in the system and prevents roles from being accidentally seeded in production environments.

**This is a required step before any user can sign up.** If the roles do not exist when a signup request is made, the API will return:

```json
{
  "error": "No Role found for category 'ADMIN'."
}
```

---

### Creating the Admin Role

1. Go to `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.
2. In the left sidebar, find **Auth Role** under the `Authentication` section and click **+ Add**.
3. Fill in the form exactly as follows:

| Field          | Value                      |
|----------------|----------------------------|
| Role name      | `Admin`                    |
| Category       | `ADMIN`                    |
| Description    | `System coordinator role`  |
| Is system role | ☐ **Leave unchecked**      |

4. Click **Save**.

---

### Creating the Field Agent Role

1. Click **+ Add** on the Auth Role page again.
2. Fill in the form exactly as follows:

| Field          | Value                         |
|----------------|-------------------------------|
| Role name      | `Field Agent`                 |
| Category       | `FIELD_AGENT`                 |
| Description    | `Field monitoring agent role` |
| Is system role | ☐ **Leave unchecked**         |

3. Click **Save**.

> **Critical:** The `Category` values must be exactly `ADMIN` and `FIELD_AGENT` — uppercase, with the underscore. The system uses these strings directly for permission checks and serializer routing. Any deviation will cause signup to fail with a 400 error.

---

### Verifying User Emails During Development

The system requires email verification before a user can log in. In production this is handled by a verification email. During development, verify users manually through the admin panel:

1. Go to **Users** in the Django Admin sidebar.
2. Click the user you want to activate.
3. Scroll to the flags section and:
   - Check ✅ **Email verified**
   - Check ✅ **Is active**
4. Click **Save**.

The user can now log in via the API.

---

## App Breakdown

### 1. `core`

The `core` app is a shared foundation used across the entire project. It contains no views and exposes no API endpoints. Its sole purpose is to provide the `BaseModel` abstract class that every other model inherits from.

**`BaseModel`** (abstract)

| Field        | Type            | Details                                                                                      |
|--------------|-----------------|----------------------------------------------------------------------------------------------|
| `id`         | `UUIDField`     | Primary key using `uuid4`. Non-sequential and non-guessable, preventing ID enumeration attacks on the API. |
| `created_at` | `DateTimeField` | Automatically set when the record is first saved.                                           |
| `updated_at` | `DateTimeField` | Automatically updated on every subsequent save.                                             |

All models across `authentication` and `fields` inherit from `BaseModel`, giving every table a consistent primary key format and timestamps with no repetition.

---

### 2. `authentication`

The `authentication` app owns everything related to identity — who a user is, what role they hold, how they register, how they log in, and what parts of the system they are permitted to access.

---

#### Models

**`Role`**

Defines the access tier for a user. Created manually in Django Admin before signups can occur.

| Field           | Type                  | Details                                                              |
|-----------------|-----------------------|----------------------------------------------------------------------|
| `role_name`     | `CharField`           | Human-readable label e.g. `Admin`, `Field Agent`.                  |
| `category`      | `CharField (choices)` | Machine key used in code: `ADMIN` or `FIELD_AGENT`.                |
| `permissions`   | `ManyToManyField`     | Optional Django permission objects for fine-grained control.        |
| `description`   | `TextField`           | Free-text description of what the role covers.                      |
| `is_system_role`| `BooleanField`        | Reserved flag for internal roles not available for public signup.   |

---

**`User`**

A fully custom user model extending Django's `AbstractUser`. Email is used as the login identifier — there is no `username` field.

| Field                       | Type                    | Details                                                                      |
|-----------------------------|-------------------------|------------------------------------------------------------------------------|
| `email`                     | `EmailField`            | Unique. Used as `USERNAME_FIELD` for all authentication.                    |
| `role`                      | `ForeignKey → Role`     | Determines all access control decisions system-wide.                         |
| `first_name`                | `CharField`             | User's given name.                                                           |
| `last_name`                 | `CharField`             | User's family name.                                                          |
| `phone_number`              | `CharField`             | Required in E.164 format e.g. `+254712345678`.                              |
| `kra_pin`                   | `CharField`             | Unique Kenya Revenue Authority PIN. Real-world identity anchor.              |
| `email_verified`            | `BooleanField`          | Must be `True` before the user can log in. Defaults to `False`.             |
| `email_verification_token`  | `CharField`             | Secure 64-character hex token for email verification.                        |
| `email_verification_expiry` | `DateTimeField`         | Token expires 24 hours after generation.                                     |
| `failed_login_attempts`     | `PositiveIntegerField`  | Tracks consecutive failed logins for lockout logic.                          |
| `locked_until`              | `DateTimeField`         | If set, the account rejects login attempts until this timestamp passes.      |
| `is_active`                 | `BooleanField`          | `False` on creation. Set to `True` after email verification.                |

Key methods:

- `generate_email_token()` — Creates and saves a new verification token with a 24-hour expiry window.
- `verify_email(token)` — Validates the token against expiry, activates the account, and clears token fields.
- `is_locked` *(property)* — Returns `True` if `locked_until` is set and has not yet passed.

---

**`OTPRecord`**

Stores hashed one-time passwords used for phone verification, login OTP, and password reset flows.

| Field       | Type                        | Details                                                          |
|-------------|-----------------------------|------------------------------------------------------------------|
| `user`      | `ForeignKey → User`         | The user this OTP belongs to.                                   |
| `purpose`   | `CharField (choices)`       | One of `phone_verify`, `login`, or `password_reset`.            |
| `code_hash` | `CharField`                 | Bcrypt hash of the OTP. Plaintext is never persisted.           |
| `otp_expiry`| `DateTimeField`             | OTP is invalid after this timestamp.                            |
| `used_at`   | `DateTimeField`             | Set when the OTP is consumed. Prevents replay attacks.          |
| `attempts`  | `PositiveSmallIntegerField` | Maximum of 3 verification attempts allowed per record.          |

---

#### Services

**`signup_service.py` → `build_user(validated_data, role_category)`**

The single authoritative place where `User` objects are created. Called from serializer `create()` methods rather than placing creation logic in the serializer or view layer.

Steps it performs:

1. Looks up the `Role` by `category` string (e.g. `'FIELD_AGENT'`).
2. Raises `ValueError` with a clear message if the role is missing — surfaces cleanly as a `400` response.
3. Handles `Role.MultipleObjectsReturned` gracefully by taking the oldest matching role.
4. Constructs a `User` instance with `is_active=False`.
5. Calls `user.set_password()` so the password is hashed via Django's PBKDF2 hasher before being stored.
6. Saves and returns the user.

Isolating this in a service means the creation logic can be unit tested without constructing a serializer or a request object.

---

#### Serializers

**`BaseSignupSerializer`**

The shared base for all signup flows. Defines every field that all user types must provide, and houses validators that run for every signup regardless of role.

| Validator              | What it enforces                                                |
|------------------------|-----------------------------------------------------------------|
| `validate_email`       | Email not already registered. Lowercases before storage.       |
| `validate_phone_number`| Must be E.164 format (must start with `+`).                   |
| `validate_password`    | Calls `validate_password_strength()` from `utility.py`.        |
| `validate_kra_pin`     | KRA PIN not already registered on another account.             |

**`AdminSignupSerializer`** and **`AgentSignupSerializer`**

Both extend `BaseSignupSerializer` directly, inheriting all field definitions and validation. Their only difference is the `role_category` string passed to `build_user()` inside `create()`.

**`UserProfileSerializer`**

Serializes the `User` returned as part of the login response. Exposes `role_name` sourced from `role.category` via a `source` argument.

**`AdminProfileSerializer`** and **`AgentProfileSerializer`**

Role-specific profile serializers composed into the login response by `serialize_full_user()`. `AgentProfileSerializer` includes `assigned_fields_count`. These grow as role-specific data requirements expand.

---

#### Permissions

Defined in `authentication/permissions.py`. Imported by any app that needs role-based access control.

**`IsAdminUser`**
```
Grants access when: request.user.role.category == 'ADMIN'
Denied response:    403 "Access restricted to Admin users only."
```

**`IsFieldAgent`**
```
Grants access when: request.user.role.category == 'FIELD_AGENT'
Denied response:    403 "Access restricted to Field Agents only."
```

---

#### View Logic

**`UserSignupView`**

- Reads `user_type` from the request body.
- Looks up the correct serializer from the `SIGNUP_SERIALIZER` dispatch map — avoids `if/elif` chains.
- Runs validation, calls `serializer.save()`, returns the new user's ID, role, and `is_active` flag.
- Wrapped in `transaction.atomic()` so any failure rolls back cleanly.

**`UserLoginView`**

- Lowercases the email before querying to handle case variations.
- Sequentially checks: password validity → email verification → account active status → role not restricted.
- Blocks `SYSTEM` and `STAFF` category roles from logging in via the public API.
- Calls `update_last_login()` for audit tracking.
- Returns the full serialized user object alongside a JWT access and refresh token pair.

The `serialize_full_user()` helper composes the final response by combining `UserProfileSerializer` output with the role-appropriate profile serializer, looked up via the `PROFILE_SERIALIZER` dispatch map.

---

### 3. `fields`

The `fields` app owns the core business domain — creating fields, assigning them to agents, recording observations, computing field status, and generating dashboard summaries.

---

#### Models

**`FieldManagement`**

Represents a single agricultural field being monitored throughout a growing season.

| Field            | Type                      | Details                                                                            |
|------------------|---------------------------|------------------------------------------------------------------------------------|
| `name`           | `CharField`               | Field name e.g. `North Plot A`.                                                   |
| `crop_type`      | `CharField`               | Crop being grown e.g. `Maize`, `Wheat`, `Sorghum`.                               |
| `planting_date`  | `DateField`               | Date the crop was planted. Used in status and age calculations.                   |
| `current_stage`  | `CharField (choices)`     | One of `planted`, `growing`, `ready`, `harvested`.                               |
| `field_status`   | `CharField (choices)`     | One of `active`, `at_risk`, `completed`. Recalculated on every agent update.     |
| `review`         | `TextField`               | Latest notes or observations submitted by the assigned field agent.               |
| `review_at`      | `DateTimeField`           | Timestamp of the last agent update. Central to the `at_risk` status calculation. |
| `assigned_agent` | `ForeignKey → Agents`     | `SET_NULL` — removing an agent does not delete the field.                         |
| `created_by`     | `ForeignKey → User`       | Which admin created this field. Set automatically from `request.user` in the view.|

The relationship between agents and fields is **one-to-many**. One agent can be responsible for many fields, but each field has at most one assigned agent at any time. This is modelled with a `ForeignKey` on `FieldManagement` rather than a `ManyToManyField` on `Agents`, which keeps the database constraint clear and queries straightforward.

```python
# Get all fields for a given agent
agent.fields.all()

# Get the responsible agent for a field
field.assigned_agent

# Find all currently unassigned fields
FieldManagement.objects.filter(assigned_agent=None)
```

---

**`Agents`**

A profile record for users with the `FIELD_AGENT` role. Created when a field agent signs up and linked one-to-one with their `User` record.

| Field  | Type              | Details                                                         |
|--------|-------------------|-----------------------------------------------------------------|
| `user` | `OneToOneField`   | Links to `authentication.User` via `related_name="agent_profile"`. |

The model is intentionally thin. It exists as a typed anchor for the `assigned_agent` foreign key and as a clean extension point for agent-specific attributes without polluting the `User` model.

---

#### Views

**`FieldManagementView`** — `GET /fields/` and `POST /fields/` — Admin only

- `GET` returns a paginated list of all fields. Uses `select_related('assigned_agent__user')` to fetch related data in a single query and avoid N+1 issues.
- `POST` creates a new field. `created_by` is set to `request.user` in the view — the client does not supply it.

**`AssignFieldView`** — `PATCH /fields/<field_id>/assign/` — Admin only

- Pass `agent_id` to assign a field to an agent.
- Pass `agent_id: null` to unassign the field, making it available for reassignment.

**`AgentFieldListView`** — `GET /agent/fields/` — Field Agent only

- Returns all fields assigned to the currently authenticated agent.
- The agent is resolved from `request.user` — no agent ID is needed in the URL, preventing agents from querying other agents' fields.

**`AgentFieldUpdateView`** — `PATCH /fields/<field_id>/update/` — Field Agent only

- Allows the agent to update `current_stage` and/or `review` on one of their assigned fields.
- The query `FieldManagement.objects.get(id=field_id, assigned_agent=agent)` enforces ownership. An attempt to update another agent's field returns `404`, not `403`, to avoid leaking whether the field ID exists.

**`AdminDashboardView`** — `GET /dashboard/admin/` — Admin only

Returns a summary across all fields in the system:

```json
{
  "total_fields": 12,
  "unassigned_fields": 2,
  "status_breakdown": {
    "active": 7,
    "at_risk": 3,
    "completed": 2
  },
  "stage_breakdown": {
    "planted": 2,
    "growing": 5,
    "ready": 3,
    "harvested": 2
  }
}
```

**`AgentDashboardView`** — `GET /dashboard/agent/` — Field Agent only

Returns the same response shape but scoped exclusively to the authenticated agent's assigned fields.

---

## API Reference

All protected endpoints require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

### Authentication Endpoints

#### `POST /auth/signup/`

Register a new user. `user_type` determines which role is assigned.

**Request:**

```json
{
  "user_type": "FIELD_AGENT",
  "email": "agent@smartseason.com",
  "phone_number": "+254712345678",
  "first_name": "John",
  "last_name": "Kamau",
  "kra_pin": "A012345678Z",
  "password": "SecurePass123!"
}
```

**Success `201`:**

```json
{
  "message": "User created successfully",
  "user_id": "<uuid>",
  "user_type": "FIELD_AGENT",
  "is_active": false
}
```

> `is_active` will be `false` until the user's email is verified.

---

#### `POST /auth/login/`

**Request:**

```json
{
  "email": "admin@smartseason.com",
  "password": "Admin1234!"
}
```

**Success `200`:**

```json
{
  "message": "Login successful",
  "user": {
    "id": "<uuid>",
    "email": "admin@smartseason.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "role_name": "ADMIN",
    "is_active": true,
    "email_verified": true,
    "phone_number": "+254712345678",
    "profile": {}
  },
  "tokens": {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
}
```

---

### Field Endpoints

| Method | Endpoint                          | Role         | Description                               |
|--------|-----------------------------------|--------------|-------------------------------------------|
| GET    | `/fields/`                        | Admin        | Paginated list of all fields              |
| POST   | `/fields/`                        | Admin        | Create a new field                        |
| PATCH  | `/fields/<field_id>/assign/`      | Admin        | Assign or unassign a field to an agent    |
| GET    | `/agent/fields/`                  | Field Agent  | List the authenticated agent's fields     |
| PATCH  | `/fields/<field_id>/update/`      | Field Agent  | Update stage and notes on an owned field  |

**Create field:**

```json
{
  "name": "North Plot A",
  "crop_type": "Maize",
  "planting_date": "2026-01-15",
  "current_stage": "planted"
}
```

**Assign field:**

```json
{ "agent_id": "<agent-uuid>" }
```

**Unassign field:**

```json
{ "agent_id": null }
```

**Update field (agent):**

```json
{
  "current_stage": "growing",
  "review": "Strong early growth observed. No pest activity detected."
}
```

---

### Dashboard Endpoints

| Method | Endpoint             | Role        | Description                              |
|--------|----------------------|-------------|------------------------------------------|
| GET    | `/dashboard/admin/`  | Admin       | Summary stats across all fields          |
| GET    | `/dashboard/agent/`  | Field Agent | Summary stats for the agent's own fields |

---

## Field Status Logic

Each field carries a `field_status` value of `active`, `at_risk`, or `completed`. This is recalculated every time a field agent submits an update via `PATCH /fields/<field_id>/update/`.

| Condition                                                                  | Status assigned |
|----------------------------------------------------------------------------|-----------------|
| `current_stage` is `harvested`                                             | `completed`     |
| `review_at` is `null` or more than **7 days** ago, and stage is not `harvested` | `at_risk`  |
| All other cases                                                            | `active`        |

**Rationale:**

- A harvested field has reached the end of its lifecycle and needs no further monitoring. It is definitively `completed`.
- A field with no logged activity in over a week is a signal that the agent may not be checking in, or that the crop may have encountered problems. Surfacing it as `at_risk` prompts the admin to follow up.
- The 7-day threshold is a sensible default for a growing season where regular check-ins are expected. It can be adjusted in the update service without touching the model schema or API contract.
- Storing `field_status` as a database column rather than computing it on every read keeps dashboard queries fast — status breakdowns are simple `filter()` calls rather than in-memory iteration.

---

## Design Decisions

**UUID primary keys everywhere** — All models use `uuid4` as their primary key. Sequential integer IDs are guessable and enable enumeration attacks on the API. UUIDs eliminate this with no meaningful downside at this system's scale.

**Role dispatch maps over if/elif chains** — `SIGNUP_SERIALIZER` and `PROFILE_SERIALIZER` in `authentication/views.py` map role category strings to serializer classes. Adding a new role is a single dictionary entry rather than a new conditional branch.

**Service layer for user creation** — `build_user()` in `signup_service.py` keeps serializer `create()` methods thin. The creation logic is independently testable without needing a request or a serializer context.

**ForeignKey on FieldManagement, not ManyToManyField on Agents** — A field has exactly one responsible agent at any time. A `ForeignKey` enforces this as a database-level constraint and makes access patterns (`agent.fields.all()`) simpler and more direct than a many-to-many join would be.

**`SET_NULL` on agent deletion** — Deleting an agent nulls out their fields' `assigned_agent` rather than cascading. Field history and data are preserved and the field becomes available for reassignment.

**Email verification gate** — Users are created with `is_active=False`. They cannot log in until both `is_active` and `email_verified` are `True`. This prevents throwaway registrations and guarantees every account has a reachable contact address.

**404 not 403 for cross-agent field access** — When an agent attempts to update a field not assigned to them, the view intentionally returns `404`. Returning `403` would confirm the field ID exists, leaking information about the system's data.

---

## Assumptions

- A field is assigned to at most one agent at a time.
- Only Admins can create fields and manage agent assignments.
- Field Agents can only view and update fields explicitly assigned to them.
- KRA PIN is a required unique identifier for all users, used as a real-world identity anchor in the Kenyan context.
- Phone numbers must be provided in E.164 format (e.g. `+254712345678`).
- The 7-day inactivity window for `at_risk` is a reasonable default for a growing season context and can be tuned as needed.
- Roles must be created via Django Admin before any signups can succeed. This is a deliberate operator-controlled setup step.
- Email sending (verification emails, welcome emails) is scaffolded with commented-out `.delay()` calls in the signup view, showing where an async email task would integrate once a mail backend and Celery are configured.

---

## Demo Credentials

Create these users via `POST /auth/signup/`, then manually verify their emails in the Django Admin panel as described in the [Verifying User Emails](#verifying-user-emails-during-development) section.

| Role        | Email                      | Password      |
|-------------|----------------------------|---------------|
| Admin       | `admin@smartseason.com`    | `Admin1234!`  |
| Field Agent | `agent@smartseason.com`    | `Agent1234!`  |
