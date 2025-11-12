# ============================================================
# GOAL MATRIX ENGINE v9.9.11 — No-Fail Auto-Retry Edition
# ============================================================

import time, random
from functools import wraps

class GoalMatrixEngine:
    def __init__(self):
        self.last_matrix = None
        print("[GoalMatrixEngine] ✅ Initialized (Auto-Retry Mode)")

    # === Retry wrapper ===
    def safe_exec(max_retries=3, delay=1.5):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        result = func(self, *args, **kwargs)
                        return result
                    except Exception as e:
                        print(f"[GoalMatrixEngine] ⚠️ Retry {attempt}/{max_retries}: {e}")
                        time.sleep(delay)
                print("[GoalMatrixEngine] 🧠 Returning cached matrix.")
                return self.last_matrix or {"status": "error", "message": "unavailable"}
            return wrapper
        return decorator

    @safe_exec(max_retries=3)
    def get_goal_matrix(self, match_id="default"):
        """Simulate computation of xG / heatmap matrix."""
        if random.random() < 0.2:
            raise Exception("Matrix compute failed.")
        matrix = {
            "match_id": match_id,
            "xG_home": round(random.uniform(0.8, 2.5), 2),
            "xG_away": round(random.uniform(0.6, 2.2), 2),
            "likely_goals": random.randint(1, 5),
            "alerts": [{"zone": "Left Wing", "pressure": "High"}] if random.random() < 0.3 else []
        }
        self.last_matrix = matrix
        return matrix

# === Singleton instance ===
engine = GoalMatrixEngine()

def get_goal_matrix(match_id="default"):
    return engine.get_goal_matrix(match_id)
