export const LOCAL_ONLY = import.meta.env.VITE_LOCAL_ONLY === 'true';
export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  (import.meta.env.VITE_CONVEX_SITE_URL as string | undefined) ??
  '';
