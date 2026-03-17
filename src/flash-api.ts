import { raiseForCode } from "./errors.js";

// TODO(release): 上线前换回 https://mineru.net/api/v1/agent
const DEFAULT_FLASH_BASE_URL = "https://staging.mineru.org.cn/api/v1/agent";

interface FlashApiResponse {
  code: number;
  msg?: string;
  trace_id?: string;
  data: Record<string, unknown>;
}

export { DEFAULT_FLASH_BASE_URL };

export class FlashApiClient {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;
  private source: string;

  constructor(baseUrl: string = DEFAULT_FLASH_BASE_URL, source = "") {
    this.baseUrl = baseUrl;
    this.headers = { "Content-Type": "application/json" };
    this.source = source;
  }

  setSource(source: string): void {
    this.source = source;
  }

  async post(
    path: string,
    json: Record<string, unknown>,
  ): Promise<FlashApiResponse> {
    const headers: Record<string, string> = { ...this.headers };
    if (this.source) {
      headers["source"] = this.source;
    }
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(json),
    });
    return this.handle(resp);
  }

  async get(path: string): Promise<FlashApiResponse> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
    });
    return this.handle(resp);
  }

  async putFile(url: string, data: Uint8Array): Promise<void> {
    const resp = await fetch(url, { method: "PUT", body: data });
    if (!resp.ok) {
      throw new Error(`Upload failed: ${resp.status} ${resp.statusText}`);
    }
  }

  async downloadText(url: string): Promise<string> {
    const resp = await fetch(url, { redirect: "follow" });
    if (!resp.ok) {
      throw new Error(`Download failed: ${resp.status} ${resp.statusText}`);
    }
    return resp.text();
  }

  private async handle(resp: Response): Promise<FlashApiResponse> {
    if (resp.status === 429) {
      raiseForCode(
        "RATE_LIMITED",
        "flash API rate limit exceeded; try again later",
      );
    }
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(
        `HTTP ${resp.status}: ${resp.statusText}${text ? ` — ${text}` : ""}`,
      );
    }
    const body = (await resp.json()) as FlashApiResponse;
    if (body.code !== 0) {
      raiseForCode(body.code, body.msg ?? "unknown error", body.trace_id ?? "");
    }
    return body;
  }
}
