export type ApiErrorShape = {
  message: string;
  status?: number;
  details?: unknown;
};

const DEFAULT_BASE = '/api';

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE).replace(/\/$/, '');
}

export async function apiGet<T>(path: string): Promise<T> {
  const base = getApiBaseUrl();
  const url = `${base}${path.startsWith('/') ? '' : '/'}${path}`;

  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    let details: unknown = undefined;
    try {
      details = await res.json();
    } catch {
      // ignore
    }
    const err: ApiErrorShape = { message: `GET ${url} failed`, status: res.status, details };
    throw err;
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const base = getApiBaseUrl();
  const url = `${base}${path.startsWith('/') ? '' : '/'}${path}`;

  const res = await fetch(url, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : '{}'
  });

  if (!res.ok) {
    let details: unknown = undefined;
    try {
      details = await res.json();
    } catch {
      // ignore
    }
    const err: ApiErrorShape = { message: `POST ${url} failed`, status: res.status, details };
    throw err;
  }

  return (await res.json()) as T;
}

