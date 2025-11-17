// =======================================================================
// AI MATCHLAB — SOURCE B (SOFASCORE RESULTS WIDGET)
// =======================================================================

const HTML_HEADERS = {
  "content-type": "text/html; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
};

const RESULTS_WIDGET_URL = "https://www.sofascore.com/embed/results";

export default {
  async fetch() {
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8" />
        <title>AI MATCHLAB — RESULTS</title>
        <style>
          body { margin:0; padding:0; background:#000; overflow:hidden; }
          iframe { width:100%; height:100vh; border:none; }
        </style>
      </head>
      <body>
        <iframe src="${RESULTS_WIDGET_URL}" allowfullscreen></iframe>
      </body>
      </html>
    `;
    return new Response(html, { headers: HTML_HEADERS });
  },
};
