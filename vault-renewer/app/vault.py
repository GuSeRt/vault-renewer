import time, requests
from .jsonlog import jlog

class VaultClient:
    def __init__(self, addr: str, timeout: float = 5.0, retries: int = 3):
        self.addr, self.timeout, self.retries = addr, timeout, retries

    def _req(self, method: str, path: str, token: str, **kw) -> requests.Response:
        kw.setdefault("timeout", self.timeout)
        headers = kw.pop("headers", {})
        headers["X-Vault-Token"] = token
        url = f"{self.addr}{path}"
        last = None
        for i in range(self.retries):
            try:
                r = requests.request(method, url, headers=headers, **kw)
                r.raise_for_status()
                return r
            except Exception as e:
                last = e
                time.sleep(min(2**i, 5))
        raise last

    def lookup_self(self, token: str) -> dict:
        r = self._req("GET", "/v1/auth/token/lookup-self", token)
        return r.json()["data"]

    def renew_self(self, token: str, increment_sec: int) -> dict:
        j = {"increment": f"{increment_sec}s"}
        r = self._req("POST", "/v1/auth/token/renew-self", token, json=j)
        body = r.json()
        return body.get("auth") or body.get("data") or {}
