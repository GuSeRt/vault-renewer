from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    vault_addr: str = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    token_file: str = os.getenv("VAULT_TOKEN_FILE", "/etc/vault/token")
    fallback_token_file: str | None = os.getenv("VAULT_FALLBACK_TOKEN_FILE")

    renew_before_sec: int = int(os.getenv("RENEW_BEFORE_SEC", str(7 * 24 * 3600)))
    renew_increment_sec: int = int(os.getenv("RENEW_INCREMENT_SEC", str(31 * 24 * 3600)))
    check_interval_sec: int = int(os.getenv("CHECK_INTERVAL_SEC", "300"))

    http_timeout: float = float(os.getenv("HTTP_TIMEOUT", "5.0"))
    retries: int = int(os.getenv("RETRIES", "3"))
    metrics_port: int = int(os.getenv("METRICS_PORT", "9754"))

    zulip_site: str | None = os.getenv("ZULIP_SITE")
    zulip_email: str | None = os.getenv("ZULIP_EMAIL")
    zulip_api_key: str | None = os.getenv("ZULIP_API_KEY")
    zulip_to: str | None = os.getenv("ZULIP_TO")       # "a@b" или "a@b,c@d"
    zulip_topic: str = os.getenv("ZULIP_TOPIC", "Vault token maintenance")

