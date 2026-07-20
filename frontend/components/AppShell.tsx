"use client";

import Link from "next/link";

const NAV = [
	{ href: "/org/branches", label: "Chi nhánh" },
	{ href: "/org/classes", label: "Lớp học" },
	{ href: "/org/users", label: "Tài khoản" },
	{ href: "/org/import", label: "Import học sinh" },
	{ href: "/content", label: "Ngân hàng câu hỏi" },
	{ href: "/practices", label: "Bài luyện tập" },
	{ href: "/bao-cao", label: "Báo cáo lớp" },
	{ href: "/hoc", label: "Việc cần làm (HS)" },
	{ href: "/hoc/bao-cao", label: "Báo cáo của tôi (HS)" },
];

export function AppShell({
	title,
	children,
}: {
	title: string;
	children: React.ReactNode;
}) {
	function logout() {
		localStorage.removeItem("access_token");
		localStorage.removeItem("refresh_token");
		window.location.href = "/login";
	}

	return (
		<div className="min-h-screen flex flex-col bg-neutral-100 dark:bg-neutral-950">
			<header className="h-14 flex items-center gap-4 px-6 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
				<span className="font-bold">Edmicro</span>
				<div className="flex-1" />
				<button
					type="button"
					onClick={logout}
					className="text-sm text-neutral-500"
					data-testid="logout"
				>
					Đăng xuất
				</button>
			</header>
			<div className="flex flex-1">
				<aside className="w-56 p-3 border-r border-neutral-200 dark:border-neutral-800">
					{NAV.map((n) => (
						<Link
							key={n.href}
							href={n.href}
							className="block px-3 py-2 rounded-lg text-sm text-neutral-600 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-800"
						>
							{n.label}
						</Link>
					))}
				</aside>
				<main className="flex-1 p-6 max-w-5xl">
					<h1 className="text-xl font-semibold mb-4">{title}</h1>
					{children}
				</main>
			</div>
		</div>
	);
}
