import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.env import BASE_URL, DEFAULT_TIMEOUT


class APIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.timeout = DEFAULT_TIMEOUT
        self._retry_on_transient_failures()

    def _retry_on_transient_failures(self):
        # The suite runs against a public API from a shared CI runner, so a rate limit
        # or a 502 is a fact of life rather than a defect in the code under test.
        # 4xx responses are never retried; those are the results being asserted on.
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, endpoint: str, params: dict = None) -> requests.Response:
        return self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            timeout=self.timeout,
        )

    def post(self, endpoint: str, payload: dict = None) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=self.timeout,
        )

    def put(self, endpoint: str, payload: dict = None) -> requests.Response:
        return self.session.put(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=self.timeout,
        )

    def patch(self, endpoint: str, payload: dict = None) -> requests.Response:
        return self.session.patch(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=self.timeout,
        )

    def delete(self, endpoint: str) -> requests.Response:
        return self.session.delete(
            f"{self.base_url}{endpoint}",
            timeout=self.timeout,
        )
