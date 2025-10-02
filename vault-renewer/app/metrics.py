from prometheus_client import start_http_server, Gauge, Counter, CollectorRegistry

class Metrics:
    """
    Аккуратные метрики под один /metrics:
    - vault_service_up (Gauge 0/1)
    - vault_status{state="ok|renewed|non_renewable|error"} (GaugeVec)
    - vault_fallback_active (Gauge 0/1)
    - vault_token_ttl_seconds (Gauge)
    - vault_last_check_time_seconds, vault_last_success_time_seconds,
      vault_last_error_time_seconds, vault_last_renew_time_seconds (Gauges)
    - vault_renew_attempts_total / success_total / fail_total (Counters)
    - vault_fallback_switch_total (Counter)
    - vault_notifications_total{status="success|error"} (Counter)
    """
    STATES = ("ok", "renewed", "non_renewable", "error")

    def __init__(self, port: int):
        # СВОЙ реестр — никаких process_/python_ метрик
        self.registry = CollectorRegistry()

        # Служебные
        self.SERVICE_UP = Gauge("vault_service_up", "Service running (1=up, 0=down)", registry=self.registry)
        self.STATUS     = Gauge("vault_status", "High-level service status", ["state"], registry=self.registry)
        self.FALLBACK   = Gauge("vault_fallback_active", "Is fallback token active (1/0)", registry=self.registry)

        # Основное
        self.TTL        = Gauge("vault_token_ttl_seconds", "Current Vault token TTL (seconds)", registry=self.registry)

        # Временные отметки
        self.LAST_CHECK   = Gauge("vault_last_check_time_seconds", "Last check time (unix seconds)", registry=self.registry)
        self.LAST_SUCCESS = Gauge("vault_last_success_time_seconds", "Last success time (unix seconds)", registry=self.registry)
        self.LAST_ERROR   = Gauge("vault_last_error_time_seconds", "Last error time (unix seconds)", registry=self.registry)
        self.LAST_RENEW   = Gauge("vault_last_renew_time_seconds", "Last renew time (unix seconds)", registry=self.registry)

        # Счётчики
        self.RENEW_ATTEMPTS = Counter("vault_renew_attempts_total", "Renew attempts", registry=self.registry)
        self.RENEW_SUCCESS  = Counter("vault_renew_success_total",  "Renew successes", registry=self.registry)
        self.RENEW_FAIL     = Counter("vault_renew_fail_total",     "Renew failures", registry=self.registry)
        self.SWITCH_FB      = Counter("vault_fallback_switch_total","Fallback switches", registry=self.registry)
        self.NOTIFY         = Counter("vault_notifications_total",  "Notifications", ["status"], registry=self.registry)

        # Запуск /metrics только с этим реестром
        start_http_server(port, registry=self.registry)

        # Инициализация
        self.SERVICE_UP.set(1)
        self.FALLBACK.set(0)
        self._set_status("ok")  # до первого прогона считаем «окей»

    # Удобный сеттер статуса (ровно один state=1, остальные 0)
    def _set_status(self, state: str):
        for s in self.STATES:
            self.STATUS.labels(state=s).set(1 if s == state else 0)

    # Публичные шорткаты
    def status_ok(self):            self._set_status("ok")
    def status_renewed(self):       self._set_status("renewed")
    def status_non_renewable(self): self._set_status("non_renewable")
    def status_error(self):         self._set_status("error")

    def set_fallback(self, active: bool): self.FALLBACK.set(1 if active else 0)

    def shutdown(self):
        self.SERVICE_UP.set(0)
