type JsonObject = Record<string, unknown>;

export type CodexEndpointKind = "app-server-ws" | "bridge-http";
export type CodexLoginFlow = "browser" | "device";
export type AIRuntimeMode = "codex-oauth" | "api-key" | "openai-compatible" | "local-api" | "cli";
export type AIConfigFormat = "env" | "json" | "yaml" | "curl" | "cli";
export type AIProviderId =
  | "codex-oauth"
  | "openai-api"
  | "openrouter-api"
  | "anthropic-api"
  | "gemini-api"
  | "deepseek-api"
  | "ollama-local"
  | "openai-compatible"
  | "hermes-cli"
  | "custom-cli";

export interface CodexEndpointValidation {
  endpoint: string;
  kind?: CodexEndpointKind;
  valid: boolean;
  message: string;
}

export interface AIProviderProfile {
  id: AIProviderId;
  label: string;
  runtime: AIRuntimeMode;
  defaultModel: string;
  defaultBaseUrl?: string;
  credentialEnvVars: string[];
  defaultCliCommand?: string;
  notes: string[];
}

export interface AIConfig {
  providerId: AIProviderId;
  model: string;
  baseUrl: string;
  endpoint: string;
  bridgeNonce: string;
  keyEnvVar: string;
  cliCommand: string;
  configFormat: AIConfigFormat;
}

export interface AIConfigValidation {
  valid: boolean;
  message: string;
  runtime: AIRuntimeMode;
  endpointKind?: CodexEndpointKind;
}

export interface AIConfigPreview {
  title: string;
  body: string;
  notes: string[];
}

export interface CodexBridgeHealth {
  ok: boolean;
  nonceRequired?: boolean;
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

export interface ExtractedInspirationBlock {
  label: string;
  text: string;
}

export interface ExtractInspirationFileRequest {
  name: string;
  mimeType: string;
  contentBase64: string;
}

export interface ExtractInspirationFileResult {
  ok: boolean;
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  blocks: ExtractedInspirationBlock[];
  preview: string;
  warnings: string[];
  error?: string;
}

const aiConfigStorageKey = "soleil.ai.config";
const endpointStorageKey = "soleil.ai.endpoint";
const bridgeNonceStorageKey = "soleil.ai.bridgeNonce";
const legacyEndpointStorageKey = "soleil.codex.oauth.endpoint";
const legacyBridgeNonceStorageKey = "soleil.codex.oauth.bridgeNonce";
const defaultBridgeEndpoint = "http://127.0.0.1:8787";

export const AI_PROVIDER_PROFILES: AIProviderProfile[] = [
  {
    id: "codex-oauth",
    label: "Codex OAuth / Local Bridge",
    runtime: "codex-oauth",
    defaultModel: "codex-default",
    credentialEnvVars: [],
    notes: ["Uses the existing Codex app-server or trusted localhost bridge.", "The page never reads Codex tokens."],
  },
  {
    id: "openai-api",
    label: "OpenAI API",
    runtime: "openai-compatible",
    defaultModel: "gpt-4.1",
    defaultBaseUrl: "https://api.openai.com/v1",
    credentialEnvVars: ["OPENAI_API_KEY"],
    notes: ["OpenAI-compatible chat completions format."],
  },
  {
    id: "openrouter-api",
    label: "OpenRouter API",
    runtime: "openai-compatible",
    defaultModel: "openai/gpt-4.1",
    defaultBaseUrl: "https://openrouter.ai/api/v1",
    credentialEnvVars: ["OPENROUTER_API_KEY"],
    notes: ["OpenAI-compatible routing format with provider-qualified model names."],
  },
  {
    id: "anthropic-api",
    label: "Anthropic API",
    runtime: "api-key",
    defaultModel: "claude-sonnet-4",
    defaultBaseUrl: "https://api.anthropic.com/v1",
    credentialEnvVars: ["ANTHROPIC_API_KEY"],
    notes: ["Provider-specific messages API format."],
  },
  {
    id: "gemini-api",
    label: "Gemini API",
    runtime: "api-key",
    defaultModel: "gemini-2.5-pro",
    defaultBaseUrl: "https://generativelanguage.googleapis.com/v1beta",
    credentialEnvVars: ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    notes: ["Provider-specific generateContent format."],
  },
  {
    id: "deepseek-api",
    label: "DeepSeek API",
    runtime: "openai-compatible",
    defaultModel: "deepseek-chat",
    defaultBaseUrl: "https://api.deepseek.com/v1",
    credentialEnvVars: ["DEEPSEEK_API_KEY"],
    notes: ["OpenAI-compatible chat completions format."],
  },
  {
    id: "ollama-local",
    label: "Ollama Local API",
    runtime: "local-api",
    defaultModel: "llama3.1",
    defaultBaseUrl: "http://127.0.0.1:11434",
    credentialEnvVars: [],
    notes: ["Local HTTP runtime; no browser-stored secret."],
  },
  {
    id: "openai-compatible",
    label: "Custom OpenAI-Compatible API",
    runtime: "openai-compatible",
    defaultModel: "model-name",
    defaultBaseUrl: "https://api.example.com/v1",
    credentialEnvVars: ["AI_API_KEY"],
    notes: ["Use for vLLM, LM Studio server mode, LiteLLM, or a compatible proxy."],
  },
  {
    id: "hermes-cli",
    label: "Hermes CLI Profile",
    runtime: "cli",
    defaultModel: "openrouter/horizon-beta",
    credentialEnvVars: ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    defaultCliCommand: "hermes --model {model}",
    notes: ["CLI command template; edit it to match the installed Hermes command surface."],
  },
  {
    id: "custom-cli",
    label: "Custom CLI Adapter",
    runtime: "cli",
    defaultModel: "model-name",
    credentialEnvVars: ["AI_API_KEY"],
    defaultCliCommand: "your-cli --model {model}",
    notes: ["Use for Codex CLI, Claude Code, Gemini CLI, Aider, OpenCode, or any local wrapper."],
  },
];

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

function profileById(providerId: string | null | undefined) {
  return AI_PROVIDER_PROFILES.find((profile) => profile.id === providerId) ?? AI_PROVIDER_PROFILES[0];
}

function isAIProviderId(value: string): value is AIProviderId {
  return AI_PROVIDER_PROFILES.some((profile) => profile.id === value);
}

function isAIConfigFormat(value: string): value is AIConfigFormat {
  return ["env", "json", "yaml", "curl", "cli"].includes(value);
}

function parseStoredAIConfig(value: string | null): Partial<AIConfig> {
  if (!value) {
    return {};
  }

  try {
    const parsed = JSON.parse(value);
    return isRecord(parsed) ? parsed as Partial<AIConfig> : {};
  } catch {
    return {};
  }
}

function readStorage(key: string) {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(key);
}

function firstCredentialEnvVar(profile: AIProviderProfile) {
  return profile.credentialEnvVars[0] ?? "AI_API_KEY";
}

function normalizeConfig(config: AIConfig): AIConfig {
  const profile = profileById(config.providerId);
  return {
    providerId: profile.id,
    model: config.model.trim() || profile.defaultModel,
    baseUrl: trimTrailingSlash(config.baseUrl.trim() || (profile.defaultBaseUrl ?? "")),
    endpoint: trimTrailingSlash(config.endpoint.trim() || defaultBridgeEndpoint),
    bridgeNonce: config.bridgeNonce.trim(),
    keyEnvVar: config.keyEnvVar.trim() || firstCredentialEnvVar(profile),
    cliCommand: config.cliCommand.trim() || (profile.defaultCliCommand ?? ""),
    configFormat: config.configFormat,
  };
}

export function getAIProviderProfile(providerId: AIProviderId) {
  return profileById(providerId);
}

export function getInitialAIConfig(): AIConfig {
  if (typeof window === "undefined") {
    const profile = AI_PROVIDER_PROFILES[0];
    return {
      providerId: profile.id,
      model: profile.defaultModel,
      baseUrl: profile.defaultBaseUrl ?? "",
      endpoint: defaultBridgeEndpoint,
      bridgeNonce: "",
      keyEnvVar: firstCredentialEnvVar(profile),
      cliCommand: profile.defaultCliCommand ?? "",
      configFormat: "env",
    };
  }

  const params = new URLSearchParams(window.location.search);
  const stored = parseStoredAIConfig(window.localStorage.getItem(aiConfigStorageKey));
  const providerFromQuery = params.get("ai_provider");
  const providerId = providerFromQuery && isAIProviderId(providerFromQuery)
    ? providerFromQuery
    : isAIProviderId(String(stored.providerId))
      ? stored.providerId as AIProviderId
      : "codex-oauth";
  const profile = profileById(providerId);
  const formatFromQuery = params.get("ai_format");
  const configFormat = formatFromQuery && isAIConfigFormat(formatFromQuery)
    ? formatFromQuery
    : isAIConfigFormat(String(stored.configFormat))
      ? stored.configFormat as AIConfigFormat
      : "env";

  return normalizeConfig({
    providerId,
    model: params.get("ai_model") ?? stored.model ?? profile.defaultModel,
    baseUrl: params.get("ai_base_url") ?? stored.baseUrl ?? profile.defaultBaseUrl ?? "",
    endpoint:
      params.get("ai_endpoint") ??
      params.get("codex_ws") ??
      params.get("codex_bridge") ??
      stored.endpoint ??
      readStorage(endpointStorageKey) ??
      readStorage(legacyEndpointStorageKey) ??
      defaultBridgeEndpoint,
    bridgeNonce:
      params.get("ai_bridge_nonce") ??
      params.get("codex_bridge_nonce") ??
      params.get("codex_nonce") ??
      stored.bridgeNonce ??
      readStorage(bridgeNonceStorageKey) ??
      readStorage(legacyBridgeNonceStorageKey) ??
      "",
    keyEnvVar: params.get("ai_key_env") ?? stored.keyEnvVar ?? firstCredentialEnvVar(profile),
    cliCommand: params.get("ai_cli") ?? stored.cliCommand ?? profile.defaultCliCommand ?? "",
    configFormat,
  });
}

export function rememberAIConfig(config: AIConfig) {
  if (typeof window === "undefined") {
    return;
  }

  const normalized = normalizeConfig(config);
  window.localStorage.setItem(aiConfigStorageKey, JSON.stringify(normalized));
  window.localStorage.setItem(endpointStorageKey, normalized.endpoint);
  if (normalized.bridgeNonce) {
    window.localStorage.setItem(bridgeNonceStorageKey, normalized.bridgeNonce);
  } else {
    window.localStorage.removeItem(bridgeNonceStorageKey);
  }
}

export function applyAIProviderDefaults(config: AIConfig, providerId: AIProviderId): AIConfig {
  const profile = profileById(providerId);
  return normalizeConfig({
    ...config,
    providerId: profile.id,
    model: profile.defaultModel,
    baseUrl: profile.defaultBaseUrl ?? "",
    keyEnvVar: firstCredentialEnvVar(profile),
    cliCommand: profile.defaultCliCommand ?? "",
    endpoint: config.endpoint || defaultBridgeEndpoint,
  });
}

function validateUrl(input: string, allowPlainLoopback = false) {
  let url: URL;
  try {
    url = new URL(input);
  } catch {
    return "URL is invalid.";
  }

  if (url.username || url.password) {
    return "Do not embed credentials in URLs.";
  }

  if (url.protocol === "http:" && !allowPlainLoopback && !isLoopbackHost(url.hostname)) {
    return "Plain HTTP is allowed only for localhost or 127.0.0.1.";
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    return "Use http:// or https://.";
  }

  return "";
}

export function validateAIConfig(config: AIConfig): AIConfigValidation {
  const normalized = normalizeConfig(config);
  const profile = profileById(normalized.providerId);

  if (!normalized.model) {
    return { valid: false, message: "Model is required.", runtime: profile.runtime };
  }

  if (profile.runtime === "codex-oauth") {
    const endpointValidation = validateCodexEndpoint(normalized.endpoint);
    return {
      valid: endpointValidation.valid,
      message: endpointValidation.message,
      runtime: profile.runtime,
      endpointKind: endpointValidation.kind,
    };
  }

  if (profile.runtime === "cli") {
    return normalized.cliCommand
      ? { valid: true, message: "CLI command template is configured. Secrets must stay in the CLI environment.", runtime: profile.runtime }
      : { valid: false, message: "CLI command template is required.", runtime: profile.runtime };
  }

  if (profile.credentialEnvVars.length && !/^[A-Z_][A-Z0-9_]*$/.test(normalized.keyEnvVar)) {
    return { valid: false, message: "Credential environment variable must look like OPENAI_API_KEY.", runtime: profile.runtime };
  }

  if (!normalized.baseUrl) {
    return { valid: false, message: "Base URL is required for API providers.", runtime: profile.runtime };
  }

  const urlError = validateUrl(normalized.baseUrl, profile.runtime === "local-api");
  return {
    valid: !urlError,
    message: urlError || "AI API configuration is valid. Store only the environment variable name here, not the key value.",
    runtime: profile.runtime,
  };
}

function interpolateCliCommand(config: AIConfig) {
  const normalized = normalizeConfig(config);
  return normalized.cliCommand
    .split("{model}").join(normalized.model)
    .split("{baseUrl}").join(normalized.baseUrl)
    .split("{endpoint}").join(normalized.endpoint)
    .split("{envVar}").join(normalized.keyEnvVar);
}

function yamlLine(key: string, value: string, indent = "") {
  return `${indent}${key}: ${JSON.stringify(value)}`;
}

function openAiCompatibleCurl(config: AIConfig) {
  const normalized = normalizeConfig(config);
  const base = normalized.baseUrl.replace(/\/$/, "");
  return `curl "${base}/chat/completions" \\
  -H "Authorization: Bearer $${normalized.keyEnvVar}" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify({
    model: normalized.model,
    messages: [{ role: "user", content: "Write a one sentence status update." }],
  })}'`;
}

export function buildAIConfigPreview(config: AIConfig): AIConfigPreview {
  const normalized = normalizeConfig(config);
  const profile = profileById(normalized.providerId);
  const notes = profile.notes;
  const commonJson = {
    provider: profile.id,
    runtime: profile.runtime,
    model: normalized.model,
    credential: profile.credentialEnvVars.length ? { env: normalized.keyEnvVar } : "none",
    baseUrl: normalized.baseUrl || undefined,
    endpoint: profile.runtime === "codex-oauth" ? normalized.endpoint : undefined,
  };

  if (normalized.configFormat === "json") {
    return { title: "JSON config", body: JSON.stringify(commonJson, null, 2), notes };
  }

  if (normalized.configFormat === "yaml") {
    const body = [
      yamlLine("provider", profile.id),
      yamlLine("runtime", profile.runtime),
      yamlLine("model", normalized.model),
      profile.credentialEnvVars.length ? "credential:" : "credential: none",
      ...(profile.credentialEnvVars.length ? [yamlLine("env", normalized.keyEnvVar, "  ")] : []),
      normalized.baseUrl ? "endpoint:" : "",
      normalized.baseUrl ? yamlLine("base_url", normalized.baseUrl, "  ") : "",
      profile.runtime === "codex-oauth" ? yamlLine("codex_endpoint", normalized.endpoint) : "",
    ].filter(Boolean).join("\n");
    return { title: "YAML config", body, notes };
  }

  if (normalized.configFormat === "cli") {
    if (profile.runtime === "codex-oauth") {
      return {
        title: "Codex bridge commands",
        body: `node scripts/codex_oauth_bridge.mjs --port 8787\ncodex app-server --listen ws://127.0.0.1:4500`,
        notes,
      };
    }

    const secretLine = profile.credentialEnvVars.length ? `export ${normalized.keyEnvVar}=...` : "# No API key environment variable is required.";
    return { title: "CLI command template", body: `${secretLine}\n${interpolateCliCommand(normalized)}`, notes };
  }

  if (normalized.configFormat === "curl") {
    if (profile.runtime === "codex-oauth") {
      return {
        title: "Codex bridge HTTP contract",
        body: `curl "${normalized.endpoint}/codex/status"${normalized.bridgeNonce ? ` \\\n  -H "x-codex-bridge-nonce: ${normalized.bridgeNonce}"` : ""}\n\ncurl "${normalized.endpoint}/writing/inspiration/extract" \\\n  -H "content-type: application/json"${normalized.bridgeNonce ? ` \\\n  -H "x-codex-bridge-nonce: ${normalized.bridgeNonce}"` : ""} \\\n  -d '{"name":"notes.txt","mimeType":"text/plain","contentBase64":"..."}'`,
        notes,
      };
    }

    if (profile.id === "anthropic-api") {
      return {
        title: "Anthropic messages request",
        body: `curl "${normalized.baseUrl.replace(/\/$/, "")}/messages" \\
  -H "x-api-key: $${normalized.keyEnvVar}" \\
  -H "anthropic-version: 2023-06-01" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify({
    model: normalized.model,
    max_tokens: 1024,
    messages: [{ role: "user", content: "Write a one sentence status update." }],
  })}'`,
        notes,
      };
    }

    if (profile.id === "gemini-api") {
      return {
        title: "Gemini generateContent request",
        body: `curl "${normalized.baseUrl.replace(/\/$/, "")}/models/${normalized.model}:generateContent?key=$${normalized.keyEnvVar}" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify({ contents: [{ parts: [{ text: "Write a one sentence status update." }] }] })}'`,
        notes,
      };
    }

    if (profile.id === "ollama-local") {
      return {
        title: "Ollama local chat request",
        body: `curl "${normalized.baseUrl.replace(/\/$/, "")}/api/chat" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify({
    model: normalized.model,
    messages: [{ role: "user", content: "Write a one sentence status update." }],
    stream: false,
  })}'`,
        notes,
      };
    }

    return { title: "OpenAI-compatible chat request", body: openAiCompatibleCurl(normalized), notes };
  }

  if (profile.runtime === "codex-oauth") {
    const lines = [
      "AI_PROVIDER=codex-oauth",
      `AI_MODEL=${normalized.model}`,
      `CODEX_ENDPOINT=${normalized.endpoint}`,
      normalized.bridgeNonce ? `CODEX_BRIDGE_NONCE=${normalized.bridgeNonce}` : "# CODEX_BRIDGE_NONCE=printed-by-local-bridge",
    ];
    return { title: "Environment config", body: lines.join("\n"), notes };
  }

  const lines = [
    `AI_PROVIDER=${profile.id}`,
    `AI_MODEL=${normalized.model}`,
    normalized.baseUrl ? `AI_BASE_URL=${normalized.baseUrl}` : "",
    profile.credentialEnvVars.length ? `${normalized.keyEnvVar}=...` : "# No API key environment variable is required.",
  ].filter(Boolean);
  return { title: "Environment config", body: lines.join("\n"), notes };
}

export function getInitialCodexEndpoint() {
  if (typeof window === "undefined") {
    return defaultBridgeEndpoint;
  }

  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("ai_endpoint") ?? params.get("codex_ws") ?? params.get("codex_bridge");
  if (fromQuery) {
    return fromQuery;
  }

  return window.localStorage.getItem(endpointStorageKey) ?? window.localStorage.getItem(legacyEndpointStorageKey) ?? defaultBridgeEndpoint;
}

export function rememberCodexEndpoint(endpoint: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(endpointStorageKey, endpoint.trim());
  }
}

export function getInitialCodexBridgeNonce() {
  if (typeof window === "undefined") {
    return "";
  }

  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("ai_bridge_nonce") ?? params.get("codex_bridge_nonce") ?? params.get("codex_nonce");
  if (fromQuery) {
    return fromQuery;
  }

  return window.localStorage.getItem(bridgeNonceStorageKey) ?? window.localStorage.getItem(legacyBridgeNonceStorageKey) ?? "";
}

export function rememberCodexBridgeNonce(nonce: string) {
  if (typeof window !== "undefined") {
    const value = nonce.trim();
    if (value) {
      window.localStorage.setItem(bridgeNonceStorageKey, value);
    } else {
      window.localStorage.removeItem(bridgeNonceStorageKey);
    }
  }
}

export function isDefaultCodexEndpoint(input: string) {
  return trimTrailingSlash(input.trim()) === defaultBridgeEndpoint;
}

export function hasExplicitCodexEndpoint() {
  if (typeof window === "undefined") {
    return false;
  }

  const params = new URLSearchParams(window.location.search);
  const storedConfig = parseStoredAIConfig(window.localStorage.getItem(aiConfigStorageKey));
  const stored = window.localStorage.getItem(endpointStorageKey) ?? storedConfig.endpoint;
  return params.has("ai_endpoint") || params.has("codex_ws") || params.has("codex_bridge") || Boolean(stored && !isDefaultCodexEndpoint(stored));
}

export function isGithubPagesRuntime() {
  return typeof window !== "undefined" && window.location.hostname.endsWith("github.io");
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

function bridgeHeaders(nonce?: string) {
  return nonce?.trim() ? { "x-codex-bridge-nonce": nonce.trim() } : {};
}

async function fetchBridge<T>(endpoint: string, path: string, init?: RequestInit, nonce?: string) {
  const headers = new Headers(init?.headers);
  headers.set("content-type", "application/json");
  const nonceValue = bridgeHeaders(nonce)["x-codex-bridge-nonce"];
  if (nonceValue) {
    headers.set("x-codex-bridge-nonce", nonceValue);
  }

  const response = await fetch(`${endpoint}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = `Bridge ${path} returned HTTP ${response.status}.`;
    try {
      const payload = await response.json();
      if (isRecord(payload) && typeof payload.error === "string") {
        message = payload.error;
      }
    } catch {
      // Keep the status-based message when the bridge does not return JSON.
    }
    throw new Error(message);
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

function normalizeExtractResult(payload: unknown): ExtractInspirationFileResult {
  if (!isRecord(payload)) {
    return {
      ok: false,
      fileName: "uploaded-file",
      mimeType: "application/octet-stream",
      sizeBytes: 0,
      blocks: [],
      preview: "",
      warnings: ["Bridge returned an invalid extraction response."],
      error: "Bridge returned an invalid extraction response.",
    };
  }

  const blocks = Array.isArray(payload.blocks)
    ? payload.blocks.flatMap((block) => {
      if (!isRecord(block) || typeof block.label !== "string" || typeof block.text !== "string") {
        return [];
      }
      return [{ label: block.label, text: block.text }];
    })
    : [];
  const warnings = Array.isArray(payload.warnings)
    ? payload.warnings.filter((warning): warning is string => typeof warning === "string")
    : [];

  return {
    ok: Boolean(payload.ok),
    fileName: typeof payload.fileName === "string" ? payload.fileName : "uploaded-file",
    mimeType: typeof payload.mimeType === "string" ? payload.mimeType : "application/octet-stream",
    sizeBytes: typeof payload.sizeBytes === "number" ? payload.sizeBytes : 0,
    blocks,
    preview: typeof payload.preview === "string" ? payload.preview : blocks.map((block) => `${block.label}: ${block.text}`).join("\n\n"),
    warnings,
    error: typeof payload.error === "string" ? payload.error : undefined,
  };
}

export async function probeCodexBridge(endpoint: string, bridgeNonce?: string) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || validation.kind !== "bridge-http") {
    throw new Error(validation.kind === "app-server-ws" ? "Health probe is only used for HTTP bridge endpoints." : validation.message);
  }

  return await fetchBridge<CodexBridgeHealth>(validation.endpoint, "/health", { method: "GET" }, bridgeNonce);
}

export async function readCodexAccount(endpoint: string, refreshToken: boolean, bridgeNonce?: string) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    return normalizeAccount(await fetchBridge(validation.endpoint, refreshToken ? "/codex/refresh" : "/codex/status", {
      method: refreshToken ? "POST" : "GET",
    }, bridgeNonce));
  }

  return withCodexClient(validation.endpoint, async (client) => {
    const result = await client.request("account/read", { refreshToken });
    return normalizeAccount(result);
  });
}

export async function startCodexLogin(endpoint: string, flow: CodexLoginFlow, bridgeNonce?: string) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    return normalizeLogin(await fetchBridge(validation.endpoint, "/codex/start-oauth", {
      method: "POST",
      body: JSON.stringify({ flow }),
    }, bridgeNonce));
  }

  return withCodexClient(validation.endpoint, async (client) => {
    const result = await client.request("account/login/start", {
      type: flow === "browser" ? "chatgpt" : "chatgptDeviceCode",
    });
    return normalizeLogin(result);
  });
}

export async function logoutCodex(endpoint: string, bridgeNonce?: string) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }

  if (validation.kind === "bridge-http") {
    await fetchBridge(validation.endpoint, "/codex/logout", { method: "POST" }, bridgeNonce);
    return;
  }

  await withCodexClient(validation.endpoint, async (client) => {
    await client.request("account/logout");
  });
}

export async function extractInspirationFile(endpoint: string, bridgeNonce: string, request: ExtractInspirationFileRequest) {
  const validation = validateCodexEndpoint(endpoint);
  if (!validation.valid || !validation.kind) {
    throw new Error(validation.message);
  }
  if (validation.kind !== "bridge-http") {
    throw new Error("Writing inspiration extraction requires the trusted HTTP bridge endpoint.");
  }

  const payload = await fetchBridge<unknown>(validation.endpoint, "/writing/inspiration/extract", {
    method: "POST",
    body: JSON.stringify(request),
  }, bridgeNonce);
  return normalizeExtractResult(payload);
}
