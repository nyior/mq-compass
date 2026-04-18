const http = require("http");
const fs = require("fs");
const path = require("path");

const host = "0.0.0.0";
const port = process.env.PORT || 3000;
const backendApiUrl = process.env.BACKEND_API_URL || "http://127.0.0.1:8103";
const root = __dirname;

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function proxyAsk(req, res) {
  const target = new URL("/ask", backendApiUrl);
  const proxyReq = http.request(
    {
      hostname: target.hostname,
      port: target.port,
      path: target.pathname,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    },
    (proxyRes) => {
      let body = "";
      proxyRes.on("data", (chunk) => {
        body += chunk;
      });
      proxyRes.on("end", () => {
        res.writeHead(proxyRes.statusCode || 500, {
          "Content-Type": "application/json; charset=utf-8",
        });
        res.end(body);
      });
    }
  );

  let body = "";
  req.on("data", (chunk) => {
    body += chunk;
  });
  req.on("end", () => {
    proxyReq.write(body);
    proxyReq.end();
  });

  proxyReq.on("error", () => {
    res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ detail: "Unable to reach retrieval service" }));
  });
}

http
  .createServer((req, res) => {
    if (req.method === "GET" && req.url === "/config.js") {
      const configJs = `window.__MQ_COMPASS_CONFIG__ = { apiBaseUrl: '/api' };`;
      res.writeHead(200, { "Content-Type": "application/javascript; charset=utf-8" });
      res.end(configJs);
      return;
    }

    if (req.method === "POST" && req.url === "/api/ask") {
      proxyAsk(req, res);
      return;
    }

    const requestPath = req.url === "/" ? "/index.html" : req.url;
    const filePath = path.join(root, requestPath);

    fs.readFile(filePath, (error, data) => {
      if (error) {
        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Not found");
        return;
      }

      const extension = path.extname(filePath);
      res.writeHead(200, {
        "Content-Type": mimeTypes[extension] || "application/octet-stream",
      });
      res.end(data);
    });
  })
  .listen(port, host, () => {
    console.log(`chat_widget demo running at http://${host}:${port}`);
  });
