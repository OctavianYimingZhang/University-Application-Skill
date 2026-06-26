#!/usr/bin/env node

import { createServer } from "node:http";
import { spawn } from "node:child_process";

const defaultAllowedOrigins = new Set([
  "https://octavianyimingzhang.github.io",
  "http://127.0.0.1:5173",
  "http://127.0.0.1:5174",
  "http://localhost:5173",
  "http://localhost:5174",
]);

function parseArgs(argv) {
  const options = {
    port: 8787,
    host: "127.0.0.1",
    codexBin: "codex",
    allowedOrigins: new Set(defaultAllowedOrigins),
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    if (arg === "--port" && next) {
      options.port = Number(next);
      index += 1;
    } else if (arg === "--host" && next) {
      options.host = next;
      index += 1;
    } else if (arg === "--codex-bin" && next) {
      options.codexBin = next;
      index += 1;
    } else if (arg === "--allow-origin" && next) {
      options.allowedOrigins.add(next);
      index += 1;
    } else if (arg === "--help" || arg === "-h") {
      console.log(`Usage: node scripts/codex_oauth_bridge.mjs [--port 8787] [--host 127.0.0.1] [--codex-bin codex] [--allow-origin ORIGIN]\n\nEndpoints:\n  GET  /health\n  GET  /codex/status\n  POST /codex/start-oauth  { \"flow\": \"browser\" | \"device\" }\n  POST /codex/refresh\n  POST /codex/logout`);
      process.exit(0);
    }
  }

  if (!Number.isInteger(options.port) || options.port < 1 || options.port > 65535) {
    throw new Error("--port must be an integer from 1 to 65535.");
  }

  return options;
}

class CodexStdioClient {
  constructor(codexBin) {
    this.codexBin = codexBin;
    this.child = null;
    this.buffer = "";
    this.nextId = 1;
    this.pending = new Map();
    this.initPromise = null;
  }

  async request(method, params = undefined) {
    await this.ensureStarted();
    return this.sendRequest(method, params);
  }

  async ensureStarted() {
    if (this.initPromise) {
      return this.initPromise;
    }

    this.child = spawn(this.codexBin, ["app-server", "--stdio"], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.child.stdout.setEncoding("utf8");
    this.child.stderr.setEncoding("utf8");
    this.child.stdout.on("data", (chunk) => this.handleStdout(chunk));
    this.child.stderr.on("data", (chunk) => process.stderr.write(chunk));
    this.child.on("close", () => this.handleClose());
    this.child.on("error", (error) => this.handleClose(error));

    this.initPromise = this.sendRequest("initialize", {
      clientInfo: {
        name: "university_application_skill_oauth_bridge",
        title: "University Application Skill OAuth Bridge",
        version: "0.1.0",
      },
    }).then((result) => {
      this.sendNotification("initialized");
      return result;
    }).catch((error) => {
      this.stop();
      throw error;
    });

    return this.initPromise;
  }

  sendRequest(method, params = undefined) {
    if (!this.child?.stdin.writable) {
      return Promise.reject(new Error("Codex app-server stdio is not writable."));
    }

    const id = this.nextId;
    this.nextId += 1;
    const request = params === undefined ? { id, method } : { id, method, params };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Codex app-server timed out on ${method}.`));
      }, 30000);

      this.pending.set(id, { resolve, reject, timeout });
      this.child.stdin.write(`${JSON.stringify(request)}\n`);
    });
  }

  sendNotification(method, params = {}) {
    if (this.child?.stdin.writable) {
      this.child.stdin.write(`${JSON.stringify({ method, params })}\n`);
    }
  }

  handleStdout(chunk) {
    this.buffer += chunk;
    const lines = this.buffer.split("\n");
    this.buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }

      let message;
      try {
        message = JSON.parse(line);
      } catch {
        continue;
      }

      if (typeof message.id !== "number") {
        continue;
      }

      const pending = this.pending.get(message.id);
      if (!pending) {
        continue;
      }

      clearTimeout(pending.timeout);
      this.pending.delete(message.id);

      if (message.error) {
        pending.reject(new Error(message.error.message ?? "Codex app-server returned an error."));
      } else {
        pending.resolve(message.result);
      }
    }
  }

  handleClose(error) {
    const reason = error instanceof Error ? error : new Error("Codex app-server closed.");
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(reason);
    }
    this.pending.clear();
    this.child = null;
    this.initPromise = null;
  }

  stop() {
    if (this.child) {
      this.child.kill("SIGTERM");
    }
    this.handleClose(new Error("Codex bridge stopped."));
  }
}

function normalizeAccount(result) {
  return {
    ...result,
    connected: Boolean(result?.account),
  };
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 8192) {
        reject(new Error("Request body is too large."));
        request.destroy();
      }
    });
    request.on("end", () => {
      if (!body.trim()) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch {
        reject(new Error("Request body must be JSON."));
      }
    });
    request.on("error", reject);
  });
}

function buildCors(origin, allowedOrigins) {
  if (!origin) {
    return { allowed: true, origin: "*" };
  }

  return { allowed: allowedOrigins.has(origin), origin };
}

function sendJson(response, statusCode, data, corsOrigin) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "access-control-allow-origin": corsOrigin,
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-allow-private-network": "true",
    "vary": "Origin, Access-Control-Request-Private-Network",
  });
  response.end(JSON.stringify(data));
}

function createBridgeServer(options, codex) {
  return createServer(async (request, response) => {
    const cors = buildCors(request.headers.origin, options.allowedOrigins);
    if (!cors.allowed) {
      sendJson(response, 403, { error: "Origin is not allowed by this Codex OAuth bridge." }, cors.origin);
      return;
    }

    if (request.method === "OPTIONS") {
      sendJson(response, 204, {}, cors.origin);
      return;
    }

    try {
      if (request.method === "GET" && request.url === "/health") {
        sendJson(response, 200, { ok: true }, cors.origin);
        return;
      }

      if (request.method === "GET" && request.url === "/codex/status") {
        const result = await codex.request("account/read", { refreshToken: false });
        sendJson(response, 200, normalizeAccount(result), cors.origin);
        return;
      }

      if (request.method === "POST" && request.url === "/codex/refresh") {
        const result = await codex.request("account/read", { refreshToken: true });
        sendJson(response, 200, normalizeAccount(result), cors.origin);
        return;
      }

      if (request.method === "POST" && request.url === "/codex/start-oauth") {
        const body = await readBody(request);
        const flow = body.flow === "device" ? "chatgptDeviceCode" : "chatgpt";
        const result = await codex.request("account/login/start", { type: flow });
        sendJson(response, 200, result, cors.origin);
        return;
      }

      if (request.method === "POST" && request.url === "/codex/logout") {
        const result = await codex.request("account/logout");
        sendJson(response, 200, { ok: true, result }, cors.origin);
        return;
      }

      sendJson(response, 404, { error: "Unknown Codex OAuth bridge endpoint." }, cors.origin);
    } catch (error) {
      sendJson(response, 500, { error: error instanceof Error ? error.message : "Codex OAuth bridge failed." }, cors.origin);
    }
  });
}

const options = parseArgs(process.argv.slice(2));
const codex = new CodexStdioClient(options.codexBin);
const server = createBridgeServer(options, codex);

server.listen(options.port, options.host, () => {
  console.log(`Codex OAuth bridge listening on http://${options.host}:${options.port}`);
  console.log(`Allowed origins: ${Array.from(options.allowedOrigins).join(", ")}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    server.close();
    codex.stop();
    process.exit(0);
  });
}
