# DEEP_DIVE.md — api-test-pytest

> A professional REST API test framework using **Pytest + Requests**, targeting the [DummyJSON public API](https://dummyjson.com).

---

## Table of Contents

1. [What It Is — Three Levels of Understanding](#1-what-it-is--three-levels-of-understanding)
2. [Architecture Diagram](#2-architecture-diagram)
3. [How to Run](#3-how-to-run)
4. [How to Validate](#4-how-to-validate)
5. [Interview Q&A — 25 Questions](#5-interview-qa--25-questions)

---

## 1. What It Is — Three Levels of Understanding

### Level 1 — Simple

This project is a collection of automated tests that check whether a web API behaves correctly. It sends HTTP requests (GET, POST, PUT, PATCH, DELETE) to a free public API called DummyJSON and verifies that the responses come back with the right data, the right status code, and the right structure — all without needing a browser.

Think of it as a robot that repeatedly calls an API and checks: "Did it return what it was supposed to?" If something breaks in the API, the tests fail and alert you immediately.

---

### Level 2 — Intermediate

The project has four test files, each targeting a different concern:

| File | Coverage |
|---|---|
| `tests/test_users_get.py` | 16 tests — status 200, response time SLA (<2s), JSON Schema validation, pagination (limit/skip), single user fetch, 404 handling, parametrized IDs 1–6 |
| `tests/test_users_post.py` | 7 tests — POST /users/add returns 201, schema validation, payload echo (firstName/lastName/email), integer ID in response, parametrized across 3 users |
| `tests/test_users_put_delete.py` | 10 tests — PUT full update (200 + echoed data + preserved ID), PATCH partial update, DELETE returns 200 + `isDeleted: true`, parametrized delete matrix |
| `tests/test_auth.py` | 10 tests — valid login returns 200 + accessToken, schema validation, missing password → 400, invalid credentials → 400, parametrized error scenarios |

**How fixtures chain together:**

`conftest.py` defines two session-scoped fixtures:

1. `api` — creates one `APIClient` instance for the entire test run. Every test that requests the `api` fixture receives the same shared object.
2. `auth_token` — depends on `api`. It calls `/auth/login` once, extracts the `accessToken`, and caches it. All auth tests share this single token.

This chain means: `auth_token` → uses `api` → uses `APIClient` → wraps `requests.Session`.

**JSON Schema validation** is applied across all four test files using four JSON Schema files in the `schemas/` directory:

- `user_schema.json` — validates a single user object
- `user_list_schema.json` — validates the paginated list response
- `login_response_schema.json` — validates the auth response
- `create_user_response_schema.json` — validates the POST response

---

### Level 3 — Advanced

**Why JSON Schema over manual field assertion:**

Manual assertions check individual fields: `assert resp["id"] == 1`. This is fragile and incomplete — if the API silently renames `firstName` to `first_name`, or removes the `email` field, a manual assertion on a different field won't catch it. JSON Schema describes the *contract* of the entire response object. A single `jsonschema.validate(response_body, schema)` call verifies field names, types, required fields, and structure all at once. It also documents the expected shape of every response in a machine-readable, version-controllable file.

**Session scope strategy:**

Pytest fixtures can have four scopes: `function` (default), `class`, `module`, and `session`. Using `scope="session"` means the fixture is created once for the entire test run and destroyed at the very end. For the `api` fixture, this avoids creating 43 separate `requests.Session` objects. For `auth_token`, this avoids 43 separate login API calls — which would be slow, wasteful, and potentially rate-limited.

The tradeoff: session-scoped fixtures are shared state, so tests must not mutate the `api` object in a way that affects other tests. This framework avoids that by treating `api` as a stateless transport layer.

**Fixture dependency injection:**

Pytest's fixture system is a dependency injection framework. When a test function declares `def test_something(api, auth_token)`, pytest resolves the dependency graph, creates `api` first (because `auth_token` depends on it), and injects both. This is the Inversion of Control pattern — tests declare *what* they need, not *how* to create it.

**Why requests over httpx:**

`requests` is the de facto standard for Python HTTP clients with a massive ecosystem, battle-tested reliability, and familiar API. `httpx` is its modern successor with async support, but async is not needed here — these are synchronous integration tests where each request must complete before the assertion. `requests.Session` provides connection pooling, shared headers, and timeout config in a simple interface. The added complexity of `asyncio` + `httpx` brings no benefit for this use case.

---

## 2. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          pytest runner                               │
│                    (pytest tests/ -v)                                │
└───────────┬──────────────────────────────────────────────────────────┘
            │  discovers and executes
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         conftest.py                                  │
│                                                                      │
│   ┌─────────────────────────┐   ┌──────────────────────────────┐    │
│   │  fixture: api           │   │  fixture: auth_token         │    │
│   │  scope=session          │◄──│  scope=session               │    │
│   │  → APIClient()          │   │  → calls /auth/login once    │    │
│   └────────────┬────────────┘   └──────────────────────────────┘    │
└────────────────│─────────────────────────────────────────────────────┘
                 │  injected into
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       utils/api_client.py                            │
│                                                                      │
│   APIClient (wraps requests.Session)                                 │
│   - BASE_URL prefix on all requests                                  │
│   - Content-Type: application/json header                            │
│   - DEFAULT_TIMEOUT on every call                                    │
│   - .get() .post() .put() .patch() .delete() methods                │
└────────────────┬─────────────────────────────────────────────────────┘
                 │  HTTP requests over TCP (connection reuse)
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  DummyJSON Public API                                 │
│             https://dummyjson.com                                    │
│                                                                      │
│   GET  /users?limit=6&skip=0   →  {users:[...], total:208}          │
│   GET  /users/1                →  {id:1, firstName:"Emily", ...}     │
│   GET  /users/999              →  404 {message:"not found"}          │
│   POST /users/add              →  201 {id:209, ...}                  │
│   PUT  /users/2                →  200 {id:2, ...}                    │
│   PATCH /users/2               →  200 {id:2, ...}                    │
│   DELETE /users/1              →  200 {id:1, isDeleted:true}         │
│   POST /auth/login             →  200 {accessToken, ...}             │
└────────────────┬─────────────────────────────────────────────────────┘
                 │  response (JSON body + status code + headers)
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Test Files (43 tests total)                        │
│                                                                      │
│   test_users_get.py       (16 tests)                                 │
│   test_users_post.py      (7 tests)                                  │
│   test_users_put_delete.py (10 tests)                                │
│   test_auth.py            (10 tests)                                 │
│                                                                      │
│   Each test performs TWO layers of assertion:                        │
│                                                                      │
│   ┌────────────────────────┐   ┌────────────────────────────────┐   │
│   │  Status + Value Check  │   │  JSON Schema Validation        │   │
│   │  assert resp.status    │   │  jsonschema.validate(          │   │
│   │  assert body["id"]     │   │    body, schema)               │   │
│   └────────────────────────┘   └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. How to Run

### Prerequisites

```bash
cd /path/to/api-test-pytest
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run all 43 tests

```bash
pytest tests/ -v
```

### Run a specific test file

```bash
pytest tests/test_auth.py -v
pytest tests/test_users_get.py -v
pytest tests/test_users_post.py -v
pytest tests/test_users_put_delete.py -v
```

### Run by marker

```bash
pytest -m smoke -v           # smoke tests only
pytest -m regression -v      # regression tests only
pytest -m auth -v            # auth tests only
pytest -m users -v           # user CRUD tests only
```

### Run a single test by name

```bash
pytest tests/test_users_get.py::test_get_users_status_code -v
pytest tests/test_auth.py::test_login_valid -v
```

### Override the target API (e.g., staging)

```bash
BASE_URL=https://staging.myapp.com pytest tests/ -v
```

### Generate an HTML report

```bash
pytest tests/ --html=report.html --self-contained-html
```

Open `report.html` in any browser after the run completes.

### Run with short traceback (default from pytest.ini)

```bash
pytest tests/ -v --tb=short
```

### Run with full traceback for debugging

```bash
pytest tests/ -v --tb=long
```

### Run and stop on first failure

```bash
pytest tests/ -v -x
```

### Run and show last 5 failures

```bash
pytest tests/ -v --last-failed
```

---

## 4. How to Validate

### What a passing run looks like

When all 43 tests pass, the terminal output ends with:

```
=================== 43 passed in X.XXs ===================
```

A verbose run (`-v`) shows each test individually:

```
tests/test_users_get.py::test_get_users_status_code PASSED          [  2%]
tests/test_users_get.py::test_get_users_response_time_sla PASSED    [  4%]
tests/test_users_get.py::test_get_users_schema PASSED               [  6%]
tests/test_users_get.py::test_get_users_pagination PASSED           [  9%]
tests/test_users_get.py::test_get_user_by_id[1] PASSED             [ 11%]
tests/test_users_get.py::test_get_user_by_id[2] PASSED             [ 13%]
...
tests/test_auth.py::test_login_invalid_creds[bad_user-bad_pass] PASSED [100%]

=================== 43 passed in 12.47s ===================
```

Parametrized tests show the parameter in brackets: `test_get_user_by_id[1]`, `test_get_user_by_id[2]`, etc.

### What a failure looks like

If the DummyJSON API changes its schema (e.g., renames `firstName` to `first_name`), a schema test fails:

```
FAILED tests/test_users_get.py::test_get_users_schema
AssertionError: jsonschema.exceptions.ValidationError: 'firstName' is a required property
```

If response time exceeds the 2-second SLA:

```
FAILED tests/test_users_get.py::test_get_users_response_time_sla
AssertionError: assert 2.341 < 2.0
```

### Reading the HTML report

After running `pytest tests/ --html=report.html --self-contained-html`:

1. Open `report.html` in a browser
2. The summary table shows: Total / Passed / Failed / Errors / Skipped
3. Click any failed test row to expand the full traceback
4. The "Environment" section shows Python version, pytest version, and platform
5. Each test shows its duration — useful for identifying slow tests

The HTML report is self-contained (no external dependencies) and can be shared with teammates or attached to a CI artifact.

---

## 5. Interview Q&A — 25 Questions

---

### Q1. What is API testing and why is it important?

**API testing** is the practice of sending HTTP requests to an application's interface layer and verifying the responses — checking status codes, response bodies, headers, response time, and data contracts — without going through a UI.

It matters for several reasons. First, APIs are the contract between the backend and every consumer (mobile apps, web frontends, third-party integrations). A broken API breaks everything downstream. Second, API tests are faster than UI tests because they bypass the browser rendering layer. Third, they catch regressions early in CI before code reaches production. Fourth, APIs expose business logic directly — you can test edge cases that are hard to trigger through a UI.

---

### Q2. What is the difference between API testing and UI testing?

| Dimension | API Testing | UI Testing |
|---|---|---|
| Layer | HTTP interface | Browser/DOM |
| Speed | Fast (milliseconds) | Slow (seconds per step) |
| Stability | Stable (API contracts rarely change) | Fragile (UI elements change often) |
| Tools | Pytest, Requests, Postman | Selenium, Playwright, Cypress |
| Scope | Business logic, data contracts | User workflows, visual correctness |
| Dependencies | Network only | Browser, JS runtime, CSS |

API tests are preferred for testing business logic and data validation. UI tests are preferred for testing end-to-end user journeys. A healthy test pyramid has many API tests and fewer UI tests.

---

### Q3. What is JSON Schema validation and why does it catch things status codes don't?

A **status code** (200, 201, 404) tells you whether the request succeeded or failed at the HTTP protocol level. It says nothing about the shape of the response body.

**JSON Schema** is a vocabulary for describing the structure of a JSON document: which fields are required, what types they must have, what format strings must match. When you call `jsonschema.validate(response_body, schema)`, it checks that:

- All required fields are present (e.g., `id`, `firstName`, `email`)
- Each field has the correct type (`id` is an integer, not a string)
- No required field has been silently removed or renamed

Example: if a developer renames `firstName` to `first_name` in the backend, every `assert response["firstName"]` would raise a `KeyError`. But with JSON Schema, a single validate call catches the contract break and produces a clear error: `'firstName' is a required property`. This is called **contract testing** — verifying that the API still honors the agreed-upon shape.

---

### Q4. What is a pytest fixture and what is fixture scope?

A **pytest fixture** is a function decorated with `@pytest.fixture` that provides setup (and optional teardown) to test functions via dependency injection. When a test declares a fixture as a parameter, pytest creates the fixture, passes it to the test, and handles cleanup.

**Fixture scope** controls how often the fixture is created and destroyed:

| Scope | Created | Destroyed |
|---|---|---|
| `function` (default) | Before each test | After each test |
| `class` | Once per test class | After the class |
| `module` | Once per module | After the module |
| `session` | Once per entire run | After all tests finish |

Choosing the right scope is a performance and correctness tradeoff: broad scope = faster (fewer setups), but shared state must be handled carefully.

---

### Q5. Why use session scope for the APIClient fixture?

`APIClient` wraps a `requests.Session`. Creating a session involves initializing connection pools, setting headers, and configuring timeouts. There is no reason to recreate this object 43 times — one instance can serve all tests safely because `APIClient` is stateless (it does not store response data between calls).

Using `scope="session"` means one `requests.Session` is created once and reused. This:
- Allows TCP connection reuse via HTTP keep-alive (faster requests)
- Reduces overhead from repeated object initialization
- Avoids the risk of hitting connection limits when creating many sessions

---

### Q6. What is requests.Session and why is it better than requests.get()?

`requests.get()` creates a new connection for every call and discards it after. `requests.Session` maintains a connection pool and reuses existing TCP connections via HTTP keep-alive — subsequent requests to the same host are significantly faster.

Additionally, a `Session` lets you:
- Set default headers once (`session.headers.update(...)`) — applied to every request
- Set default timeouts
- Share cookies across requests (important for auth workflows)
- Configure retry adapters

In this project, `APIClient` sets `Content-Type: application/json` once on the session, so every POST/PUT/PATCH automatically includes the correct header without repeating it in every test.

---

### Q7. What is the auth_token fixture and why is it session-scoped?

`auth_token` is a session-scoped fixture defined in `conftest.py`. It calls `POST /auth/login` with valid credentials once, extracts the `accessToken` from the response, and caches it. Every test that needs a token receives the same cached value.

Without session scope, `auth_token` would call `/auth/login` for every auth test — 10 separate login calls for `test_auth.py` alone, plus additional calls if other test files use the token. This is wasteful and potentially causes rate-limiting. Session scope reduces 10+ login calls to exactly 1.

The fixture depends on the `api` fixture: `def auth_token(api)` — pytest resolves this dependency automatically.

---

### Q8. What is parametrize in pytest and when do you use it?

`@pytest.mark.parametrize` is a decorator that runs the same test function multiple times with different input values. Instead of writing:

```python
def test_user_1(): ...
def test_user_2(): ...
def test_user_3(): ...
```

You write:

```python
@pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5, 6])
def test_get_user_by_id(api, user_id):
    resp = api.get(f"/users/{user_id}")
    assert resp.status_code == 200
```

This generates 6 test cases from one function. Use parametrize when:
- The same logic must be verified across multiple inputs
- Testing a matrix of valid/invalid inputs
- Testing multiple users, IDs, or error scenarios without copy-pasting

In this project, parametrize is used for user IDs 1–6, creating 3 different users via POST, and testing multiple invalid login credential combinations.

---

### Q9. What is the difference between PUT and PATCH?

| Method | Semantics | Body |
|---|---|---|
| `PUT` | Full replacement — replace the entire resource | Must include all fields |
| `PATCH` | Partial update — modify only specified fields | Include only changed fields |

Example: If a user has `{id, firstName, lastName, email, age}`:
- `PUT /users/2` with `{firstName: "Jane"}` would replace the resource — `lastName`, `email`, `age` might be cleared or reset
- `PATCH /users/2` with `{firstName: "Jane"}` updates only `firstName`, leaving all other fields unchanged

In practice, many APIs (including DummyJSON) are lenient — their PUT also acts like PATCH. But the semantic distinction matters for API design and test design: PUT tests should verify the full response body, PATCH tests should verify only the modified field(s) changed while others are preserved.

---

### Q10. Why does DELETE in DummyJSON return 200 with a body instead of 204?

HTTP conventions say DELETE *can* return:
- `204 No Content` — success, no body
- `200 OK` — success, with a response body

DummyJSON returns `200` with `{id: 1, ..., isDeleted: true}` because it is a **mock/fake API** designed for testing and demonstration. Returning the deleted object with a confirmation flag is more useful for learning and testing — it lets you verify *which* resource was deleted and confirm the `isDeleted` flag.

In real-world APIs, both approaches are valid. `204` is more RESTfully strict. `200` with a body is more informative for clients. Testing `isDeleted: true` in the response body is a stronger assertion than just checking `status_code == 200`.

---

### Q11. What is a response time SLA test and why include it in a test suite?

An **SLA (Service Level Agreement) test** asserts that the API responds within a defined time budget. In this project:

```python
assert resp.elapsed.total_seconds() < 2.0
```

This checks that the response arrived in under 2 seconds.

Why include it:
- Performance regressions are invisible to functional tests — an API can return correct data but take 10 seconds instead of 0.5 seconds
- Catching slow responses in CI prevents performance degradations from reaching production
- It documents the expected performance contract alongside functional requirements

Caveat: SLA tests against external APIs (like DummyJSON) can be flaky due to network variance. For internal APIs, SLA tests are more reliable and more valuable.

---

### Q12. What is the conftest.py file used for?

`conftest.py` is a special pytest file that is automatically discovered and loaded before any tests in the same directory (and subdirectories). It is used for:

1. **Shared fixtures** — fixtures defined here are available to all test files in the same directory tree without explicit imports
2. **Plugins and hooks** — custom pytest hooks (`pytest_runtest_makereport`, etc.)
3. **Shared configuration** — e.g., setting up a database connection, configuring logging

In this project, `conftest.py` defines `api` and `auth_token` so every test file can use them without any import statement. pytest's fixture injection discovers them by name automatically.

---

### Q13. How would you run just the smoke tests?

Smoke tests are marked with `@pytest.mark.smoke` in the test files. Run them with:

```bash
pytest -m smoke -v
```

The `pytest.ini` file registers the `smoke` marker to avoid `PytestUnknownMarkWarning`:

```ini
[pytest]
markers =
    smoke: quick sanity checks
```

Smoke tests typically include only the most critical, fast-running checks — the ones you run on every commit to get a 30-second "is it alive?" signal before running the full regression suite.

---

### Q14. How would you point these tests at a staging environment?

The `utils/env.py` file loads `BASE_URL` from the environment using `python-dotenv`. Override it at runtime:

```bash
BASE_URL=https://staging.myapp.com pytest tests/ -v
```

Or create a `.env.staging` file and export before running:

```bash
export BASE_URL=https://staging.myapp.com
pytest tests/ -v
```

In CI (e.g., GitHub Actions), set the environment variable in the workflow:

```yaml
env:
  BASE_URL: ${{ secrets.STAGING_URL }}
```

Because `APIClient` reads `BASE_URL` once at initialization, and `api` is session-scoped, all 43 tests run against the same target URL.

---

### Q15. What is genson and how could it be used in this project?

**Genson** is a Python library that generates JSON Schema from example JSON data. Instead of writing a schema by hand, you feed it one or more JSON examples and it infers the schema.

Usage:

```python
from genson import SchemaBuilder

builder = SchemaBuilder()
builder.add_object({"id": 1, "firstName": "Emily", "email": "emily@example.com"})
print(builder.to_schema())
# {"$schema": "...", "type": "object", "properties": {"id": {"type": "integer"}, ...}, "required": ["id", "firstName", "email"]}
```

In this project, genson could be used to:
1. Bootstrap the initial schema files by running it against live API responses
2. Update schemas when the API changes — generate a new schema from the updated response and diff it against the current schema
3. Add a utility script that auto-generates schemas in the `schemas/` directory

---

### Q16. How would you add authentication headers to protected endpoints?

If the API requires a Bearer token on every request, add it to the session headers in `APIClient`:

```python
def set_auth_token(self, token: str):
    self.session.headers.update({"Authorization": f"Bearer {token}"})
```

Then in `conftest.py`, after creating the `auth_token` fixture, call:

```python
@pytest.fixture(scope="session")
def authenticated_api(api, auth_token):
    api.set_auth_token(auth_token)
    return api
```

Tests requiring auth use `authenticated_api` instead of `api`. This keeps unauthenticated tests (like testing login itself, or 401 error tests) separate from authenticated tests.

---

### Q17. What is the difference between jsonschema.validate() and manually asserting fields?

**Manual assertion:**
```python
assert "id" in body
assert isinstance(body["id"], int)
assert "firstName" in body
assert isinstance(body["firstName"], str)
assert "email" in body
```

This is verbose, incomplete (easy to forget fields), and does not produce a clear error message about *which* contract was violated.

**jsonschema.validate():**
```python
jsonschema.validate(body, schema)
```

This reads the schema from a JSON file, validates all fields, types, and required properties in one call, and raises `ValidationError` with a precise message: `'email' is a required property` or `'id' is not of type 'integer'`. 

The schema file is also documentation — it describes the expected API contract in a language-agnostic, shareable format. Multiple teams (frontend, backend, QA) can reference the same schema file.

---

### Q18. How would you handle flaky tests against an external API?

External APIs introduce nondeterminism: network timeouts, transient 5xx errors, rate limits. Strategies:

1. **Retry logic** — use `urllib3.util.retry.Retry` with `requests.adapters.HTTPAdapter` to automatically retry on 5xx and connection errors
2. **pytest-rerunfailures** — add `@pytest.mark.flaky(reruns=3)` to tests that hit external APIs
3. **Wider SLA thresholds** — use 5s instead of 2s for external APIs with variable latency
4. **Mock for unit tests, real calls for integration tests** — use `responses` or `pytest-httpserver` to mock the API in fast unit tests, reserve real API calls for a separate integration suite
5. **Separate CI jobs** — run flaky external-API tests on a longer schedule (nightly) rather than on every commit

---

### Q19. How would you extend this to test a GraphQL API?

GraphQL uses `POST` requests with a JSON body containing a `query` field. The `APIClient` already supports `post()`. Extension steps:

1. Add a `graphql()` helper method to `APIClient`:
```python
def graphql(self, query: str, variables: dict = None):
    return self.post("/graphql", json={"query": query, "variables": variables or {}})
```
2. Write test files with GraphQL query strings
3. Validate the `data` field in the response (GraphQL always returns `{"data": {...}, "errors": [...]}`)
4. Use JSON Schema to validate the shape of `response["data"]["users"]`, etc.
5. Test error cases by sending malformed queries and asserting `response["errors"]` is non-empty

The session-scoped fixtures and schema validation approach carry over unchanged.

---

### Q20. What does --html=report.html produce and how is it useful?

`pytest-html` generates a self-contained HTML file with:

- **Summary bar** — counts of passed, failed, error, skipped tests
- **Test results table** — each test with its name, duration, and pass/fail status
- **Expandable failure details** — full traceback for any failed test, including the request/response if captured
- **Environment section** — Python version, pytest version, OS
- **Duration chart** — which tests are slowest

Usefulness:
- Share with non-technical stakeholders (PM, developers) without needing terminal access
- Attach as a CI artifact (GitHub Actions `upload-artifact`) for historical records
- Identify slow tests by sorting the duration column
- Debug failures by reading the inline traceback

---

### Q21. How does the CI pipeline work for this project?

A typical GitHub Actions workflow (`.github/workflows/test.yml`) would:

```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --html=report.html --self-contained-html
      - uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: report.html
```

On every push and pull request:
1. GitHub spins up a fresh Ubuntu runner
2. Python and dependencies are installed
3. All 43 tests run against the live DummyJSON API
4. The HTML report is uploaded as a downloadable artifact
5. If any test fails, the workflow job fails and blocks the PR from merging (if branch protection is configured)

---

### Q22. How would you add negative schema tests (verify bad data is rejected)?

For APIs with input validation, add tests that send malformed requests and assert the error response schema. Example:

```python
@pytest.mark.parametrize("bad_payload,expected_status", [
    ({"firstName": 123}, 400),           # wrong type
    ({"email": "not-an-email"}, 400),    # invalid format
    ({}, 400),                           # missing required fields
])
def test_create_user_invalid_input(api, bad_payload, expected_status):
    resp = api.post("/users/add", json=bad_payload)
    assert resp.status_code == expected_status
    body = resp.json()
    jsonschema.validate(body, error_response_schema)  # validate error shape too
```

This tests the API's *rejection* behavior, not just its happy path. Also add a `error_response_schema.json` that describes the expected shape of 400 error responses: `{message: string}`.

---

### Q23. What would you change if the API required OAuth2?

OAuth2 adds an authorization code flow before you can get an access token. Changes needed:

1. **`utils/env.py`** — add `CLIENT_ID`, `CLIENT_SECRET`, `TOKEN_URL` environment variables
2. **`conftest.py` `auth_token` fixture** — replace the simple login call with an OAuth2 client credentials flow:
```python
import requests

resp = requests.post(TOKEN_URL, data={
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
})
return resp.json()["access_token"]
```
3. **`APIClient`** — add `set_auth_token()` method and call it with the fixture token
4. **Token refresh** — for long-running test suites, detect 401 responses and re-fetch the token

For password grant (username + password OAuth2 flow), the change is minimal — replace the `POST /auth/login` call with a `POST` to the OAuth2 token endpoint with the correct `grant_type`.

---

### Q24. How would you parallelize these tests with pytest-xdist?

`pytest-xdist` runs tests in parallel across multiple workers.

Install:
```bash
pip install pytest-xdist
```

Run with 4 parallel workers:
```bash
pytest tests/ -v -n 4
```

Run with one worker per CPU core:
```bash
pytest tests/ -v -n auto
```

**Considerations for this project:**

- The `api` and `auth_token` fixtures are `scope="session"`. With xdist, each worker gets its own session — so `auth_token` will be created once per worker, not once globally. This means 4 workers = 4 login calls (not 43, but not 1 either).
- Tests must be independent (no shared mutable state between tests) — this project already satisfies that requirement.
- DummyJSON is an external API; parallelism will increase concurrent request rate. Ensure the API allows it.
- Expected speedup: 43 tests across 4 workers ≈ 3× faster wall-clock time.

---

### Q25. What is the difference between integration tests and contract tests?

**Integration tests** verify that two systems work together correctly. In this project, every test is an integration test — it sends a real HTTP request to a real API and checks the real response.

**Contract tests** verify that the *interface agreement* (the contract) between two parties is honored, independent of the actual implementation. A contract test does not necessarily call the live API — it might mock the API and verify only that the request your code sends conforms to the contract, and that the response your code handles is properly structured.

| Dimension | Integration Test | Contract Test |
|---|---|---|
| Calls live API? | Yes | Not necessarily |
| Speed | Slower (network) | Fast (mocked) |
| What it verifies | Functional behavior | Schema/interface agreement |
| Tool examples | Pytest + Requests | Pact, Dredd, jsonschema |
| When it fails | API is down or wrong | Contract has changed |

This project blends both: it calls the live DummyJSON API (integration) AND validates JSON Schema (contract). Adding `jsonschema.validate()` to each test makes them partial contract tests — they would catch a contract break even if the status code remained 200.

For full contract testing, use [Pact](https://docs.pact.io/) — it records interactions and verifies them against the provider without requiring the live API to be available in CI.

---

*End of DEEP_DIVE.md*
