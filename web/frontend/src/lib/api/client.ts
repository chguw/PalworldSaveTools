// Typed API client. Uses relative /api paths so it works both through the Vite
// dev proxy (:5173 -> :8000) and the production single-origin FastAPI serve.
import type {
  BaseListResponse, ContainerListResponse, ConvertIdsRequest,
  ConvertIdsResponse, ConvertRequest, GuildListResponse,
  HealthResponse, LanguagesResponse, LoadResponse, PalListResponse,
  PlayerListResponse, SaveStateResponse, SlotInjectorRequest,
  ToolResponse, ToolsListResponse,
} from '$types/index';

const API_BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      const j = JSON.parse(text);
      detail = j.detail ?? text;
    } catch {
      /* keep raw text */
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return text ? (JSON.parse(text) as T) : (undefined as unknown as T);
}

function jsonBody(body: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  languages: () => request<LanguagesResponse>('/data/languages'),
  i18n: (lang: string) =>
    request<{ lang: string; keys: Record<string, string> }>(`/data/i18n/${lang}`),

  saveState: () => request<SaveStateResponse>('/save/state'),
  loadFromPath: (path: string) =>
    request<LoadResponse>('/save/load', jsonBody({ path })),
  unload: () => request<SaveStateResponse>('/save', { method: 'DELETE' }),

  exportSave: async (): Promise<{ blob: Blob; filename: string; size: number }> => {
    const res = await fetch(`${API_BASE}/save/export`, { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Export failed: ${text}`);
    }
    const dispo = res.headers.get('Content-Disposition') ?? '';
    const match = dispo.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : 'Level.sav';
    const blob = await res.blob();
    return { blob, filename, size: Number(res.headers.get('X-Export-Size') ?? blob.size) };
  },

  players: () => request<PlayerListResponse>('/players'),
  guilds: () => request<GuildListResponse>('/guilds'),
  bases: () => request<BaseListResponse>('/bases'),
  containers: (limit = 200) =>
    request<ContainerListResponse>(`/containers?limit=${limit}`),
  pals: (limit = 300) => request<PalListResponse>(`/pals?limit=${limit}`),

  // ---- tools ----
  tools: () => request<ToolsListResponse>('/tools'),
  toolConvert: (params: ConvertRequest) =>
    request<ToolResponse>('/tools/convert', jsonBody(params)),
  toolConvertIds: (params: ConvertIdsRequest) =>
    request<ConvertIdsResponse>('/tools/convert-ids', jsonBody(params)),
  toolRestoreMap: (params: { path: string }) =>
    request<ToolResponse>('/tools/restore-map', jsonBody(params)),
  toolSlotInject: (params: SlotInjectorRequest) =>
    request<ToolResponse>('/tools/slot-injector', jsonBody(params)),
  toolFixHostSave: (params: Record<string, unknown>) =>
    request<ToolResponse>('/tools/fix-host-save', jsonBody(params)),
};
