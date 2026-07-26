"use client";

import { Card, CardContent, Chip, ChipLabel } from "@heroui/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Pager, PageState } from "@/components/PageState";
import { type ActivityLog, listLogs } from "@/lib/api";

const PAGE_SIZE = 30;

const MODULES = [
	"",
	"ORG",
	"CONTENT",
	"ASSIGN",
	"GRADE",
	"EXAM",
	"COURSE",
	"NOTIF",
];

export default function LogAdminPage() {
	const [logs, setLogs] = useState<ActivityLog[]>([]);
	const [module, setModule] = useState("");
	const [err, setErr] = useState("");
	const [page, setPage] = useState(0);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		setLoading(true);
		listLogs({ module: module || undefined }, PAGE_SIZE, page * PAGE_SIZE)
			.then(setLogs)
			.catch((e) => setErr(String(e)))
			.finally(() => setLoading(false));
	}, [module, page]);

	return (
		<AppShell title="Quản trị nhật ký">
			<div className="flex gap-2 mb-4 items-center">
				<span className="text-sm text-neutral-500">Module:</span>
				<select
					value={module}
					onChange={(e) => {
						setModule(e.target.value);
						setPage(0);
					}}
					data-testid="module-filter"
					className="border rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
				>
					{MODULES.map((m) => (
						<option key={m} value={m}>
							{m || "Tất cả"}
						</option>
					))}
				</select>
			</div>
			{err && <p className="text-danger text-sm mb-2">{err}</p>}
			<PageState
				loading={loading}
				empty={logs.length === 0}
				emptyText="Chưa có nhật ký."
			/>
			<Card>
				<CardContent className="p-0 overflow-x-auto">
					<table className="w-full text-sm" data-testid="log-table">
						<thead>
							<tr className="text-left text-neutral-500 border-b border-neutral-200 dark:border-neutral-800">
								<th className="p-3">Thời gian</th>
								<th className="p-3">Vai trò</th>
								<th className="p-3">Hành động</th>
								<th className="p-3">Module</th>
								<th className="p-3">Đối tượng</th>
							</tr>
						</thead>
						<tbody>
							{logs.map((l) => (
								<tr
									key={l.id}
									className="border-b border-neutral-100 dark:border-neutral-800"
								>
									<td className="p-3 text-neutral-500">
										{l.at.slice(0, 19).replace("T", " ")}
									</td>
									<td className="p-3">{l.actor_role}</td>
									<td className="p-3">{l.action}</td>
									<td className="p-3">
										<Chip>
											<ChipLabel>{l.module}</ChipLabel>
										</Chip>
									</td>
									<td className="p-3 text-neutral-500">
										{l.entity_label || l.entity_type || "—"}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</CardContent>
			</Card>
			<Pager
				page={page}
				setPage={setPage}
				hasMore={logs.length === PAGE_SIZE}
			/>
		</AppShell>
	);
}
