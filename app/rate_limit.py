from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()
_enabled = settings.environment != "testing"

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
