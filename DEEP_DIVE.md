# A deep read of api-test-pytest

The README is the short version: what this is, how to run it, why the schemas
matter. This is the long version, for someone who has to work in the code, review
it, or decide whether the approach is worth copying.

It covers what the project is at three levels of detail, every file and what it
is for, the architecture and the reasoning behind it, how to run and extend it,
the decisions I would defend and the ones I would not, and the questions people
actually ask.

- [1. What it is](#1-what-it-is)
- [2. Every file, and why it exists](#2-every-file-and-why-it-exists)
- [3. How a single test executes](#3-how-a-single-test-executes)
- [4. The client](#4-the-client)
- [5. The fixtures](#5-the-fixtures)
- [6. The schema layer](#6-the-schema-layer)
- [7. What the 43 tests actually cover](#7-what-the-43-tests-actually-cover)
- [8. Markers, and running a subset](#8-markers-and-running-a-subset)
- [9. The CI pipeline](#9-the-ci-pipeline)
- [10. The published report](#10-the-published-report)
- [11. Pointing it at your own API](#11-pointing-it-at-your-own-api)
- [12. Decisions, and the ones I would argue about](#12-decisions-and-the-ones-i-would-argue-about)
- [13. What this does not do](#13-what-this-does-not-do)
- [14. FAQ](#14-faq)

---

## 1. What it is

### If you do not write tests

Every app you use is really two programs. There is the part you see, and behind
it a server that holds the actual data. They talk over the internet in a fixed
format: the app asks *"give me user 5"*, the server answers with a block of text
containing that user's name, email and so on.

That conversation has rules. The answer must arrive quickly, it must say whether
it worked, and the fields must be named the things the app expects. If the server
team renames `firstName` to `first_name` one afternoon, the server is still
working perfectly by its own lights, and every app talking to it breaks.

This project is 43 small programs that have that conversation on purpose, several
times a minute, and complain loudly the moment any of those rules stops holding.
It runs automatically every time the code changes and again every night, and it
publishes the results to a web page anyone can open.

### If you write tests but not this kind

It is a Pytest suite against [DummyJSON](https://dummyjson.com), a free public
REST API, covering user CRUD and authentication. There is no browser, no
Selenium, no UI: everything is HTTP request in, JSON out.

Three things are worth the attention:

**Responses are validated against JSON Schema, not against individual fields.**
`schemas/` holds four schema files. A test does
`jsonschema.validate(instance=resp.json(), schema=schema)` and that single call
checks every field name, every type, and every required key at once. Asserting
`resp.json()["id"] == 1` checks one field and tells you nothing about the other
thirty.

**Expensive setup happens once per run, not once per test.** `api` and
`auth_token` are session-scoped fixtures, so the suite builds one HTTP session
and logs in once, rather than forty-three times.

**The results go somewhere people will look.** CI publishes an HTML report to
GitHub Pages at a stable URL and comments a summary on the pull request. A test
result nobody opens is not doing much.

### If you are reviewing the design

The interesting choices are all about a suite that runs against a shared public
service from a shared CI runner, which is an environment with two kinds of
failure in it: the API is wrong, and the environment is having a moment. Almost
every decision here is about telling those apart.

The retry adapter retries 429 and 5xx and never retries 4xx, because 4xx is what
the negative tests assert on and a retried 400 is a test that no longer tests
anything. The response-time ceiling is five seconds, not two, because two
seconds on a shared runner fails for reasons that have nothing to do with the
API, and a suite that cries wolf gets ignored, at which point it is worse than
no suite. The nightly cron exists because the failure this suite is best at
catching (the upstream contract changing) has no commit attached to it and would
otherwise sit undetected until someone happened to push.

The design principle, if there is one: **a test that fails for reasons unrelated
to the thing it is testing is worse than no test**, because it costs attention
every time and eventually gets muted.

---

## 2. Every file, and why it exists

```
api-test-pytest/
├── tests/
│   ├── conftest.py                    fixtures, and the report's presentation
│   ├── test_users_get.py              GET: list, single, 404, schema, timing
│   ├── test_users_post.py             POST: create
│   ├── test_users_put_delete.py       PUT, PATCH, DELETE
│   └── test_auth.py                   login: valid, incomplete, wrong
├── utils/
│   ├── api_client.py                  requests.Session with retry and timeout
│   └── env.py                         BASE_URL and DEFAULT_TIMEOUT
├── schemas/
│   ├── user_schema.json               one user object
│   ├── user_list_schema.json          the paginated list response
│   ├── login_response_schema.json     the auth response
│   └── create_user_response_schema.json
├── .github/
│   ├── workflows/api-tests.yml        the pipeline
│   └── scripts/summarise.py           JUnit XML into a PR comment
├── pytest.ini                         markers and default flags
├── requirements.txt                   five pinned dependencies
└── .env.example                       the two variables you might set
```

### `tests/conftest.py`

Three fixtures and three pytest-html hooks.

`api` builds one `APIClient` for the whole session. `auth_token` depends on it,
logs in once, and hands back the access token. `load_schema` returns a function
that reads a file out of `schemas/` by name.

`load_schema` being a fixture at all is the result of a small cleanup. The same
six lines of "open the schema file and json.load it" had been copy-pasted into
three test modules, each with its own `Path(__file__).parent.parent / "schemas"`
computation. Moving the schema directory would have meant fixing it in three
places and probably missing one. It is now defined once, and the three modules
that used to compute paths no longer import `json` or `pathlib` at all.

The bottom half of the file is about the published report, which is covered in
[section 10](#10-the-published-report).

### `utils/api_client.py`

A thin wrapper over `requests.Session` with five methods, one per HTTP verb. It
prefixes `BASE_URL`, sets `Content-Type`, applies the timeout, and mounts a
retry adapter. That is all it does, on purpose: a test client that starts making
decisions about responses becomes a second place where test logic lives.

### `utils/env.py`

Six lines. Reads `.env` if present, exposes `BASE_URL` and `DEFAULT_TIMEOUT`
with defaults. The defaults are what make `git clone && pytest` work with no
configuration at all, which matters more than it sounds: a suite you have to
configure before you can see it run is a suite most people never see run.

### `schemas/*.json`

Draft-07 JSON Schema documents. They are separate files rather than dicts inside
test modules for the same reason API contracts live in an OpenAPI file rather
than in the handler: they *are* the contract, they change on a different schedule
from the tests, and a diff of one is a meaningful thing to review.

### `.github/scripts/summarise.py`

Reads the JUnit XML pytest emits and writes a short Markdown summary. The
workflow feeds that into the pull request comment. It exists so the comment says
which tests failed and why, rather than "the job failed, go read the log".

---

## 3. How a single test executes

Take `test_single_user_matches_schema`, which is three lines long and touches
most of the codebase.

```python
@pytest.mark.users
def test_single_user_matches_schema(self, api, load_schema):
    resp = api.get("/users/1")
    schema = load_schema("user_schema.json")
    jsonschema.validate(instance=resp.json(), schema=schema)
```

**Collection.** Pytest reads `pytest.ini`, finds `testpaths = tests`, imports
every `test_*.py`, and registers this method. The `@pytest.mark.users` decorator
attaches a marker, which is what `pytest -m users` later filters on.

**Fixture resolution.** The signature asks for `api` and `load_schema`. Pytest
looks them up in `conftest.py`, sees both are `scope="session"`, and checks
whether either already exists for this run. If this is the first test that wanted
`api`, it is constructed now; every subsequent test gets the same object.

**The request.** `api.get("/users/1")` becomes
`session.get("https://dummyjson.com/users/1", params=None, timeout=10)`. The
session already carries the `Content-Type` header and the retry adapter, so if
DummyJSON answers 429 the adapter retries up to three times with backoff, and the
test never sees it. If it answers 404, the adapter passes it straight through,
because 4xx is a real answer.

**The assertion.** `jsonschema.validate` walks the response against the schema
and raises `ValidationError` on the first mismatch. Pytest catches that as a
failure and prints the path to the offending field.

The whole thing is three lines because everything expensive or repeated has been
pushed into a fixture or the client. That is the shape I want a test to have:
what is being checked, and nothing about how to get there.

---

## 4. The client

```python
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    raise_on_status=False,
)
```

Four things in there are deliberate.

**`status_forcelist` has no 4xx in it.** This is the important one. Six of the
43 tests assert that a bad request comes back 400 and that a missing user comes
back 404. If 4xx were retried, those tests would take four times as long and
still pass, and the retry would be quietly hiding whether the API is
*consistently* rejecting or just did once.

**`backoff_factor=0.5`** gives 0.5s, 1s, 2s between attempts. Enough for a rate
limit window to move, short enough that a genuinely dead endpoint fails the suite
in seconds rather than minutes.

**`allowed_methods` includes the non-idempotent verbs.** urllib3 will not retry
POST or DELETE by default, for a very good reason: retrying a create can create
twice. Here the API under test is a demo service that does not persist writes, so
the risk does not exist and the flakiness reduction is worth having. **If you
point this at a real service, take POST, PUT, PATCH and DELETE back out of that
list.** This is the single line in the repository most likely to be wrong for
your situation.

**`raise_on_status=False`** means the adapter hands back the final response
rather than raising, so the test can assert on the status code itself.

The timeout is separate and always applied. A request with no timeout can hang
until the CI job's own limit kills it, at which point you get a cancelled job
instead of a failed test, and a cancelled job tells you nothing.

---

## 5. The fixtures

```python
@pytest.fixture(scope="session")
def api() -> APIClient:
    return APIClient()

@pytest.fixture(scope="session")
def auth_token(api: APIClient) -> str:
    resp = api.post("/auth/login", {...})
    assert resp.status_code == 200
    return resp.json()["accessToken"]
```

Pytest has four fixture scopes: `function` (the default, rebuilt for every test),
`class`, `module`, and `session` (built once for the whole run).

Both of these are session-scoped, which turns 43 logins into one and 43
`requests.Session` objects into one. The session object matters more than it
looks: it keeps the TCP connection alive between requests, so the suite is not
paying for a new TLS handshake 43 times.

Two things follow from session scope that are worth knowing before you copy it.

**Session-scoped fixtures make tests order-dependent if they hold mutable
state.** These do not: `api` is stateless configuration, and `auth_token` is a
string. If you add a fixture that caches a created user id and a later test
deletes it, you have built an ordering dependency, and it will surface as a
failure that only happens under `-p no:randomly` or on someone else's machine.

**The assert inside `auth_token` is deliberate.** If login fails, every test that
depends on the token errors during setup rather than failing during the test.
Pytest reports those differently, and the difference is exactly the one you want:
*setup broke* is a different problem from *the thing under test is wrong*.

---

## 6. The schema layer

This is the part of the suite I would keep if I had to throw the rest away.

A status-code assertion tells you the server answered. It does not tell you the
answer was the right *shape*. Consider a backend team renaming a field:

```diff
- {"id": 1, "firstName": "Emily", "email": "emily@x.com"}
+ {"id": 1, "first_name": "Emily", "email": "emily@x.com"}
```

`assert resp.status_code == 200` passes. `assert resp.json()["id"] == 1` passes.
The suite is green, and every mobile client reading `firstName` is now showing a
blank name in production.

`schemas/user_schema.json` fails on the commit that did it, and the error names
the missing field:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "User",
  "type": "object",
  "required": ["id", "firstName", "lastName", "email"],
  "properties": {
    "id":        { "type": "integer", "minimum": 1 },
    "firstName": { "type": "string", "minLength": 1 },
    "lastName":  { "type": "string", "minLength": 1 },
    "email":     { "type": "string" }
  }
}
```

Three practical notes:

**Schemas describe what you depend on, not everything present.** DummyJSON's user
object has a couple of dozen fields. `required` lists the four that a consumer
would break without. Requiring all of them would make the schema fail whenever
the API added something, which is not a break and should not be a red build.

**`additionalProperties` is left permissive on purpose.** Setting it to `false`
turns "the API added a field" into a failure. For a suite watching an upstream
service you do not control, that is noise. For a suite guarding an API you own
and publish, it is a feature, and you should turn it on.

**Schemas are diffable and reviewable.** When one changes in a pull request, the
diff is the contract change, in isolation, which is a much better review artifact
than the same change hidden inside a test method.

---

## 7. What the 43 tests actually cover

| File | Tests | What it checks |
|---|---:|---|
| `test_users_get.py` | 16 | List with pagination, that page 2 shares no ids with page 1, single user by id, id echoed back, 404 for a missing user, an error message on the 404, schema on both list and single, a response-time ceiling, and six parametrized ids |
| `test_users_post.py` | 7 | Create returns 201, response matches the create schema, the payload comes back, an id is generated, and several users parametrized |
| `test_users_put_delete.py` | 10 | Full update, partial update, id preserved through both, delete sets `isDeleted`, and parametrized deletes |
| `test_auth.py` | 10 | Valid login, a non-empty access token, the login schema, missing password, missing username, empty body, wrong password, and the token fixture itself |
| **Total** | **43** | |

The one I would point at in a review is
`test_list_users_page2_has_different_users`. It is the only test that checks
pagination is *doing something* rather than merely returning 200 with six items.
An off-by-one in a `skip` parameter, which is a genuinely common backend bug,
returns a perfectly valid response with the wrong contents. Only comparing the
two pages catches it.

The one I am least fond of is
`test_list_users_responds_within_the_agreed_ceiling`. Wall-clock assertions
against a public API from a shared runner are inherently a bit soft. It is kept
because a response that suddenly takes four seconds when it used to take two
hundred milliseconds is worth knowing about, and the comment in the file is
explicit that it is a smoke alarm rather than a performance test. Real
performance work needs percentiles over many samples and a dedicated environment.

---

## 8. Markers, and running a subset

```ini
markers =
    smoke: critical path only, the subset you run on every commit
    auth: login and token tests
    users: user CRUD tests
```

```bash
pytest                      # all 43
pytest -m smoke             # 8, the critical path
pytest -m auth              # 10
pytest -m users             # 33
pytest -m "not smoke"       # everything else
pytest tests/test_auth.py -v
```

There used to be a fourth marker, `regression`, advertised in the README and
carried by exactly zero tests, so `pytest -m regression` collected nothing and
exited successfully. A command that runs no tests and reports success is a
genuinely bad failure mode, because it looks like a pass. It is gone, and the
comment in `pytest.ini` says why so that nobody helpfully adds it back.

The rule worth keeping: **every marker in `pytest.ini` must be carried by at
least one test.** It is easy to check and it prevents that whole class of
silence.

---

## 9. The CI pipeline

`.github/workflows/api-tests.yml`, on push to main, on pull requests, on a
nightly cron at 06:00 UTC, and on demand.

The nightly run is the one that earns its keep. The failure this suite is best
at catching is the upstream API changing shape, and that has no commit attached
to it. Without a schedule you find out on whatever day someone next happens to
push, and then spend the first twenty minutes assuming their change caused it.

Three details in the workflow are worth pointing at.

**`continue-on-error: true` on the test step, with an explicit failure step at
the end.** Without this, a failing test aborts the job and the report never gets
published, which means the one run you most want to look at is the one with no
artifact. The tests run, the report publishes, the summary comments, and *then*
the job fails.

**Reports are published per pull request.** `destination_dir` resolves to
`pr-<number>/` for pull requests and the root for main, with `keep_files: true`,
so a PR's report does not overwrite the published main one.

**The PR comment is updated, not appended.** The script looks for an existing
comment containing the marker `<!-- api-test-report -->` and edits it. Ten pushes
to a branch leave one comment showing the current state, rather than ten comments
of which nine are historical noise.

**`concurrency` with `cancel-in-progress`.** Pushing twice quickly cancels the
first run. Two jobs publishing to the same Pages branch at once is a race, and
this removes it.

---

## 10. The published report

The bottom half of `conftest.py` is three pytest-html hooks, and they exist
because the report is linked from a portfolio and read by people who did not run
it.

```python
def pytest_html_report_title(report):
    report.title = "REST API Test Suite, by Priya Bhagoriya"
```

pytest-html names the page after the output file by default. The output file is
`site/index.html`, so the page was titled "index.html" to everyone who opened it.

```python
def pytest_metadata(metadata):
    for noise in ("JAVA_HOME", "Plugins"):
        metadata.pop(noise, None)
    metadata["Suite"] = "43 tests over CRUD and auth, with JSON Schema contracts"
    metadata["API under test"] = os.environ.get("BASE_URL", "https://dummyjson.com")
```

The default metadata table lists `JAVA_HOME` and every installed plugin, neither
of which says anything about this suite. What replaces them is what a reader
actually needs: what was tested, against what, at which commit, from which CI
run.

`pytest_html_results_summary` adds a sentence above the results explaining the
schema layer and linking to `schemas/`, because the interesting thing about the
report is not the pass count.

None of this changes whether a test passes. It changes whether the artifact is
worth linking to, which for a published report is most of the point.

---

## 11. Pointing it at your own API

```bash
BASE_URL=https://staging.myapp.com pytest
```

Everything routes through `utils/env.py`, so that variable is the only switch.
Realistically you will then need to do four things:

1. **Rewrite the endpoints.** `/users`, `/auth/login` and the rest are
   DummyJSON's. They live in the test modules, which is fine at this size; past
   roughly a hundred tests, move them into an `endpoints.py` so a path change is
   one edit.
2. **Regenerate the schemas.** Point something at a real response and trim the
   `required` list down to the fields a consumer would actually break without.
3. **Take the write verbs out of `allowed_methods`.** See
   [section 4](#4-the-client). Retrying a POST against a service that persists
   writes will create duplicates.
4. **Add data setup.** This is the real gap, and it is covered next.

---

## 12. Decisions, and the ones I would argue about

**`requests`, not `httpx`.** `httpx` is the better library on paper and has
async. These are synchronous integration tests where every request must complete
before its assertion, so async buys nothing but a colour-function problem, and
`requests` is what any reviewer already knows.

**A public API rather than a mock server.** A mock would make the suite
deterministic and fast, and would also make it test my mock rather than an API.
The point of these tests is to catch a real service changing under me, which a
mock cannot do by construction. The cost is that a DummyJSON outage fails the
build, and I would accept that trade differently in a repository where the build
gates a release.

**Pinned dependencies.** Five lines in `requirements.txt`, all exact. A test
suite that changes behaviour because a transitive dependency shipped on a
Tuesday is a test suite people stop trusting.

**Classes as containers, not for shared state.** `TestGetUsers` and `TestAuth`
group related tests and nothing else; there is no `setup_method`, no `self`
state. State goes in fixtures where the scope is explicit and pytest manages the
lifecycle.

**What I would argue about:** 43 tests for one resource plus auth is arguably too
many, and some of the parametrized ids are close to testing the same thing six
times. The counter-argument is that they are nearly free to run and each one
names a distinct property. I would not write it the same way for an API with
forty resources.

---

## 13. What this does not do

Being explicit about this, because a template that hides its gaps is worse than
one that names them.

**No data setup or teardown.** Tests assume users 1 to 6 exist and that the API
is idempotent enough to run in any order. A real service needs seeded fixtures,
a per-test database transaction, or a cleanup step, and that is the first thing
you will have to build.

**No test isolation between runs.** DummyJSON does not persist writes, so a POST
in one run has no effect on the next. Against a real service, the create tests
will accumulate rows.

**No auth beyond the login flow.** `auth_token` is fetched and asserted to be a
string. Nothing uses it to call a protected endpoint, because DummyJSON's
protected endpoints are not interesting. On a real API this is where most of the
work would be.

**No contract test against a spec.** The schemas are hand-written and could drift
from a real OpenAPI document. Generating them from a spec would close that gap
and is what I would do next on a service that publishes one.

**No performance testing.** One wall-clock ceiling on one endpoint, explicitly
labelled a smoke alarm. Anything real needs its own tool.

---

## 14. FAQ

**Why not just check status codes?**
Because a 200 means the server answered, not that it answered correctly. The
whole [schema section](#6-the-schema-layer) is about this one gap.

**Why session-scoped fixtures rather than function-scoped?**
43 logins instead of one, 43 TLS handshakes instead of one, for no benefit. The
things being shared are immutable, so the usual argument against session scope
does not apply here.

**Does the retry adapter hide real failures?**
It hides transient ones on purpose and cannot hide a 4xx, because 4xx is not in
the forcelist. If the API is genuinely down, three retries with backoff take a
few seconds and then fail. The thing to watch is `allowed_methods`, which
includes the write verbs and should not against a service that persists.

**Why is the response-time ceiling five seconds? That is enormous.**
It is, and that is the point. It is a smoke alarm for "something has gone
badly wrong", not a performance budget. It was two seconds, and it failed on
slow CI runners often enough that people started ignoring red builds, which is
the actual danger.

**Why publish to GitHub Pages rather than upload an artifact?**
Artifacts expire, sit inside a zip, and need a GitHub login to reach. A URL you
can put in a README and hand to someone is a different kind of object.

**Why does the workflow use `continue-on-error` on the tests?**
So that a failing run still publishes its report. The job still fails, at the
last step. Without it the run you most want to inspect is the one that produced
nothing.

**How do I add a test?**
Put it in the matching `test_*.py`, ask for the fixtures you need in the
signature, and add a marker. If it needs a new response shape checked, add a
schema file rather than a pile of field assertions.

**Can this run in parallel?**
`pytest-xdist` would work, and the session fixtures would be built once per
worker rather than once overall, so you would trade a few extra logins for wall
clock. At 13 seconds it is not worth it. At three minutes it would be.

**Why DummyJSON specifically?**
Free, no signup, no key, stable, and it supports the whole verb set including
auth. Anyone who clones this can run it immediately, which is the thing that
makes a template useful rather than aspirational.

**Is 43 tests a lot or a little?**
For one resource and an auth flow, it is thorough. For a real product it is a
starting point. The number is not the interesting part; the ratio of schema
checks to field assertions is.
