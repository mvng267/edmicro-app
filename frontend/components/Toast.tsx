"use client";

import { CheckCircle2, XCircle } from "lucide-react";

import { useEffect, useState } from "react";

type ToastMsg = { id: number; text: string; type: "success" | "error" };
type Listener = (t: ToastMsg) => void;

let _listener: Listener | null = null;
let _seq = 0;

/** Gọi từ bất kỳ đâu: toast("Đã lưu"), toast("Lỗi...", "error"). */
export function toast(text: string, type: "success" | "error" = "success") {
	_listener?.({ id: ++_seq, text, type });
}

/** Host hiển thị toast — mount 1 lần trong AppShell. */
export function ToastHost() {
	const [items, setItems] = useState<ToastMsg[]>([]);

	useEffect(() => {
		_listener = (t) => {
			setItems((prev) => [...prev, t]);
			setTimeout(
				() => setItems((prev) => prev.filter((x) => x.id !== t.id)),
				4000,
			);
		};
		return () => {
			_listener = null;
		};
	}, []);

	return (
		<div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
			{items.map((t) => (
				<div
					key={t.id}
					data-testid="toast"
					className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm shadow-lg border animate-[fadein_.15s_ease-out] ${
						t.type === "success"
							? "bg-success-50 dark:bg-success-950 border-success-200 dark:border-success-900 text-success-700 dark:text-success-300"
							: "bg-danger-50 dark:bg-danger-950 border-danger-200 dark:border-danger-900 text-danger"
					}`}
				>
					{t.type === "success" ? (
						<CheckCircle2 size={16} className="shrink-0" />
					) : (
						<XCircle size={16} className="shrink-0" />
					)}
					{t.text}
				</div>
			))}
		</div>
	);
}
