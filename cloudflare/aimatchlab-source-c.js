// =======================================================================
// AI MATCHLAB — SOURCE A (SOFASCORE LIVE WIDGET)
// =======================================================================

const HTML_HEADERS = {
  "content-type": "text/html; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
};

const LIVE_WIDGET_URL = "https://www.sofascore.com/embed/livescore";

export default {
  async fetch() {
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8" />
        <title>AI MATCHLAB — LIVE</title>
        <style>
          body { margin:0; padding:0; background:#000; overflow:hidden; }
          iframe { width:100%; height:100vh; border:none; }
        </style>
      </head>
      <body>
        <iframe src="${LIVE_WIDGET_URL}" allowfullscreen></iframe>
      </body>
      </html>
    `;

    return new Response(html, { headers: HTML_HEADERS });
  },
};
