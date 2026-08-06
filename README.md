## Quickstart

### 1. Database

```sql
-- inside psql -U postgres
CREATE DATABASE databoard;
CREATE DATABASE databoard_test;
```

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env   # set database_url / jwt_secret_key

uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install

# .env
# REACT_APP_API_URL=http://localhost:8000

npm start
```

App: `http://localhost:3000`

Register an account, then upload the sample CSV from the repo root to
try the app end to end.

## Architecture decisions worth knowing (for review/interview)

- **Dataset storage is JSON, not a dynamic table per upload.** Turning
  arbitrary CSV headers into SQL column identifiers is messy (illegal
  characters, name collisions, a mild injection surface) for no real
  benefit at this scope — preview/compute/plot only ever need to loop
  over parsed rows in Python. Trade-off: no native SQL filtering on
  dataset contents.
- **JWT refresh strategy:** 15-minute access token, 7-day refresh
  token, each carrying a `type` claim so one can't be used in place of
  the other. The frontend's axios interceptor catches a 401, refreshes
  once, and retries the original request transparently — with a queue
  so simultaneous 401s only trigger one refresh call, not several. Full
  writeup in the backend and frontend sections below.
- **Ownership checks return 404, not 403** for datasets that exist but
  belong to another user — avoids confirming to an unauthorized caller
  that the ID exists at all.
- **Operation validation moved to the schema layer**
  (`Literal["min", "max", "sum"]`), not the service — an invalid
  operation is rejected with 422 before the route body even runs. The
  service layer only handles validation that depends on the *data
  itself* (missing/empty/non-numeric column).
- **`bcrypt==4.0.1` is pinned** alongside `passlib[bcrypt]==1.7.4` —
  passlib 1.7.4 predates bcrypt 4.x's API and throws a cryptic
  `AttributeError` on hashing without this pin.

---

# Backend

FastAPI + PostgreSQL API for CSV upload, dataset browsing, quick stats,
and plot data. Auth is hand-rolled JWT (access + refresh) with bcrypt
password hashing.

## Stack & why

- **FastAPI** — async-capable, automatic request validation via
  Pydantic, built-in OpenAPI docs at `/docs`.
- **SQLAlchemy (sync)** — no async DB driver needed at this scale; sync
  SQLAlchemy is simpler to reason about and plenty fast for a
  take-home.
- **PostgreSQL** — required by the spec; also gives native JSON support
  for the dataset storage approach below.
- **pyjwt + passlib[bcrypt]** — rolled by hand instead of a library
  like `fastapi-users`, specifically because the spec asks to
  *document your JWT refresh strategy*

## Project layout

- backend/
- app/
- main.py FastAPI app, router registration, table creation
- core/
- config.py Settings (env-driven via pydantic-settings)
- security.py Password hashing, JWT encode/decode
- dependencies.py get_current_user / get_refresh_user_id (FastAPI deps)
- db/
- database.py SQLAlchemy engine/session, get_db dependency
- models.py User, Dataset ORM models
- schemas/
- auth.py, dataset.py, analytics.py Pydantic request/response models
- services/
- csv_service.py CSV parsing (pure function, no framework imports)
- compute_service.py Stat computation + its edge cases (unit tested)
- plot_service.py Builds x/y point pairs for the plot endpoint
- dataset_service.py Shared "fetch dataset the caller owns, or 404"
- api/
- auth.py, datasets.py, analytics.py Routers — thin, call into services
- tests/
- conftest.py Test fixtures (Postgres test DB, auth_headers)
- test_compute.py Compute endpoint's required edge cases
- test_auth.py Register/login/refresh/me
- test_datasets.py Upload/preview/delete/ownership/pagination

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup
(`Base.metadata.create_all` in `main.py`) — no separate migration step
at this scope. Interactive API docs at `http://localhost:8000/docs`.

## Running tests

```bash
pytest tests/ -q
```

Tests run against the **`databoard_test`** database, not dev
database, each test gets a clean schema via `create_all`/`drop_all`
fixtures.

Coverage, by file:

- **`test_compute.py`** — the spec's required edge cases for
  `/dataset/:id/compute`: empty column, all-null column, non-numeric
  column requested as a stat, plus a mixed numeric/junk column (skips
  junk rather than failing outright) and the happy path. Both as pure
  unit tests against `compute_service.compute_stat()` and as HTTP
  integration tests through the real endpoint.
- **`test_auth.py`** — register, duplicate-email conflict, login with
  wrong password, short-password rejection (schema-level), the refresh
  flow, and confirmation that an access token can't be used at
  `/auth/refresh` (type-checked in `core/security.py`).
- **`test_datasets.py`** — upload validation, preview truncation to 25
  rows, delete, and cross-user access returning 404 (not 403). Also the
  **pagination proof**: uploads 5 datasets, paginates with `limit=2`,
  and asserts zero ID overlap across pages plus correct
  `total`/`total_pages`.

## JWT strategy

- **Access token**: 15 minutes. Attached to every authenticated
  request.
- **Refresh token**: 7 days. Only ever sent to `POST /auth/refresh`.
- Both tokens carry a `type` claim (`"access"` or `"refresh"`) inside
  the JWT payload. `core/security.py`'s `decode_token(token,
  expected_type)` checks this claim, so a refresh token can't be used
  directly as an API credential on a protected route, and an access
  token is rejected at `/auth/refresh` — each token is only ever valid
  where it's supposed to be. `test_refresh_rejects_access_token` in
  `test_auth.py` proves this.
- On expiry, the frontend calls `/auth/refresh` with the refresh token
  to get a new 15-minute access token, without forcing a full
  re-login. If the refresh token itself is expired or invalid, the
  user is redirected to log in again.
- Short-lived access tokens limit the exposure window if one leaks
  (e.g. via XSS); the refresh token has a narrower attack surface
  since it's only ever sent to one endpoint.

## Technical assumptions

- **Dataset storage**: uploaded CSV rows are parsed once and stored as
  JSON (`Dataset.rows`, `Dataset.columns`) rather than as a
  dynamically created SQL table per upload. Turning arbitrary CSV
  headers into SQL column identifiers is messy for no real benefit at
  this scope — the app only ever needs to preview 25 rows, compute one
  stat, or plot two columns, all done by looping over the JSON in
  Python. Trade-off: no native SQL filtering on dataset contents.
- **CSV encoding**: decoded as UTF-8 with a BOM stripped if present
  (`utf-8-sig`), and decode errors are replaced rather than raised, so
  one bad byte doesn't fail an entire upload.
- **Compute edge cases**: a column that's numeric except for a few
  stray non-numeric values still computes over the numeric subset
  (reporting how many values were skipped) rather than failing the
  whole request — mirrors how a spreadsheet's SUM/MIN/MAX ignores
  blank or text cells. A column that's *entirely* non-numeric or empty
  still returns 400, per the spec's required test cases.
- **Operation validation**: `min`/`max`/`sum` are validated by the
  request schema (`Literal["min", "max", "sum"]`) rather than in the
  service layer — an invalid operation is rejected with 422 before the
  route body even runs.
- **Ownership checks return 404, not 403**: `dataset_service.py`'s
  `get_owned_dataset_or_404` returns 404 for a dataset that exists but
  belongs to another user, avoiding confirmation that the ID exists at
  all.
- **Pagination**: `GET /dataset` runs a real `LIMIT`/`OFFSET` query
  against Postgres (not an in-memory slice) and returns
  `total`/`total_pages` from a separate `COUNT` query.
- **Plot data volume**: capped at 30 points per request
  (`plot_service.MAX_PLOT_POINTS`).
- **bcrypt version pin**: `requirements.txt` pins `bcrypt==4.0.1`
  alongside `passlib[bcrypt]==1.7.4` — passlib 1.7.4 predates bcrypt
  4.x's API changes and throws a cryptic `AttributeError` on hashing
  without this pin.

---

# Frontend

React (Create React App) client for the DataBoard API — CSV upload,
dataset browsing/preview, quick stats, and ECharts plots. JWT auth with
automatic access-token refresh.

## Stack

- **React 19** via Create React App (`react-scripts`)
- **react-router-dom v7** — routing
- **axios** — API client, with a response interceptor that
  transparently refreshes an expired access token (see below)
- **react-hot-toast** — error/success notifications
- **echarts-for-react** — the plot on the Plot page (scatter/line/bar)

> `recharts` is listed in `package.json` but not currently used
> anywhere — `echarts-for-react` is the charting library actually
> wired up.

## Project layout

- frontend/
- src/
- App.js Routes + AuthProvider + Navbar + Toaster
- context/
- AuthContext.jsx Holds user, login-state init, refresh(), logout()
- hooks/
- useAuth.js Thin useContext(AuthContext) wrapper
- utils/
- axiosConfig.jsx Shared axios instance + auth interceptors
- api/
- auth.js register/login/getMe/refreshToken calls
- vdataset.js dataset CRUD + compute/plot calls
- components/
- Navbar.jsx Brand + nav links (Data/Plot) + logout
- ProtectedRoute.jsx Redirects to /login if not authenticated
- UploadForm.jsx Name + CSV file, multipart POST to /dataset
- DatasetList.jsx Shared list used by both Data and Plot pages
- pages/
- Login.jsx, Register.jsx Auth forms
- Dashboard.jsx Landing page — links to Data / Plot
- Data_analytics.jsx Upload, list, delete, preview (Screen 2)
- Data_plot.jsx Dataset picker, compute stat, ECharts plot (Screen 3)
- NotFound.jsx

Page responsibilities are split by what the spec calls two different
screens: `Data_analytics.jsx` owns everything about *managing* a
dataset (upload/list/delete/preview), `Data_plot.jsx` owns everything
about *analyzing* one (compute a stat, plot two columns). Neither page
holds state the other needs — `Data_plot.jsx` re-fetches a dataset's
column list via the preview endpoint rather than sharing state with
`Data_analytics.jsx`, so the two pages can be visited in either order
without stale state carrying over.

## Setup & run

```bash
cd frontend
npm install
```

Point the client at your backend (defaults to `http://localhost:8000`
if unset):

## .env

REACT_APP_API_URL=http://localhost:8000

```bash
npm start       # dev server, http://localhost:3000
npm run build   # production build
```

No proxy config needed — `axiosConfig.jsx` uses an absolute
`REACT_APP_API_URL` base URL rather than relying on CRA's dev-server
proxy, so CORS on the FastAPI side (`allow_origins=["*"]` in
`app/main.py`) has to actually be permissive, which it is.

## Auth flow

- **Login/Register** (`api/auth.js`) hit `/auth/login` /
  `/auth/register`, which return `{ access_token, refresh_token, user
  }`. `Login.jsx` stores both tokens in `localStorage` under the keys
  `access_token` and `refresh_token`, and sets `user` directly from
  the response — no extra round trip to `/auth/me` on login.
- **On app load** (`AuthContext.jsx`), if an `access_token` exists,
  `/auth/me` is called to confirm it's still valid and populate
  `user`. If that fails (expired), it tries `refresh()` once before
  giving up and logging out.
- **Every outgoing request** (`utils/axiosConfig.jsx`) gets the
  current `access_token` attached via a request interceptor.
- **On a 401** from any request, a response interceptor:
  1. Reads the stored `refresh_token`.
  2. Calls `POST /auth/refresh` directly via a bare `axios` call —
     *not* through the shared `api` instance, since going through it
     would attach the (expired) access token instead of the refresh
     token as the Bearer credential, and the backend explicitly
     rejects the wrong token type there.
  3. Stores the new `access_token` and retries the original request
     exactly once (`_retry` flag prevents infinite retry loops).
  4. If several requests 401 around the same time, only the first
     triggers a refresh call — the rest queue and reuse its result
     (`isRefreshing`/`queue` in `axiosConfig.jsx`), avoiding a refresh
     stampede.
  5. If the refresh itself fails (refresh token also expired/invalid),
     both tokens are cleared and the user is redirected to `/login`.
- **Logout** clears both tokens client-side. There's no `/auth/logout`
  route on the backend — JWTs aren't server-side revocable in this
  design, so "logging out" is purely a frontend action.

## Routes

| Path | Component | Protected? |
|---|---|---|
| `/login` | `Login.jsx` | No |
| `/register` | `Register.jsx` | No |
| `/` | `Dashboard.jsx` | Yes |
| `/analytics` | `Data_analytics.jsx` | Yes |
| `/plot` | `Data_plot.jsx` | Yes |
| `*` | `NotFound.jsx` | No |

Protected routes are wrapped in `ProtectedRoute.jsx`, which redirects
to `/login` if `AuthContext`'s `user` is null once the initial auth
check (`loading`) has finished.

## Testing

`npm test` runs CRA's default Jest + React Testing Library setup, but
no test files have been written yet — the take-home's explicit testing
requirement is scoped to the backend's compute endpoint (covered under
Backend → Running tests above). Given the time budget, frontend
verification here was done as a manual QA pass instead: register →
login → upload a CSV → preview → compute a stat on an empty/non-numeric
column (confirms the 400 error surfaces as a toast) → delete → plot two
columns → confirm session survives an access-token expiry via the
silent refresh.

The single highest-value automated test to add would
be an isolated test of the refresh interceptor in `axiosConfig.jsx`
(mock a 401, assert it calls `/auth/refresh` and retries the original
request).
