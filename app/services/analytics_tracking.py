"""Product analytics via PostHog. Logs events in dev mode when no key is set."""
from __future__ import annotations
import logging
from app.config import get_settings

logger = logging.getLogger("tradeloop.tracking")

class ProductAnalytics:
    def __init__(self):
        settings = get_settings()
        self._key = settings.posthog_api_key
        self._client = None
        if self._key:
            try:
                import posthog
                posthog.project_api_key = self._key
                posthog.host = "https://app.posthog.com"
                self._client = posthog
                logger.info("PostHog initialized")
            except ImportError:
                logger.warning("posthog not installed")

    def capture(self, user_id: str, event: str, properties: dict = None):
        if self._client:
            self._client.capture(user_id, event, properties or {})
        else:
            logger.debug("Track: user=%s event=%s props=%s", user_id, event, properties)

product_analytics = ProductAnalytics()
