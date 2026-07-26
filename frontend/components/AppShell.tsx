"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { apiMe, unreadCount } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/labels";

// Nhóm vai trò dùng lại cho menu (API vẫn là nơi chặn thật — đây chỉ để đỡ rối màn hình).
const STAFF = ["owner", "manager", "academic_head", "teacher", "assistant"];
const ADMIN_ORG = ["owner", "manager", "it_admin"];
const AUTHOR = [
	"owner",
	"manager",
	"academic_head",
	"teacher",
	"content_editor",
];

type NavItem = { href: string; label: string; roles?: string[]; group: string };

const NAV: NavItem[] = [
	{ href: "/dashboard", label: "Tổng quan", group: "Chung" },
	{
		href: "/org/branches",
		label: "Chi nhánh",
		roles: ADMIN_ORG,
		group: "Tổ chức",
	},
	{
		href: "/org/classes",
		label: "Lớp học",
		roles: ADMIN_ORG,
		group: "Tổ chức",
	},
	{
		href: "/org/users",
		label: "Tài khoản",
		roles: ADMIN_ORG,
		group: "Tổ chức",
	},
	{
		href: "/org/import",
		label: "Import học sinh",
		roles: ADMIN_ORG,
		group: "Tổ chức",
	},
	{
		href: "/content",
		label: "Ngân hàng câu hỏi",
		roles: AUTHOR,
		group: "Dạy học",
	},
	{
		href: "/practices",
		label: "Bài luyện tập",
		roles: AUTHOR,
		group: "Dạy học",
	},
	{ href: "/exams", label: "Đề thi", roles: AUTHOR, group: "Dạy học" },
	{ href: "/khoa-hoc", label: "Khóa học", roles: AUTHOR, group: "Dạy học" },
	{ href: "/cham-bai", label: "Chấm bài", roles: STAFF, group: "Dạy học" },
	{
		href: "/lich-hoc",
		label: "Lịch học & điểm danh",
		roles: STAFF,
		group: "Dạy học",
	},
	{ href: "/bao-cao", label: "Báo cáo lớp", roles: STAFF, group: "Theo dõi" },
	{
		href: "/bang-xep-hang",
		label: "Bảng xếp hạng",
		roles: STAFF,
		group: "Theo dõi",
	},
	{ href: "/hoc", label: "Việc cần làm", roles: ["student"], group: "Học tập" },
	{
		href: "/hoc/khoa-hoc",
		label: "Khóa học của tôi",
		roles: ["student"],
		group: "Học tập",
	},
	{
		href: "/hoc/bao-cao",
		label: "Báo cáo của tôi",
		roles: ["student"],
		group: "Học tập",
	},
	{
		href: "/phu-huynh",
		label: "Cổng phụ huynh",
		roles: ["parent"],
		group: "Học tập",
	},
	{ href: "/ho-tro", label: "Hỗ trợ", group: "Hệ thống" },
	{
		href: "/quan-tri/usage",
		label: "Mức dùng",
		roles: ADMIN_ORG,
		group: "Hệ thống",
	},
	{
		href: "/quan-tri/log",
		label: "Quản trị log",
		roles: ["owner", "it_admin", "admin"],
		group: "Hệ thống",
	},
];

export function AppShell({
	title,
	children,
}: {
	title: string;
	children: React.ReactNode;
}) {
	const [unread, setUnread] = useState(0);
	const [role, setRole] = useState<string | null>(null);
	const [navOpen, setNavOpen] = useState(false);
	const pathname = usePathname();

	useEffect(() => {
		let alive = true;
		apiMe()
			.then((m) => {
				if (alive) setRole(m.role);
			})
			.catch(() => {});
		const poll = () =>
			unreadCount()
				.then((r) => {
					if (alive) setUnread(r.count);
				})
				.catch(() => {});
		poll();
		const id = setInterval(poll, 20000);
		return () => {
			alive = false;
			clearInterval(id);
		};
	}, []);

	// Chưa biết vai trò thì hiện mục chung, tránh nháy menu đầy rồi co lại.
	const visible = NAV.filter(
		(n) => !n.roles || (role ? n.roles.includes(role) : false),
	);
	const groups: Record<string, NavItem[]> = {};
	for (const n of visible) {
		if (!groups[n.group]) groups[n.group] = [];
		groups[n.group].push(n);
	}

	function logout() {
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
		window.location.href = "/login";
	}

	return (
		<div className="min-h-screen flex flex-col bg-neutral-100 dark:bg-neutral-950">
			<header className="h-14 flex items-center gap-4 px-4 sm:px-6 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
				<button
					type="button"
					className="md:hidden text-xl"
					aria-label="Mở menu"
					data-testid="nav-toggle"
					onClick={() => setNavOpen((v) => !v)}
				>
					☰
				</button>
				<span className="font-bold">Edmicro</span>
				{role && (
					<span
						className="hidden sm:inline text-xs rounded-full px-2 py-0.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-500"
						data-testid="header-role"
					>
						{ROLE_LABEL[role] ?? role}
					</span>
				)}
				<div className="flex-1" />
				<Link
					href="/thong-bao"
					className="relative text-lg"
					data-testid="notif-bell"
					aria-label="Thông báo"
				>
					🔔
					{unread > 0 && (
						<span
							className="absolute -top-1 -right-2 min-w-4 h-4 px-1 rounded-full bg-danger text-white text-[10px] font-semibold flex items-center justify-center"
							data-testid="notif-badge"
						>
							{unread}
						</span>
					)}
				</Link>
				<button
					type="button"
					onClick={logout}
					className="text-sm text-neutral-500"
					data-testid="logout"
				>
					Đăng xuất
				</button>
			</header>
			<div className="flex flex-1 flex-col md:flex-row">
				{/* Mobile: menu là panel gập/mở qua nút ☰; desktop: sidebar cố định */}
				<aside
					className={`${navOpen ? "block" : "hidden"} md:block w-full md:w-56 p-3 border-b md:border-b-0 md:border-r border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 md:bg-transparent`}
				>
					{Object.entries(groups).map(([group, items]) => (
						<div key={group} className="mb-3">
							<p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
								{group}
							</p>
							{items.map((n) => {
								const active = pathname === n.href;
								return (
									<Link
										key={n.href}
										href={n.href}
										onClick={() => setNavOpen(false)}
										aria-current={active ? "page" : undefined}
										className={`block px-3 py-2 rounded-lg text-sm ${
											active
												? "bg-primary-100 dark:bg-primary-950 text-primary font-medium"
												: "text-neutral-600 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-800"
										}`}
									>
										{n.label}
									</Link>
								);
							})}
						</div>
					))}
				</aside>
				<main className="flex-1 p-4 sm:p-6 max-w-5xl">
					<h1 className="text-xl font-semibold mb-4">{title}</h1>
					{children}
				</main>
			</div>
		</div>
	);
}
