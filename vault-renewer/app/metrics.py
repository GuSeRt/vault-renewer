from prometheus_client import start_http_server, Gauge, Counter

class Metrics:
    def __init__(self, port: int):
        # gauges
        self.UP = Gauge("vault_up", "Script running (1=up, 0=down)")
        self.USING_FALLBACK = Gauge("vault_using_fallback", "1 if fallback token active")
        self.LAST_CHECK = Gauge("vault_last_check_timestamp_seconds", "Last check time")
        self.LAST_OK = Gauge("vault_last_success_timestamp_seconds", "Last success time")
        self.LAST_ERR = Gauge("vault_last_error_timestamp_seconds", "Last error time")
        self.TTL = Gauge("vault_token_ttl_seconds", "Current Vault token TTL")

        # counters
        self.RENEW_ATTEMPTS = Counter("vault_renew_attempts_total", "Renew attempts")
        self.RENEW_SUCCESS  = Counter("vault_renew_success_total", "Renew successes")
        self.RENEW_FAIL     = Counter("vault_renew_fail_total", "Renew failures")
        self.SWITCH_FB      = Counter("vault_fallback_switch_total", "Fallback switches")
        self.NOTIFY         = Counter("vault_notifications_total", "Notifications", ["status"])

        start_http_server(port)   # единственный эндпоинт /metrics
        self.UP.set(1)
        self.USING_FALLBACK.set(0)

    def shutdown(self):
        self.UP.set(0)
