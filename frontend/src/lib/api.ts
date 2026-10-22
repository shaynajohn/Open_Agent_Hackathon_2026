import type {
  OutreachRequest,
  OutreachResponse,
  SearchRequest,
  SearchResponse,
} from "@/lib/types";

export function apiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return configured.replace(/\/$/, "");
}

export async function searchPeople(body: SearchRequest): Promise<SearchResponse> {
  return postJson<SearchResponse>("/api/search", body);
}

export async function createOutreach(body: OutreachRequest): Promise<OutreachResponse> {
  return postJson<OutreachResponse>("/api/outreach", body);
}

export async function apiIsReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${apiBaseUrl()}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(
      `Could not reach the MeetMind API at ${apiBaseUrl()}. Start the backend and try again.`,
    );
  }

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }

  return (await response.json()) as T;
}

async function errorMessage(response: Response): Promise<string> {
  const payload: unknown = await response.json().catch(() => null);
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return "";
        })
        .filter(Boolean);
      if (messages.length > 0) {
        return messages.join(" ");
      }
    }
  }
  return `The request failed (${response.status}).`;
}
