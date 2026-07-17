const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

export function tenantSlugFromHost(): string {
  if (typeof window === "undefined") return "";
  const sub = window.location.hostname.split(".")[0];
  return sub && sub !== "localhost" && sub !== "www" && sub !== "127" ? sub : "";
}

export interface LoginResult {
  access_token: string;
  refresh_token: string;
  must_change_password: boolean;
}

export async function apiLogin(
  slug: string,
  username: string,
  password: string,
): Promise<LoginResult> {
  const res = await fetch(`${API_URL}/api/v1/authz/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Tenant-Slug": slug },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("invalid_credentials");
  return res.json();
}

export interface Me {
  user_id: string;
  tenant_id: string;
  role: string;
}

export async function apiMe(accessToken: string): Promise<Me> {
  const res = await fetch(`${API_URL}/api/v1/authz/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error("unauthorized");
  return res.json();
}
