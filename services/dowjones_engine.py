# ============================================================
# Dow Jones (Odds Momentum) Engine — Betfair-centric
# ============================================================
import os, time, random, math
from collections import defaultdict, deque
from typing import Dict, Any, List
import httpx

class DowJonesEngine:
    def __init__(self, refresh_seconds: int = 10):
        self.refresh_seconds = refresh_seconds
        self.client: httpx.AsyncClient | None = None
        self.cfg = self._load_cfg()
        self.state = {"last_refresh": 0, "tick": 0, "mock_mode": False}
        self.history: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=30)))

    def _load_cfg(self) -> Dict[str, Any]:
        return {
            "workers": {
                "betfair": os.getenv("WORKER_BETFAIR_URL"),
                "bet365": os.getenv("WORKER_BET365_URL"),
                "stoiximan": os.getenv("WORKER_STOIXIMAN_URL"),
                "opap": os.getenv("WORKER_OPAP_URL"),
            },
            "auth_scheme": os.getenv("WORKER_AUTH_SCHEME", "").strip(),
            "auth_token": os.getenv("WORKER_AUTH_TOKEN", "").strip(),
            "countries": [x.strip() for x in os.getenv("DJ_COUNTRIES", "").split(",") if x.strip()],
            "leagues": [x.strip() for x in os.getenv("DJ_LEAGUES", "").split(",") if x.strip()],
        }

    def _headers(self) -> Dict[str, str]:
        h = {"User-Agent": "EURO_GOALS/9.8.8"}
        if self.cfg.get("auth_scheme") and self.cfg.get("auth_token"):
            h["Authorization"] = f"{self.cfg['auth_scheme']} {self.cfg['auth_token']}"
        return h

    async def start(self):
        self.client = httpx.AsyncClient(timeout=10)
        if not any(self.cfg["workers"].values()):
            self.state["mock_mode"] = True

    async def stop(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def refresh(self):
        self.state["tick"] += 1
        self.state["last_refresh"] = int(time.time())
        if self.state.get("mock_mode"):
            self._ingest_mock()
            return
        await self._ingest_from_workers()

    async def _ingest_from_workers(self):
        tasks = []
        for name, url in self.cfg["workers"].items():
            if url:
                tasks.append(self._fetch_worker(name, url))
        if not tasks:
            self._ingest_mock()
            return
        results = await _gather_safe(tasks)
        for name, data in results:
            if data:
                self._merge_feed(name, data)

    async def _fetch_worker(self, name: str, url: str):
        try:
            assert self.client is not None
            resp = await self.client.get(url, headers=self._headers())
            if resp.status_code != 200:
                return (name, None)
            return (name, resp.json())
        except Exception:
            return (name, None)

    def _merge_feed(self, source: str, data: Dict[str, Any]):
        fixtures = data.get("fixtures", [])
        for fx in fixtures:
            fid = str(fx.get("id"))
            league = (fx.get("league") or "").strip()
            country = (fx.get("country") or "").strip()
            if self.cfg["countries"] and country and country not in self.cfg["countries"]:
                continue
            if self.cfg["leagues"] and league and league not in self.cfg["leagues"]:
                continue
            markets = fx.get("markets", {})
            for mk, prices in markets.items():
                if not prices:
                    continue
                vals = [v for v in prices.values() if isinstance(v, (int, float)) and v > 0]
                if not vals:
                    continue
                mid = sum(vals) / len(vals)
                self.history[fid][mk].append({"t": self.state["last_refresh"], "source": source, "mid": mid})

    def _ingest_mock(self):
        n = random.randint(3, 6)
        for i in range(n):
            fid = f"MOCK-{i}"
            t = int(time.time())
            for mk, base in ("1x2", 2.0), ("O/U2.5", 1.9):
                self.history[fid][mk].append({"t": t, "source": "mock", "mid": base + (random.random()-0.5)*0.2})
                for k in range(1, 5):
                    self.history[fid][mk].append({"t": t - k*10, "source": "mock", "mid": base + (random.random()-0.5)*0.2})

    def _compute_momentum(self, series: deque) -> float:
        if len(series) < 3:
            return 0.0
        xs = [p["t"] for p in series]
        ys = [p["mid"] for p in series]
        n = len(xs)
        mean_x = sum(xs)/n
        mean_y = sum(ys)/n
        num = sum((xs[i]-mean_x)*(ys[i]-mean_y) for i in range(n))
        den = sum((xs[i]-mean_x)**2 for i in range(n)) or 1.0
        slope = num/den
        var = sum((y-mean_y)**2 for y in ys)/max(1, n-1)
        vol = (var ** 0.5)
        return slope * (1.0 + vol)

    def _fixture_score(self, fid: str):
        mk_scores = {mk: self._compute_momentum(dq) for mk, dq in self.history.get(fid, {}).items()}
        agg = (sum(s*s for s in mk_scores.values()) ** 0.5) if mk_scores else 0.0
        dom = max(mk_scores, key=lambda k: abs(mk_scores[k])) if mk_scores else None
        return {"aggregate": agg, "by_market": mk_scores, "dominant": dom}

    def snapshot(self) -> Dict[str, Any]:
        rows = []
        for fid in list(self.history.keys()):
            sc = self._fixture_score(fid)
            rows.append({"fixture_id": fid, "score": sc["aggregate"], "dominant": sc["dominant"], "markets": sc["by_market"]})
        rows.sort(key=lambda r: abs(r["score"]), reverse=True)
        return {"ts": self.state["last_refresh"], "tick": self.state["tick"], "mock": self.state.get("mock_mode", False), "rows": rows[:100]}

    def public_config(self) -> Dict[str, Any]:
        return {"refresh_seconds": self.refresh_seconds, "workers": {k: bool(v) for k, v in self.cfg["workers"].items()}, "countries": self.cfg["countries"], "leagues": self.cfg["leagues"]}

    def health(self) -> Dict[str, Any]:
        return {"mock": self.state.get("mock_mode", False), "last_refresh": self.state["last_refresh"], "tick": self.state["tick"], "workers_up": {k: bool(v) for k, v in self.cfg["workers"].items()}}

async def _gather_safe(tasks: List[Any]):
    results = []
    for coro in tasks:
        try:
            r = await coro
            results.append(r)
        except Exception:
            results.append(("unknown", None))
    return results
________________________________________
