// =======================================================================
// AI MATCHLAB — MAIN ROUTER (SOFASCORE EDITION)
// =======================================================================

const HTML = (url) => `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AI MATCHLAB</title>
  <style>
    body { margin:0; padding:0; background:#000; overflow:hidden; }
    iframe { width:100%; height:100vh; border:none; }
  </style>
</head>
<body>
  <iframe src="${url}" allowfullscreen></iframe>
</body>
</html>
`;

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // LIVE
    if (path === "/live") {
      return new Response(
        HTML("https://aimatchlab-source-a.pierros1402.workers.dev"),
        { headers: { "content-type": "text/html" } }
      );
    }

    // RESULTS
    if (path === "/recent") {
      return new Response(
        HTML("https://aimatchlab-source-b.pierros1402.workers.dev"),
        { headers: { "content-type": "text/html" } }
      );
    }

    // FIXTURES
    if (path === "/upcoming") {
      return new Response(
        HTML("https://aimatchlab-source-c.pierros1402.workers.dev"),
        { headers: { "content-type": "text/html" } }
      );
    }

    // MATCH PAGE (SofaScore Match Widget)
    if (path.startsWith("/match/")) {
      const id = path.split("/").pop();
      const widgetURL = `https://www.sofascore.com/embed/event/${id}`;
      return new Response(HTML(widgetURL), {
        headers: { "content-type": "text/html" },
      });
    }

    // DEFAULT → go to live
    if (path === "/" || path === "") {
      return Response.redirect(url.origin + "/live");
    }

    return new Response("Not Found", { status: 404 });
  },
};
