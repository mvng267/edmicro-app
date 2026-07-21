"use client";

import { Button, Card, CardContent } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
	markAllNotifRead,
	markNotifRead,
	myNotifications,
	type Notification,
} from "@/lib/api";

export default function NotificationsPage() {
	const [items, setItems] = useState<Notification[]>([]);
	const [err, setErr] = useState("");

	async function load() {
		setItems(await myNotifications());
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: chỉ load 1 lần khi mở trang
	useEffect(() => {
		load().catch((e) => setErr(String(e)));
	}, []);

	async function readOne(id: string) {
		await markNotifRead(id).catch(() => {});
		await load();
	}
	async function readAll() {
		await markAllNotifRead().catch(() => {});
		await load();
	}

	return (
		<AppShell title="Thông báo">
			<div className="flex justify-end mb-3">
				<Button variant="ghost" onPress={readAll} data-testid="read-all">
					Đánh dấu tất cả đã đọc
				</Button>
			</div>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			{items.length === 0 ? (
				<p className="text-sm text-neutral-500">Chưa có thông báo.</p>
			) : (
				<ul data-testid="notif-list" className="flex flex-col gap-2">
					{items.map((n) => (
						<li key={n.id}>
							<Card
								className={n.read ? "opacity-60" : ""}
								data-testid={`notif-${n.id}`}
							>
								<CardContent className="flex flex-col gap-1">
									<div className="flex items-center gap-2">
										{!n.read && (
											<span className="w-2 h-2 rounded-full bg-primary" />
										)}
										<span className="font-medium">{n.title}</span>
										<span className="ml-auto text-xs text-neutral-400">
											{n.created_at.slice(0, 16).replace("T", " ")}
										</span>
										{!n.read && (
											<Button
												variant="ghost"
												onPress={() => readOne(n.id)}
												data-testid={`read-${n.id}`}
											>
												Đã đọc
											</Button>
										)}
									</div>
									<p className="text-sm text-neutral-500">{n.body}</p>
								</CardContent>
							</Card>
						</li>
					))}
				</ul>
			)}
		</AppShell>
	);
}
