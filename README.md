# REST API Test Suite

A Pytest-based REST API test framework demonstrating code-first API testing with JSON Schema validation, environment-aware fixtures, and CI/CD integration. Tests target the [Reqres.in](https://reqres.in) public API across user CRUD operations and authentication flows. Designed to show the step senior QA engineers take from Postman collections to version-controlled, CI-runnable tests.

[![API Tests](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml/badge.svg)](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Tests](https://img.shields.io/badge/tests-33-brightgreen.svg)

---

## Test coverage

| Module | Tests | What's covered |
|--------|-------|----------------|
| GET users | 11 | List (paginated), single user, 404, schema validation, response time SLA |
| POST users | 6 | Create, schema validation, echoed payload, parametrized multi-user |
| PUT / PATCH / DELETE | 8 | Update, partial update, `updatedAt` timestamp, no-body 204 |
| Auth | 8 | Valid login, token presence, schema, missing fields, error messages |
| **Total** | **33** | |

---

## Why JSON Schema validation matters

Status code + response time is table stakes. Schema validation catches **contract breaks** — when a backend team renames `first_name` to `firstName`, a status-200 test still passes. Schema tests don't. Every GET response in this suite is validated against a JSON Schema before the test is marked green. The schemas live in `schemas/` alongside the tests so they version-control with the contract they're testing.

---

## Project structure

```
api-test-pytest/
├── tests/
│   ├── conftest.py             # APIClient + auth_token fixtures
│   ├── test_users_get.py       # GET tests with schema validation
│   ├── test_users_post.py      # POST tests
│   ├── test_users_put_delete.py
│   └── test_auth.py
├── utils/
│   ├── api_client.py           # thin requests wrapper (session, headers, timeout)
│   └── env.py                  # loads BASE_URL + DEFAULT_TIMEOUT from .env
├── schemas/
│   ├── user_schema.json
│   ├── user_list_schema.json
│   ├── login_response_schema.json
│   └── create_user_response_schema.json
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

**Run a specific suite:**
```bash
pytest tests/test_auth.py -v
pytest tests/test_users_get.py -v
```

**Run against a different base URL:**
```bash
BASE_URL=https://staging.myapp.com pytest tests/ -v
```

**Generate HTML report:**
```bash
pytest tests/ --html=report.html --self-contained-html
```

---

Built by Priya Bhagoriya | [LinkedIn](https://linkedin.com/in/priya-bhagoriya)
