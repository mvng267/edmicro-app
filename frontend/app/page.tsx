"use client";

import { useEffect } from "react";

// Trang gốc chỉ điều hướng: đã đăng nhập → dashboard, chưa → login.
// (Token nằm ở localStorage nên phải kiểm phía client, giống guard của /dashboard.)
export default function Home() {
	useEffect(() => {
		const token = localStorage.getItem("access_token");
		window.location.replace(token ? "/dashboard" : "/login");
	}, []);

	return (
		<div className="min-h-screen flex items-center justify-center bg-neutral-100 dark:bg-neutral-950">
			<p className="text-sm text-neutral-500">Đang chuyển hướng…</p>
		</div>
	);
}
