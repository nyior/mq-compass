const http = require("http");
const fs = require("fs");
const path = require("path");

const host = "127.0.0.1";
const port = process.env.PORT || 8301;
const root = __dirname;

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

http
  .createServer((req, res) => {
    const requestPath = req.url === "/" ? "/public/index.html" : req.url;
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
    console.log(`MQ Compass widget preview running at http://${host}:${port}`);
  });
