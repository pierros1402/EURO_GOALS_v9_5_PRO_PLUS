# ============================================================
# AI MatchLab / EURO_GOALS PRO+ — CONFIG
# ============================================================

import os
import logging

# ------------------------------------------------------------
# CORE APP META
# ------------------------------------------------------------
APP_NAME = "AI MatchLab"

# Μπορείς να το αλλάζεις και από env αν θέλεις
APP_VERSION = os.getenv(
    "AIMATCHLAB_VERSION",
    "AI MatchLab v1.0.0 — Unified RealData Hub"
)

APP_ENV = os.getenv("EUROGOALS_ENV", "production")

# ------------------------------------------------------------
# LIVE HUB SETTINGS
# ------------------------------------------------------------
LIVE_HUB_URL = os.getenv("EUROGOALS_LIVE_HUB_URL", "").strip()
LIVE_HUB_TIMEOUT = float(os.getenv("EUROGOALS_LIVE_HUB_TIMEOUT", "4.0"))

# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------
LOG_LEVEL = os.getenv("EUROGOALS_LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="[AI_MATCHLAB] %(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("ai_matchlab")
