const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

export function tenantSlugFromHost(): string {
	if (typeof window === "undefined") return "";
	const sub = window.location.hostname.split(".")[0];
	return sub && sub !== "localhost" && sub !== "www" && sub !== "127"
		? sub
		: "";
}

function authHeaders(): Record<string, string> {
	const token =
		typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
	return {
		"Content-Type": "application/json",
		"X-Tenant-Slug": tenantSlugFromHost(),
		...(token ? { Authorization: `Bearer ${token}` } : {}),
	};
}

async function req<T>(
	method: string,
	path: string,
	body?: unknown,
): Promise<T> {
	const res = await fetch(`${API_URL}${path}`, {
		method,
		headers: authHeaders(),
		body: body === undefined ? undefined : JSON.stringify(body),
	});
	if (res.status === 401) {
		if (typeof window !== "undefined") window.location.href = "/login";
		throw new Error("unauthorized");
	}
	if (!res.ok) {
		const detail = await res.json().catch(() => ({}));
		throw new Error(detail.detail ?? `error_${res.status}`);
	}
	return res.status === 204 ? (undefined as T) : res.json();
}

// ---- Auth ----
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
export const apiMe = () => req<Me>("GET", "/api/v1/authz/me");

// ---- ORG ----
export interface Branch {
	id: string;
	name: string;
	address: string | null;
	status: string;
}
export const listBranches = () => req<Branch[]>("GET", "/api/v1/org/branches");
export const createBranch = (name: string, address?: string) =>
	req<Branch>("POST", "/api/v1/org/branches", { name, address });

export interface Klass {
	id: string;
	branch_id: string;
	name: string;
	language: string;
	level: string | null;
	status: string;
}
export const listClasses = () => req<Klass[]>("GET", "/api/v1/org/classes");
export const createClass = (
	branch_id: string,
	name: string,
	language: string,
	level?: string,
) =>
	req<Klass>("POST", "/api/v1/org/classes", {
		branch_id,
		name,
		language,
		level,
	});

export interface UserRow {
	id: string;
	username: string;
	full_name: string;
	role: string;
	status: string;
}
export interface Credential {
	id: string;
	username: string;
	password: string;
	full_name: string;
}
export const listUsers = (q?: string, role?: string) => {
	const p = new URLSearchParams();
	if (q) p.set("q", q);
	if (role) p.set("role", role);
	return req<UserRow[]>("GET", `/api/v1/org/users?${p.toString()}`);
};
export const createUser = (payload: {
	full_name: string;
	role: string;
	dob?: string;
	class_id?: string;
}) => req<Credential>("POST", "/api/v1/org/users", payload);

export interface ImportRow {
	row_no: number;
	data: Record<string, string | null>;
	error: string | null;
}
export interface ImportPreview {
	job_id: string;
	summary: { total: number; valid: number; errors: number };
	rows: ImportRow[];
}
export async function importValidate(file: File): Promise<ImportPreview> {
	const fd = new FormData();
	fd.append("file", file);
	const token = localStorage.getItem("access_token");
	const res = await fetch(`${API_URL}/api/v1/org/users/import`, {
		method: "POST",
		headers: {
			"X-Tenant-Slug": tenantSlugFromHost(),
			...(token ? { Authorization: `Bearer ${token}` } : {}),
		},
		body: fd,
	});
	if (!res.ok) throw new Error("import_failed");
	return res.json();
}
export const importCommit = (jobId: string) =>
	req<{ created: number; credentials: Credential[] }>(
		"POST",
		`/api/v1/org/users/import/${jobId}/commit`,
	);
