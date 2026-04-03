from app.services.event_bus import EventBus, event_bus
from app.services.trade_service import TradeService
from app.services.analytics_service import AnalyticsService
from app.services.compliance_service import ComplianceService
from app.services.broker_service import BrokerService

# Singletons — import these instead of creating new instances
trade_svc = TradeService()
analytics_svc = AnalyticsService()
compliance_svc = ComplianceService()
broker_svc = BrokerService()

__all__ = [
    "EventBus", "event_bus",
    "TradeService", "AnalyticsService", "ComplianceService", "BrokerService",
    "trade_svc", "analytics_svc", "compliance_svc", "broker_svc",
]
