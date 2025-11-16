// =======================================================================
// AI MATCHLAB — MAIN UNIFIED WORKER (A2 FINAL v3 — /api/* version)
// Fully JSON-safe, supports workers.dev (no routing needed)
// =======================================================================

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

// ------------------------------------------------------------
// CORS
// ------------------------------------------------------------
function withCorsHeaders(headers = {}, request) {
  const origin = request.headers.get("Origin") || "*";
  return {
    ...headers,
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers":
      "Content-Type, Authorization, X-Requested-With",
    "Access-Control-Max-Age": "86400",
  };
}

function jsonResponse(data, status = 200, request) {
  return new Response(JSON.stringify(data), {
    status,
    headers: withCorsHeaders(JSON_HEADERS, request),
  });
}

function handleOptions(request) {
  return new Response(null, {
    status: 204,
    headers: withCorsHeaders({}, request),
  });
}

// ------------------------------------------------------------
// UNIVERSAL JSON-SAFE PROXY
// ------------------------------------------------------------
async function proxyExternal(url, request, extraHeaders = {}) {
  const init = {
    method: request.method === "POST" ? "POST" : "GET",
    headers: {
      "accept-encoding": "identity",
      ...extraHeaders,
    },
  };

  if (request.method === "POST") {
    init.body = await request.clone().arrayBuffer();
  }

  let res;
  try {
    res = await fetch(url, init);
  } catch (err) {
    return jsonResponse(
      { ok: false, error: "fetch_failed", details: String(err), url },
      500,
      request
    );
  }

  const raw = await res.text();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_) {
    return jsonResponse(
      { ok: false, error: "invalid_json_from_source", raw, url },
      res.status,
      request
    );
  }

  return new Response(JSON.stringify(parsed), {
    status: res.status,
    headers: withCorsHeaders(JSON_HEADERS, request),
  });
}

// ------------------------------------------------------------
// Source A — LIVE
// ------------------------------------------------------------
async function handleLive(url, request, env) {
  const base =
    env.SOFASCORE_LIVE_BASE_URL ||
    env.SOFASCORE_BYPASS_URL ||
    "";

  if (!base) {
    return jsonResponse(
      {
        ok: false,
        error: "Missing SOFASCORE_LIVE_BASE_URL / SOFASCORE_BYPASS_URL",
      },
      500,
      request
    );
  }

  const qs = url.search || "";
  return proxyExternal(`${base}${qs}`, request);
}

// ------------------------------------------------------------
// Source A — MATCH DETAILS
// ------------------------------------------------------------
async function handleMatch(url, request, env) {
  const base =
    env.SOFASCORE_MATCH_BASE_URL ||
    env.SOFASCORE_BYPASS_URL ||
    "";

  if (!base) {
    return jsonResponse(
      {
        ok: false,
        error: "Missing SOFASCORE_MATCH_BASE_URL / SOFASCORE_BYPASS_URL",
      },
      500,
      request
    );
  }

  const qs = url.search || "";
  return proxyExternal(`${base}${qs}`, request);
}

// ------------------------------------------------------------
// Generic provider proxy
// /api/proxy/:provider/:rest...
// ------------------------------------------------------------
function resolveProviderBase(provider, env) {
  switch (provider) {
    case "sofascore":
      return env.SOFASCORE_PROXY_BASE || env.SOFASCORE_BYPASS_URL || "";
    case "betfair":
      return env.BETFAIR_PUBLIC_BASE || env.BETFAIR_PROXY_URL || "";
    case "bet365":
      return env.BET365_PROXY_BASE || "";
    case "stoiximan":
      return env.STOIXIMAN_PROXY_BASE || "";
    default:
      return "";
  }
}

async function handleGenericProxy(url, request, env, provider, restPath) {
  const base = resolveProviderBase(provider, env);

  if (!base) {
    return jsonResponse(
      { ok: false, error: `Missing base URL for provider '${provider}'` },
      500,
      request
    );
  }

  const qs = url.search || "";
  const cleanBase = base.endsWith("/") ? base.slice(0, -1) : base;
  const cleanRest = restPath.startsWith("/")
    ? restPath.slice(1)
    : restPath;

  const target = `${cleanBase}/${cleanRest}${qs}`;
  return proxyExternal(target, request);
}

// ------------------------------------------------------------
// STATUS
// ------------------------------------------------------------
function handleStatus(request) {
  return jsonResponse(
    {
      ok: true,
      service: "AI MATCHLAB MAIN WORKER",
      version: "A2-FINAL-v3",
      timestamp: new Date().toISOString(),
    },
    200,
    request
  );
}

// ------------------------------------------------------------
// MAIN ROUTER
// ------------------------------------------------------------
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return handleOptions(request);
    }

    // /api/status
    if (path === "/api/status") return handleStatus(request);

    // /api/live
    if (path === "/api/live") return handleLive(url, request, env);

    // /api/match
    if (path === "/api/match") return handleMatch(url, request, env);

    // /api/proxy/:provider/:rest
    if (path.startsWith("/api/proxy/")) {
      const parts = path.split("/").filter(Boolean);
      const provider = parts[2];
      const rest = "/" + parts.slice(3).join("/");
      return handleGenericProxy(url, request, env, provider, rest);
    }

    return jsonResponse(
      { ok: false, error: "not_found", path },
      404,
      request
    );
  },
};
