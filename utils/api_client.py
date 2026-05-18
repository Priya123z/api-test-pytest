import requests
from utils.env import BASE_URL, DEFAULT_TIMEOUT


class APIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.timeout = DEFAULT_TIMEOUT

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
