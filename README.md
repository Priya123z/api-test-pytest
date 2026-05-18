# REST API Test Suite

A Pytest-based REST API test framework demonstrating code-first API testing with JSON Schema validation, environment-aware fixtures, and CI/CD integration. Tests target the [DummyJSON](https://dummyjson.com) public API across user CRUD operations and authentication flows. Designed to show the step senior QA engineers take from Postman collections to version-controlled, CI-runnable tests.

[![API Tests](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml/badge.svg)](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Tests](https://img.shields.io/badge/tests-43-brightgreen.svg)

---

## What it tests

| Module | Tests | What's covered |
|--------|-------|----------------|
| GET users | 16 | List (paginated), single user, 404, schema validation, response time SLA, parametrized IDs |
| POST users | 7 | Create (201), schema validation, echoed payload, generated ID, parametrized multi-user |
| PUT / PATCH / DELETE | 10 | Full update, partial update, ID preserved, `isDeleted` flag, parametrized deletes |
| Auth | 10 | Valid login (200), access token, schema, missing fields (400), invalid creds (400), parametrized error matrix |
| **Total** | **43** | |

---

## Why JSON Schema validation matters

Status code + response time is table stakes. Schema validation catches **contract breaks** — when a backend team renames `firstName` to `first_name`, a status-200 test still passes. Schema tests don't. Every GET response in this suite is validated against a JSON Schema before the test is marked green. The schemas live in `schemas/` alongside the tests so they version-control with the contract they're testing.

---

## Project structure

```
api-test-pytest/
├── tests/
│   ├── conftest.py             # APIClient + auth_token fixtures
│   ├── test_users_get.py       # GET tests with schema validation + SLA
│   ├── test_users_post.py      # POST (create) tests
│   ├── test_users_put_delete.py # PUT, PATCH, DELETE tests
│   └── test_auth.py            # Auth login tests (valid, missing fields, invalid creds)
├── utils/
│   ├── api_client.py           # Thin requests wrapper (session, headers, timeout)
│   └── env.py                  # Loads BASE_URL + DEFAULT_TIMEOUT from .env
├── schemas/
│   ├── user_schema.json               # Single user contract
│   ├── user_list_schema.json          # Paginated user list contract
│   ├── login_response_schema.json     # Auth response contract (accessToken)
│   └── create_user_response_schema.json  # Create user response contract
├── .env.example
├── pytest.ini
├── requirements.txt
└── .github/workflows/api-tests.yml
```

---

## Quick start

```bash
git clone https://github.com/Priya123z/api-test-pytest.git
cd api-test-pytest

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest tests/ -v
```

No API key or sign-up needed — [DummyJSON](https://dummyjson.com) is a free public test API.

---

## Running specific suites

```bash
# Run a single test file
pytest tests/test_auth.py -v
pytest tests/test_users_get.py -v

# Run by marker
pytest -m smoke -v
pytest -m auth -v

# Run against a different base URL (e.g., your own staging server)
BASE_URL=https://staging.myapp.com pytest tests/ -v
```

---

## Generate HTML report

```bash
pytest tests/ --html=report.html --self-contained-html
# Open report.html in a browser
```

---

## Test design highlights

- **Fixtures with session scope** — the `APIClient` and `auth_token` are created once per test run, not once per test — saves repeated login round-trips
- **Parametrized tests** — multi-user creation and delete are expressed as one test method with multiple parameter sets, not copy-pasted tests
- **Response time SLA** — GET /users asserts it completes in under 2 seconds; catches regressions before monitoring does
- **Contract-first schema** — JSON Schemas in `schemas/` are the source of truth for response shape, not the test code itself

---

## CI/CD

GitHub Actions runs the full 43-test suite on every push and pull request to `main`, generating an HTML report artifact (14-day retention).

```yaml
# .github/workflows/api-tests.yml
pytest tests/ --html=api-test-report.html --self-contained-html -v
```

No secrets or environment variables are needed — DummyJSON requires no API key.

---

Built by Priya Bhagoriya | [LinkedIn](https://linkedin.com/in/priya-bhagoriya)
