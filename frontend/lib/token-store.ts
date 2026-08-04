const STORAGE_KEY = "careerpilot_access_token";

let currentToken: string | null = null;

export function getAccessToken(): string | null {
  if (currentToken) return currentToken;
  if (typeof window !== "undefined") {
    currentToken = window.localStorage.getItem(STORAGE_KEY);
  }
  return currentToken;
}

export function setAccessToken(token: string | null): void {
  currentToken = token;
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}
