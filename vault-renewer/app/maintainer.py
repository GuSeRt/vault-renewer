import os, time, signal
from .config import Config
from .jsonlog import jlog
from .metrics import Metrics
from .vault import VaultClient
from .notifier import ZulipNotifier

def _read_token(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None

def _write_token(path: str, token: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token.strip() + "\n")

class Maintainer:
    def __init__(self, cfg: Config, m: Metrics):
        self.cfg, self.m = cfg, m
        self.vault = VaultClient(cfg.vault_addr, cfg.http_timeout, cfg.retries)
        self.notifier = ZulipNotifier(cfg.zulip_site, cfg.zulip_email,
                                      cfg.zulip_api_key, cfg.zulip_to, cfg.zulip_topic)

    def _notify(self, text: str):
        ok = self.notifier.send(text)
        if ok: self.m.NOTIFY.labels("success").inc()
        else:  self.m.NOTIFY.labels("error").inc()

    def _ensure_valid_token(self) -> tuple[str, dict]:
        t = _read_token(self.cfg.token_file)
        if not t:
            raise RuntimeError(f"empty token file: {self.cfg.token_file}")
        try:
            data = self.vault.lookup_self(t)
            self.m.set_fallback(False)
            return t, data
        except Exception as e:
            jlog("error", "primary_lookup_failed", error=str(e))
            if not self.cfg.fallback_token_file:
                raise
            fb = _read_token(self.cfg.fallback_token_file)
            if not fb:
                raise RuntimeError("fallback token file empty")
            data = self.vault.lookup_self(fb)  # поднимет исключение, если тоже плохой
            _write_token(self.cfg.token_file, fb)
            self.m.SWITCH_FB.inc()
            self.m.set_fallback(True)
            self._notify("Переключился на резервный Vault-токен.")
            return fb, data

    def check_and_renew(self):
        now = time.time()
        self.m.LAST_CHECK.set(now)
    
        # lookup + возможное переключение на fallback
        try:
            token, info = self._ensure_valid_token()
        except Exception as e:
            self.m.LAST_ERROR.set(time.time())
            self.m.status_error()
            self._notify(f"Критическая ошибка обслуживания токена: {e}")
            jlog("error", "lookup_failed", error=str(e))
            return
    
        ttl = int(info.get("ttl", 0))
        self.m.TTL.set(ttl)
        
        if not info.get("renewable", False):
            self.m.LAST_ERROR.set(time.time())
            self.m.status_non_renewable()
            self._notify("Токен не возобновляем. Требуется вмешательство.")
            return
    
        # Рано продлевать — всё ок
        if ttl > self.cfg.renew_before_sec:
            self.m.LAST_SUCCESS.set(time.time())
            self.m.status_ok()
            return
    
            # Пора продлевать
        self.m.RENEW_ATTEMPTS.inc()
        try:
            self.vault.renew_self(token, self.cfg.renew_increment_sec)
            ttl2 = int(self.vault.lookup_self(token).get("ttl", ttl))
            self.m.TTL.set(ttl2)
            self.m.RENEW_SUCCESS.inc()
            t = time.time()
            self.m.LAST_SUCCESS.set(t)
            self.m.LAST_RENEW.set(t)
            self.m.status_renewed()
            self._notify(f"Продлил Vault-токен. Новый TTL ≈ {ttl2} с.")
            jlog("info", "renew_ok", new_ttl=ttl2)
        except Exception as e:
            self.m.RENEW_FAIL.inc()
            self.m.LAST_ERROR.set(time.time())
            self.m.status_error()
            self._notify(f"Ошибка продления токена: {e}")
            jlog("error", "renew_failed", error=str(e))


    def run_loop(self):
        running = True
        def stop(_s, _f): 
            nonlocal running
            running = False
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        jlog("info", "loop_started", interval=self.cfg.check_interval_sec)
        while running:
            start = time.time()
            try:
                self.check_and_renew()
            except Exception as e:
                self.m.LAST_ERR.set(time.time())
                self._notify(f"Критическая ошибка обслуживания токена: {e}")
                jlog("error", "loop_unhandled", error=str(e))
            time.sleep(max(1, self.cfg.check_interval_sec - (time.time() - start)))
        self.m.shutdown()
        jlog("info", "shutdown")
