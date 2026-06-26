type JsonObject = Record<string, unknown>;

export type CodexEndpointKind = "app-server-ws" | "bridge-http";
export type CodexLoginFlow = "browser" | "device";

export interface CodexEndpointValidation {
  endpoint: string;
  kind?: CodexEndpointKind;
  valid: boolean;
  message: string;
}

export interface CodexAccountInfo {
  type: string;
  email?: string;
  planType?: string | null;
  credentialSource?: string;
}

export interface CodexAccountReadResult {
  account: CodexAccountInfo | null;
  requiresOpenaiAuth: boolean;
  connected: boolean;
}

export type CodexLoginResult =
  | {
      type: "chatgpt";
      loginId: string;
      authUrl: string;
    }
  | {
      type: "chatgptDeviceCode";
      loginId: string;
      verificationUrl: string;
      userCode: string;
    }
  | {
      type: "bridge";
      loginId?: string;
      authUrl?: string;
      verificationUrl?: string;
      userCode?: string;
      message?: string;
    };

const endpointStorageKey = "soleil.codex.oauth.endpoint";

function isRecord(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isLoopbackHost(hostname: string) {
  const host = hostname.toLowerCase();
  return host === "localhost" || host === "127.0.0.1" || host === "::1" || host.startsWith("127.");
}

function trimTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function getInitialCodexEndpoint() {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8787";
  }

  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("codex_ws") ?? params.get("codex_bridge");
  if (fromQuery) {
    return fromQuery;
  }

  return window.localStorage.getItem(endpointStorageKey) ?? "http://127.0.0.1:8787";
}

export function rememberCodexEndpoint(endpoint: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(endpointStorageKey, endpoint.trim());
  }
}

export function validateCodexEndpoint(input: string): CodexEndpointValidation {
  const endpoint = input.trim();
  if (!endpoint) {
    return { endpoint, valid: false, message: "No Codex endpoint configured." };
  }

  let url: URL;
  try {
    url = new URL(endpoint);
  } catch {
    return { endpoint, valid: false, message: "Endpoint must be a valid URL." };
  }

  if (url.username || url.password) {
    return { endpoint, valid: false, message: "Do not embed credentials in the endpoint URL." };
  }

  if (url.protocol === "ws:" || url.protocol === "wss:") {
    if (url.protocol === "ws:" && !isLoopbackHost(url.hostname)) {
      return { endpoint, valid: false, message: "Plain WebSocket is allowed only for localhost or 127.0.0.1." };
    }

    return {
      endpoint: trimTrailingSlash(endpoint),
      kind: "app-server-ws",
      valid: true,
      message: "Codex app-server WebSocket endpoint. Browser pages may need the HTTP bridge if Origin is rejected.",
    };
  }

  if (url.protocol === "http:" || url.protocol === "https:") {
    if (url.protocol === "http:" && !isLoopbackHost(url.hostname)) {
      return { endpoint, valid: false, message: "Plain HTTP bridges are allowed only for localhost or 127.0.0.1." };
    }

    return {
      endpoint: trimTrailingSlash(endpoint),
      kind: "bridge-http",
      valid: true,
      message: "Trusted HTTP bridge endpoint.",
    };
  }

  return { endpoint, valid: false, message: "Use ws://, wss://, http://, or https://." };
}

class CodexRpcClient {
  private nextId = 1;
  private pending = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void; timeout: number }>();

  private constructor(private readonly socket: WebSocket) {
    this.socket.addEventListener("message", (event) => this.handleMessage(event));
    this.socket.addEventListener("close", () => this.rejectPending(new Error("Codex app-server connection closed.")));
    this.socket.addEventListener("error", () => this.rejectPending(new Error("Codex app-server connection failed.")));
  }

  static open(endpoint: string) {
    return new Promise<CodexRpcClient>((resolve, reject) => {
      const socket = new WebSocket(endpoint);
      const timeout = window.setTimeout(() => {
        socket.close();
        reject(new Error("Timed out connecting to Codex app-server."));
      }, 8000);

      socket.addEventListener("open", () => {
        window.clearTimeout(timeout);
        resolve(new CodexRpcClient(socket));
      }, { once: true });

      socket.addEventListener("error", () => {
        window.clearTimeout(timeout);
        reject(new Error("Could not open Codex app-server WebSocket."));
      }, { once: true });
    });
  }

  request<T>(method: string, params?: unknown) {
    const id = this.nextId;
    this.nextId += 1;

    return new Promise<T>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Codex app-server timed out on ${method}.`));
      }, 15000);

      this.pending.set(id, {
        resolve: (value) => resolve(value as T),
        reject,
        timeout,
      });

      this.socket.send(JSON.stringify(params === undefined ? { method, id } : { method, id, params }));
    });
  }

  notify(method: string, params: unknown = {}) {
    this.socket.send(JSON.stringify({ method, params }));
  }

  close() {
    this.socket.close();
  }

  private handleMessage(event: MessageEvent<string>) {
    let message: JsonObject;
    try {
      const parsed = JSON.parse(event.data);
      if (!isRecord(parsed)) {
        return;
      }
      message = parsed;
    } catch {
      return;
    }

    if (typeof message.id !== "number") {
      return;
    }

    const pending = this.pending.get(message.id);
    if (!pending) {
      return;
    }

    window.clearTimeout(pending.timeout);
    this.pending.delete(message.id);

    if (isRecord(message.error)) {
      const errorMessage = typeof message.error.message === "string" ? message.error.message : "Codex app-server returned an error.";
      pending.reject(new Error(errorMessage));
      return;
    }

    pending.resolve(message.result);
  }

  private rejectPending(error: Error) {
    this.pending.forEach((pending) => {
      window.clearTimeout(pending.timeout);
      pending.reject(error);
    });
    this.pending.clear();
  }
}

async function withCodexClient<T>(endpoint: string, task: (client: CodexRpcClient) => Promise<T>) {
  const client = await CodexRpcClient.open(endpoint);
  try {
    await client.request("initialize", {
      clientInfo: {
        name: "university_application_skill_web",
        title: "University Application Skill Website",
        version: "0.1.0",
      },
    });
    client.notify("initialized");
    return await task(client);
  } finally {
    client.close();
  }
}

async function fetchBridge<T>(endpoint: string, path: string, init?: RequestInit) {
  const response = await fetch(`${endpoint}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Bridge ${path} returned HTTP ${response.status}.`);
  }

  return await response.json() as T;
}

function normalizeAccount(payload: unknown): CodexAccountReadResult {
  if (!isRecord(payload)) {
    return { account: null, requiresOpenaiAuth: false, connected: false };
  }

  const rawAccount = isRecord(payload.account) ? payload.account : null;
  const connected = typeof payload.connected === "boolean" ? payload.connected : rawAccount !== null;
  const requiresOpenaiAuth = typeof payload.requiresOpenaiAuth === "boolean" ? payload.requiresOpenaiAuth : connected;

  if (!rawAccount) {
    return { account: null, requiresOpenaiAuth, connected };
  }

  return {
    account: {
      type: String(rawAccount.type ?? "unknown"),
      email: typeof rawAccount.email === "string" ? rawAccount.email : undefined,
      planType: typeof rawAccount.planType === "string" || rawAccount.planType === null ? rawAccount.planType : undefined,
      credentialSource: typeof rawAccount.credentialSource === "string" ? rawAccount.credentialSource : undefined,
    },
    requiresOpenaiAuth,
    connected,
  };
}

function normalizeLogin(payload: unknown): CodexLoginResult {
  if (!isRecord(payload)) {
    return { type: "bridge", message: "Bridge started login without returning extra details." };
  }

  if (payload.type === "chatgpt" && typeof payload.loginId === "string" && typeof payload.authUrl === "string") {
    return {
      type: "chatgpt",
      loginId: payload.loginId,
      authUrl: payload.authUrl,
    };
  }

  if (
    payload.type === "chatgptDeviceCode" &&
    typeof payload.loginId === "string" &&
    typeof payload.verificationUrl === "string" &&
    typeof payload.userCode === "string"
  ) {
    return {
      type: "chatgptDeviceCode",
      loginId: payload.loginId,
      verificationUrl: payload.verificationUrl,
      userCode: payload.userCode,
    };
  }

  return {
    type: "bridge",
    loginId: typeof payload.loginId === "string" ? payload.loginId : undefined,
    authUrl: typeof payload.authUrl === "string" ? payload.authUrl : undefined,
    verificationUrl: typeof payload.verificationUrl === "string" ? payload.verificationUrl : undefined,
    userCode: typeof payload.userCode === "string" ? payload.userCode : undefined,
    message: typeof payload.message === "string" ? payload.message : undefined,
  };
}

export async function readCodexAccount(endpoint: string, refreshToken: boolean) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    return normalizeAccount(await fetchBridge(validation.endpoint, refreshToken ? "/codex/refresh" : "/codex/status", {
      method: refreshToken ? "POST" : "GET",
    }));
  }

  return withCodexClient(validation.endpoint, async (client) => {
    const result = await client.request("account/read", { refreshToken });
    return normalizeAccount(result);
  });
}

export async function startCodexLogin(endpoint: string, flow: CodexLoginFlow) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    return normalizeLogin(await fetchBridge(validation.endpoint, "/codex/start-oauth", {
      method: "POST",
      body: JSON.stringify({ flow }),
    }));
  }

  return withCodexClient(validation.endpoint, async (client) => {
    const result = await client.request("account/login/start", {
      type: flow === "browser" ? "chatgpt" : "chatgptDeviceCode",
    });
    return normalizeLogin(result);
  });
}

export async function logoutCodex(endpoint: string) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    await fetchBridge(validation.endpoint, "/codex/logout", { method: "POST" });
    return;
  }

  await withCodexClient(validation.endpoint, async (client) => {
    await client.request("account/logout");
  });
}
