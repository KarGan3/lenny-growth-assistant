// Centralised runtime config. Everything the app needs to know about *where*
// to talk lives here, driven by Vite env vars (see .env.example).

const raw = import.meta.env

export const config = {
  // API prefix. Vite (dev) / nginx (prod) proxy this to FastAPI.
  apiBaseUrl: raw.VITE_API_BASE_URL || '/api',

  // When true, use the in-memory mock adapter instead of hitting the backend.
  // Real backend by default; mock mode must be explicitly enabled.
  useMock: String(raw.VITE_USE_MOCK ?? 'false').toLowerCase() === 'true',
}
