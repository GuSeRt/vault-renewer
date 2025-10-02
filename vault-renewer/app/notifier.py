import requests
from .jsonlog import jlog

class ZulipNotifier:
    def __init__(self, site: str | None, email: str | None, api_key: str | None,
                 to: str | None, topic: str):
        self.site, self.email, self.api_key, self.topic = site, email, api_key, topic
        self.to = [x.strip() for x in (to or "").split(",") if x.strip()]
        self.enabled = bool(site and email and api_key and self.to)

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        try:
            r = requests.post(
                f"{self.site}/api/v1/messages",
                data={"type": "private", "to": self.to, "content": text, "topic": self.topic},
                auth=(self.email, self.api_key),
                timeout=5.0,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            jlog("error", "zulip_failed", error=str(e))
            return False
