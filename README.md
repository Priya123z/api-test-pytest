# REST API Test Suite

42 Pytest tests over a REST API's CRUD and auth flows, with the response shapes
validated against JSON Schemas, published from CI on every commit.

[**Open the live report**](https://priya123z.github.io/api-test-pytest/): the real thing, not a screenshot.

[![API Tests](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml/badge.svg)](https://github.com/Priya123z/api-test-pytest/actions/workflows/api-tests.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Tests](https://img.shields.io/badge/tests-42-0a6e4e.svg)

Tests run against [DummyJSON](https://dummyjson.com), a free public API, so
there is nothing to sign up for and nothing to configure. Point `BASE_URL` at
your own service and the same structure works.

---

## When you would reach for this

This is a template for the step between a Postman collection and a suite the
build actually depends on.

- **You have API tests in Postman and want them in the repo.** This is what that
  looks like: same requests, but version-controlled, reviewable in a pull
  request, and running on every commit without anyone pressing Send.
- **You need to know when a backend team changes a response shape.** That is
  what the schema layer is for, and it is the reason to prefer this over a
  status-code check. See below.
- **You are starting an API suite and want a layout that will not need
  rewriting.** Client wrapper, env config, schemas as separate files, fixtures
  for anything expensive. Four directories, nothing clever.
- **You want a worked example of publishing test results somewhere people will
  read them.** CI writes an HTML report to GitHub Pages and comments the summary
  on the pull request.

Where **not** to use it as-is: it has no database setup or teardown, and it
assumes the API under test is reachable and idempotent enough that tests can run
in any order. Real services usually need seeded data, which is a fixture
concern this deliberately does not solve for you.

---

## What it covers

| Module | Tests | Covered |
|---|---|---|
| GET users | 16 | Paginated list, single user, 404, schema validation, response-time budget, parametrized IDs |
| POST users | 7 | Create returns 201, schema, payload echoed back, generated id, parametrized multi-user |
| PUT / PATCH / DELETE | 10 | Full update, partial update, id preserved, `isDeleted` flag, parametrized deletes |
| Auth | 9 | Valid login, access token present, schema, missing fields → 400, invalid credentials → 400 |
| **Total** | **42** | |

---

## The point of the schema layer

Status code and response time are table stakes. Schema validation is what
catches a **contract break**.

When a backend team renames `firstName` to `first_name`, a test that asserts
`response.status_code == 200` still passes. Your suite stays green and the
mobile client breaks in production. A schema test fails on the commit that did
it.

So the response shapes are validated against a JSON Schema before the test goes
green: the user list, a single user, a created user, and a login. The error
paths (a 404, a 400 from an incomplete login) are asserted on status and message
instead, because there is no contract to hold them to.

The schemas live in `schemas/` as their own files rather than as assertions
buried in test code. They are the contract, so they belong under version control
next to it, where you can diff them.

What this does **not** catch: none of the four schemas sets
`additionalProperties: false`, so a field being *added* passes. A field being
removed or retyped fails, which is the break that matters here.

---

## Quick start

```bash
git clone https://github.com/Priya123z/api-test-pytest.git
cd api-test-pytest

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest
```

No key, no sign-up, no `.env` needed. `BASE_URL` and `DEFAULT_TIMEOUT` both have
defaults in `utils/env.py`, so there is nothing to configure before the first
run.

### Running a subset

```bash
pytest -m smoke          # 8 tests, the critical path
pytest -m auth           # 9
pytest -m users          # 33
pytest -m "not smoke"    # everything else
pytest tests/test_auth.py -v
```

Every marker in `pytest.ini` is used by at least one test, so none of these
commands collects zero. That sounds obvious, and it was not true before: the
README advertised `-m regression` and nothing carried the marker. `--strict-markers`
now turns a typo in a decorator into a collection error rather than a marker
that quietly means nothing.

### Against your own service

```bash
BASE_URL=https://staging.myapp.com pytest
```

### A local HTML report

```bash
pytest --html=report.html --self-contained-html
```

---

## Design notes

- **A session-scoped client.** `APIClient` is built once per run rather than once
  per test, so forty-two tests share one connection pool and one retry policy.
- **Parametrized rather than copy-pasted.** Multi-user create and delete are one
  test method with several parameter sets.
- **A retry adapter on the client.** The API under test is a shared public
  service. A 429 from a busy CI runner is a fact of the environment, not a
  defect, so 429 and 5xx are retried with backoff. 4xx is never retried, because
  the negative tests assert on those.
- **`load_schema()` lives in `conftest.py`.** It was copy-pasted into the three
  test files that validate schemas, which meant three places to change when the
  schema directory moved.
- **A response-time assertion with a realistic budget.** It used to be a hard
  two seconds, which flakes on a shared runner for reasons that have nothing to
  do with the API.

---

## CI

GitHub Actions runs all 42 tests on every push and pull request, and again
nightly on a cron. The nightly run is the useful one: it catches the upstream
API changing shape on a day when nobody pushed anything, which is exactly the
failure a suite like this exists to find.

Each run:

- writes an HTML report and **publishes it to GitHub Pages**, so the latest
  result is always at a stable URL rather than inside an artifact zip that
  expires
- posts a pass/fail summary as a **pull request comment**, updating the same
  comment instead of adding a new one each push
- publishes per-PR reports under `pr-<number>/`

No secrets or environment variables are needed, because DummyJSON needs no key.

---

## Layout

```
api-test-pytest/
|- tests/
|  |- conftest.py               the client and load_schema fixtures, report metadata
|  |- test_users_get.py         GET, with schema validation and a time budget
|  |- test_users_post.py        create
|  |- test_users_put_delete.py  update, partial update, delete
|  '- test_auth.py              login: valid, missing fields, bad credentials
|- utils/
|  |- api_client.py             requests session with retry and timeout
|  '- env.py                    BASE_URL and DEFAULT_TIMEOUT, with defaults
|- schemas/
|  |- user_schema.json
|  |- user_list_schema.json
|  |- login_response_schema.json
|  '- create_user_response_schema.json
|- .github/
|  |- workflows/api-tests.yml
|  '- scripts/summarise.py     JUnit XML to the markdown in the PR comment
|- pytest.ini
'- requirements.txt
```

MIT. Built by Priya Bhagoriya: [portfolio](https://priya123z.github.io/) · [LinkedIn](https://linkedin.com/in/priya-bhagoriya)
