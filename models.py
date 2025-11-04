# ================================================================
# EURO_GOALS – Database Models (v9.4.4 PRO+)
# ================================================================

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

# ------------------------------------------------
# SMART MONEY ALERTS
# ------------------------------------------------
class SmartMoneyAlert(Base):
    __tablename__ = "smartmoney_alerts"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, index=True)
    league = Column(String)
    team = Column(String)
    event_time = Column(DateTime(timezone=True), default=func.now())
    minute = Column(Integer)
    delta_odds = Column(Float)
    intensity = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ------------------------------------------------
# PUSH SUBSCRIPTIONS
# ------------------------------------------------
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, unique=True, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ------------------------------------------------
# FUTURE MODELS (αν θέλεις αργότερα)
# ------------------------------------------------
# class Match(Base):
#     __tablename__ = "matches"
#     id = Column(Integer, primary_key=True, index=True)
#     home_team = Column(String)
#     away_team = Column(String)
#     league = Column(String)
#     start_time = Column(DateTime)
#     odds_home = Column(Float)
#     odds_draw = Column(Float)
#     odds_away = Column(Float)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
