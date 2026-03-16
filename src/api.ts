import { raiseForCode } from "./errors.js";

interface ApiResponse {
  code: number;
  msg?: string;
  trace_id?: string;
  data: Record<string, unknown>;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;

  constructor(token: string, baseUrl: string) {
    this.baseUrl = baseUrl;
    this.headers = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  async post(
    path: string,
    json: Record<string, unknown>,
  ): Promise<ApiResponse> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(json),
    });
    return this.handle(resp);
  }

  async get(path: string): Promise<ApiResponse> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: this.headers,
    });
    return this.handle(resp);
  }

  async putFile(url: string, data: Uint8Array): Promise<void> {
    const resp = await fetch(url, {
      method: "PUT",
      body: data,
    });
    if (!resp.ok) {
      throw new Error(`Upload failed: ${resp.status} ${resp.statusText}`);
    }
  }

  async download(url: string): Promise<Uint8Array> {
    const resp = await fetch(url, { redirect: "follow" });
    if (!resp.ok) {
      throw new Error(`Download failed: ${resp.status} ${resp.statusText}`);
    }
    return new Uint8Array(await resp.arrayBuffer());
  }

  private async handle(resp: Response): Promise<ApiResponse> {
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(
        `HTTP ${resp.status}: ${resp.statusText}${text ? ` — ${text}` : ""}`,
      );
    }
    const body = (await resp.json()) as ApiResponse;
    if (body.code !== 0) {
      raiseForCode(body.code, body.msg ?? "unknown error", body.trace_id ?? "");
    }
    return body;
  }
}
