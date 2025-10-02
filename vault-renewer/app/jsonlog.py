import logging, json
from datetime import datetime, timezone

logger = logging.getLogger("vault")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(_handler)

def jlog(level: str, msg: str, **fields):
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "msg": msg, **fields}
    getattr(logger, level)(json.dumps(rec, ensure_ascii=False))
