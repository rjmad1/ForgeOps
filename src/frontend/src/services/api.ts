const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8088';

export interface Service {
  id: string;
  name: string;
  type: string;
  port: number | null;
  status: string;
  pid: number | null;
  binary_path: string | null;
  args: string[];
  config_path: string | null;
  auto_start: boolean;
}

export interface Model {
  id: string;
  name: string;
  type: string;
  provider: string;
  metadata: {
    size_bytes?: number;
    family?: string;
    parameter_size?: string;
    quantization_level?: string;
    format?: string;
    description?: string;
    [key: string]: any;
  };
}

export interface SystemMetrics {
  cpu: {
    utilization_pct: number;
  };
  ram: {
    total_bytes: number;
    available_bytes: number;
    used_bytes: number;
    utilization_pct: number;
  };
  gpu: {
    available: boolean;
    name: string;
    utilization_pct: number;
    vram_used_bytes: number;
    vram_total_bytes: number;
  };
}

export interface HistoryEvent {
  id: number;
  event_type: string;
  service_id: string | null;
  severity: string;
  message: string;
  details: any;
  timestamp: string;
}

export interface InventoryItem {
  key: string;
  category: string;
  value: any;
  last_updated: string;
}

let cachedToken: string | null = null;

function getCookie(name: string): string | null {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

export async function ensureAuthToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  
  // Try cookie first
  const cookieToken = getCookie("session_api_key");
  if (cookieToken) {
    cachedToken = cookieToken;
    return cookieToken;
  }
  
  // Handshake with backend to fetch token (specifically for dev mode port 5173)
  try {
    const res = await fetch(`${BASE_URL}/api/v1/auth/token`, { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      if (data.token) {
        cachedToken = data.token;
        return data.token;
      }
    }
  } catch (e) {
    console.warn("Could not handshake auth token:", e);
  }
  
  return "";
}

async function authedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = await ensureAuthToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("X-API-Key", token);
  }
  return fetch(url, { ...options, headers });
}

export async function fetchServices(refresh = false): Promise<Service[]> {
  const res = await authedFetch(`${BASE_URL}/api/v1/services?refresh=${refresh}`);
  if (!res.ok) throw new Error('Failed to fetch services');
  return res.json();
}

export async function fetchModels(): Promise<Model[]> {
  const res = await authedFetch(`${BASE_URL}/api/v1/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function fetchHealth(): Promise<{ status: string; services: Record<string, string> }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/health`);
  if (!res.ok) throw new Error('Failed to fetch health');
  return res.json();
}

export async function fetchSystemMetrics(): Promise<SystemMetrics> {
  const res = await authedFetch(`${BASE_URL}/api/v1/system/metrics`);
  if (!res.ok) throw new Error('Failed to fetch system metrics');
  return res.json();
}

export async function fetchHistory(limit = 20): Promise<HistoryEvent[]> {
  const res = await authedFetch(`${BASE_URL}/api/v1/history?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch operational history');
  return res.json();
}

export async function fetchInventory(): Promise<InventoryItem[]> {
  const res = await authedFetch(`${BASE_URL}/api/v1/inventory`);
  if (!res.ok) throw new Error('Failed to fetch inventory');
  return res.json();
}

export async function triggerInventoryScan(): Promise<{ status: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/inventory/discover`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger inventory scan');
  return res.json();
}

export async function startService(serviceId: string): Promise<{ status: string; pid?: number }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/services/${serviceId}/start`, { method: 'POST' });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Failed to start service');
  }
  return res.json();
}

export async function stopService(serviceId: string): Promise<{ status: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/services/${serviceId}/stop`, { method: 'POST' });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Failed to stop service');
  }
  return res.json();
}

export async function restartService(serviceId: string): Promise<{ status: string; pid?: number }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/services/${serviceId}/restart`, { method: 'POST' });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || 'Failed to restart service');
  }
  return res.json();
}

export async function fetchServiceLogs(serviceId: string, limit = 100): Promise<{ service_id: string; logs: string[]; message?: string; log_file_path?: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/services/${serviceId}/logs?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch service logs');
  return res.json();
}

export async function fetchConfig(key: string): Promise<{ key: string; value: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/config/${key}`);
  if (!res.ok) throw new Error('Config key not found');
  return res.json();
}

export async function updateConfig(data: { key: string; value: string }): Promise<{ status: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update config');
  return res.json();
}

export async function fetchPlugins(): Promise<any[]> {
  const res = await authedFetch(`${BASE_URL}/api/v1/plugins`);
  if (!res.ok) throw new Error('Failed to fetch plugins');
  return res.json();
}

export interface UpdateStatus {
  installed: boolean;
  current_version: string | null;
  latest_version: string;
}

export interface UpdateCheckResponse {
  ollama: UpdateStatus;
  litellm: UpdateStatus;
  openclaw: UpdateStatus;
}

export async function fetchUpdates(): Promise<UpdateCheckResponse> {
  const res = await authedFetch(`${BASE_URL}/api/v1/updates/check`);
  if (!res.ok) throw new Error('Failed to check updates');
  return res.json();
}

export async function triggerUpdate(target: string): Promise<{ status: string; message: string }> {
  const res = await authedFetch(`${BASE_URL}/api/v1/updates/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Failed to trigger update');
  }
  return res.json();
}

export async function fetchDiagnosticsReport(): Promise<any> {
  const res = await authedFetch(`${BASE_URL}/api/v1/diagnostics/report`);
  if (!res.ok) throw new Error('Failed to query diagnostics report');
  return res.json();
}
