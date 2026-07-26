/** Nhãn tiếng Việt dùng chung — tránh lộ mã trạng thái tiếng Anh thô ra UI. */

export const TODO_STATUS: Record<string, { label: string; tone: string }> = {
	not_opened: {
		label: "Chưa mở",
		tone: "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300",
	},
	in_progress: {
		label: "Đang làm",
		tone: "bg-primary-100 dark:bg-primary-950 text-primary",
	},
	submitted: {
		label: "Đã nộp",
		tone: "bg-success-100 dark:bg-success-950 text-success-700 dark:text-success-400",
	},
	overdue: {
		label: "Quá hạn",
		tone: "bg-danger-100 dark:bg-danger-950 text-danger",
	},
};

export const Q_TYPE: Record<string, string> = {
	mcq_single: "Trắc nghiệm",
	fill_blank: "Điền từ",
	writing: "Viết",
};

export const Q_STATUS: Record<string, string> = {
	draft: "Nháp",
	published: "Đã xuất bản",
	archived: "Đã lưu trữ",
};

export const ROLE_LABEL: Record<string, string> = {
	owner: "Chủ trung tâm",
	manager: "Quản lý học vụ",
	academic_head: "Tổ trưởng",
	it_admin: "IT trung tâm",
	teacher: "Giáo viên",
	assistant: "Trợ giảng",
	content_editor: "NV nội dung",
	support_agent: "NV hỗ trợ",
	student: "Học sinh",
	parent: "Phụ huynh",
	admin: "Admin hệ thống",
};

export const TICKET_STATUS: Record<string, string> = {
	open: "Đang mở",
	closed: "Đã đóng",
};

export function fmtDue(dueAt: string | null): string {
	if (!dueAt) return "";
	const d = new Date(dueAt);
	return `${d.toLocaleDateString("vi-VN")} ${d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}`;
}
