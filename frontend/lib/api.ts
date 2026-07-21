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

// ---- CONTENT ----
export interface QuestionRow {
	id: string;
	type: string;
	language: string;
	skill: string | null;
	level: string | null;
	exam_tag: string | null;
	topic: string | null;
	status: string;
	prompt: string | null;
}
export const listQuestions = (filters: {
	skill?: string;
	language?: string;
	status?: string;
}) => {
	const p = new URLSearchParams();
	for (const [k, v] of Object.entries(filters)) if (v) p.set(k, v);
	return req<QuestionRow[]>("GET", `/api/v1/content/questions?${p.toString()}`);
};
export const createQuestion = (payload: {
	type: string;
	language: string;
	skill?: string;
	content: Record<string, unknown>;
	answer_key: Record<string, unknown>;
}) => req<{ id: string }>("POST", "/api/v1/content/questions", payload);
export const publishQuestion = (id: string) =>
	req<{ ok: boolean }>("POST", `/api/v1/content/questions/${id}/publish`);

// ---- PRACTICE + ASSIGN ----
export interface Practice {
	id: string;
	name: string;
	skill: string | null;
	language: string;
	status: string;
	n_q: number;
}
export const listPractices = () => req<Practice[]>("GET", "/api/v1/practices");
export const createPractice = (
	name: string,
	skill: string,
	question_ids: string[],
) =>
	req<{ id: string }>("POST", "/api/v1/practices", {
		name,
		skill,
		language: "en",
		question_ids,
	});
export const createAssignment = (
	content_id: string,
	class_id: string,
	due_at: string,
) =>
	req<{ id: string; assignee_count: number }>("POST", "/api/v1/assignments", {
		content_id,
		class_id,
		due_at,
	});

export interface TodoItem {
	assignee_id: string;
	assignment_id: string;
	practice_name: string;
	due_at: string | null;
	status: string;
	attempt_id: string | null;
}
export const myAssignments = () =>
	req<TodoItem[]>("GET", "/api/v1/me/assignments");

export interface AttemptQuestion {
	question_version_id: string;
	type: string;
	content: { prompt: string; options?: string[] };
	sort_order: number;
}
export interface AttemptStart {
	attempt_id: string;
	practice: { id: string; name: string; questions: AttemptQuestion[] };
}
export const startAttempt = (assigneeId: string) =>
	req<AttemptStart>("POST", `/api/v1/assignments/${assigneeId}/start`);
export const saveAnswer = (
	attemptId: string,
	question_version_id: string,
	payload: object,
) =>
	req<{ saved: boolean }>("PUT", `/api/v1/attempts/${attemptId}/answers`, {
		question_version_id,
		payload,
	});
export const submitAttempt = (attemptId: string) =>
	req<{
		submitted: boolean;
		correct_count: number;
		total_count: number;
		score: number;
	}>("POST", `/api/v1/attempts/${attemptId}/submit`);

export interface ReviewItem {
	sort_order: number;
	type: string;
	content: { prompt: string; options?: string[] };
	answer_key: { correct_index?: number; blanks?: string[][] } | null;
	explanation: string | null;
	your_answer: { selected?: number; blanks?: string[]; text?: string } | null;
	is_correct: boolean | null;
	grade_status: string | null;
	ai_feedback: string | null;
	final_score: number | null;
}
export interface AttemptResult {
	correct_count: number;
	total_count: number;
	score: number;
	status: string;
	review: ReviewItem[];
}
export const getResult = (attemptId: string) =>
	req<AttemptResult>("GET", `/api/v1/attempts/${attemptId}/result`);

// ── Chấm AI writing + review GV (M6) ──────────────────────────
export interface GradingQueueItem {
	attempt_id: string;
	student_id: string;
	student_name: string;
	class_id: string;
	class_name: string;
	practice_name: string;
	pending_count: number;
	priority: number;
	has_manual: boolean;
}
export const gradingQueue = () =>
	req<GradingQueueItem[]>("GET", "/api/v1/grading/queue");

export interface ReviewOpenItem {
	answer_id: string;
	sort_order: number;
	prompt: string | null;
	rubric: string | null;
	your_answer: string | null;
	ai_score: number | null;
	ai_feedback: string | null;
	ai_confidence: number | null;
	final_score: number | null;
	grade_status: string;
}
export interface ReviewDetail {
	attempt_id: string;
	items: ReviewOpenItem[];
}
export const reviewDetail = (attemptId: string) =>
	req<ReviewDetail>("GET", `/api/v1/grading/attempts/${attemptId}`);
export const finalizeAnswer = (
	answerId: string,
	final_score: number,
	feedback?: string,
) =>
	req<{ score: number; status: string }>(
		"POST",
		`/api/v1/grading/answers/${answerId}/finalize`,
		{ final_score, feedback },
	);

// ── Báo cáo (M5) ──────────────────────────────────────────────
export interface StudentReportItem {
	practice_name: string;
	score: number | null;
	correct_count: number;
	total_count: number;
	submitted_at: string | null;
	attempt_id: string;
}
export interface StudentReport {
	summary: { assigned: number; submitted: number; avg_score: number | null };
	items: StudentReportItem[];
}
export const myReport = () => req<StudentReport>("GET", "/api/v1/me/report");
export const studentReport = (studentId: string) =>
	req<StudentReport>("GET", `/api/v1/reports/students/${studentId}`);

export interface ClassReportStudent {
	student_id: string;
	full_name: string;
	assigned: number;
	submitted: number;
	avg_score: number | null;
}
export interface ClassReport {
	summary: {
		student_count: number;
		assigned_total: number;
		submitted_total: number;
		class_avg: number | null;
		completion_rate: number | null;
	};
	students: ClassReportStudent[];
}
export const classReport = (classId: string) =>
	req<ClassReport>("GET", `/api/v1/reports/classes/${classId}`);
