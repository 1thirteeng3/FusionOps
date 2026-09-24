function resolveWsUrl(): string {
  // Build-time absolute URLs break remote deployments (Vite bakes env at
  // build). Derive same-origin /ws at runtime (F1); explicit env wins.
  const fromEnv = import.meta.env.VITE_WS_URL as string | undefined;
  if (fromEnv) return fromEnv;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws`;
}

export const config = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string) || '/api/v1',
  wsUrl: resolveWsUrl(),
};
